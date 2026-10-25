"""data/kuratabi.json と data/kura.json から「蔵旅 by 一献」のページを作るスクリプト。
蔵の紹介も旅程もこのサイトの中で完結させ、一献のページへは飛ばしません。
使い方: python3 tools/build.py

旅のしおりを足すときは data/kuratabi.json の trips に1件追加して、このスクリプトを実行してください。
蔵の名前・見学の可否・創業などは data/kura.json から読み込みます(蔵の一覧のページ kura.html もここから作ります)。
GitHub に上げると、公開の仕組みでも自動で実行されます。
assets/ の CSS・JS を直したら、下の VERSION を1つ上げてください(閲覧者のブラウザに古い版が残らなくなります)。
"""
import html
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

VERSION = "7"
LEAFLET = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/"
RAKUTEN_ON = False  # 楽天アフィリエイト(宿の予約リンク・宿のカード・広告の表示)を使うときは True にする。いまは止めている
RAKUTEN_AFF = "58c36830.1e80c147.58c36831.fb6bd4b1"  # 楽天アフィリエイトID
AD_NOTICE = "    <span>当サイトは楽天アフィリエイトなどの広告を利用しています。予約のリンクから得た収益は、サイトの運営に使います。</span>\n" if RAKUTEN_ON else ""

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data/kuratabi.json").read_text(encoding="utf-8"))
kura = {k["id"]: k for k in json.loads((ROOT / "data/kura.json").read_text(encoding="utf-8"))}
# 一献のなかま4サービスの住所(独自ドメインに移すときは data/sites.json を直す)
SITES = json.loads((ROOT / "data/sites.json").read_text(encoding="utf-8"))
URL = {k: v["url"] for k, v in SITES["sites"].items()}
SITE = URL["kuratabi"]


def family(keys):
    """フッターに置く「一献のなかま」。keys は data/sites.json の sites のキー。"""
    links = "".join(f'<a href="{e(URL[k])}" data-site="{k}"><b>{e(SITES["sites"][k]["name"])}</b><small>{e(SITES["sites"][k]["desc"])}</small></a>' for k in keys)
    return f'<nav class="family" aria-label="一献のなかま"><span class="family-h">一献のなかま</span>{links}</nav>'
kura_geo = data.get("kuraGeo", {})
kura_order = list(kura)
e = html.escape

AREAS = ["仙台・県央", "県南", "塩竈", "大崎・加美・遠田", "栗原・登米", "石巻・気仙沼"]
TOUR = {"yes": ("見学できる", "tour-yes"), "partial": ("一部見学", "tour-ask"), "ask": ("要相談", "tour-ask"), "no": ("見学不可", "tour-no")}
LENGTH = {"half": "半日", "day": "1日"}
# 酒造りの暦(一般的な目安。蔵によって前後します)
CALENDAR = [
    ("仕込み", "蔵がいちばん忙しい季節。見学を休む蔵も", [11, 12, 1, 2, 3]),
    ("新酒・しぼりたて", "その冬に搾った酒が出回る", [12, 1, 2, 3]),
    ("蔵開き", "春先に蔵を開く催しが多い", [2, 3, 4, 5]),
    ("夏酒", "軽やかな夏向けの酒", [6, 7, 8]),
    ("ひやおろし", "夏を越して熟した秋の酒", [9, 10, 11]),
]

# 打ち間違いで旅のしおりが黙って消えたり壊れたりしないよう、先に確かめる
TRIP_KEYS = ["kura", "title", "lead", "access", "length", "lengthKey", "spots", "course"]
errors, seen = [], set()


def bad_geo(g):
    return not (isinstance(g, list) and len(g) == 2 and 37 < g[0] < 40 and 139 < g[1] < 143)


for i, t in enumerate(data["trips"], start=1):
    where = t.get("kura") or f"{i}番目の旅"
    errors += [f"{where}: 「{k}」がありません" for k in TRIP_KEYS if not t.get(k)]
    if t.get("kura") not in kura:
        errors.append(f"{where}: 蔵 ID「{t.get('kura')}」が data/kura.json にありません")
    if t.get("kura") in seen:
        errors.append(f"{where}: 同じ蔵の旅が2つあります")
    seen.add(t.get("kura"))
    if t.get("lengthKey") and t["lengthKey"] not in LENGTH:
        errors.append(f"{where}: lengthKey は half か day にしてください")
    for w in t.get("with", []):
        if w not in kura:
            errors.append(f"{where}: with の蔵 ID「{w}」が data/kura.json にありません")
    for j, s in enumerate(t.get("spots", []), start=1):
        errors += [f"{where}: 見どころ{j}に「{k}」がありません" for k in ["kind", "name", "note"] if not s.get(k)]
        if "geo" in s and bad_geo(s["geo"]):
            errors.append(f"{where}: 見どころ{j}の geo が宮城の範囲を外れています")
    for j, c in enumerate(t.get("course", []), start=1):
        errors += [f"{where}: 旅程{j}に「{k}」がありません" for k in ["time", "text"] if not c.get(k)]
    if t.get("kura") in kura_geo and bad_geo(kura_geo[t["kura"]]):
        errors.append(f"{where}: kuraGeo の座標が宮城の範囲を外れています")
for k in kura.values():
    if k["area"] not in AREAS:
        errors.append(f'{k["id"]}: 地域「{k["area"]}」が AREAS にありません')
    if k["tour"] not in TOUR:
        errors.append(f'{k["id"]}: 見学「{k["tour"]}」が TOUR にありません')
# 一献・カップ酒図鑑は data/sites.json の kuratabiTrips を見てしおりへリンクするので、食い違いを止める
trip_ids = {t["kura"] for t in data["trips"]}
if trip_ids != set(SITES["kuratabiTrips"]):
    errors.append(f'data/sites.json の kuratabiTrips がしおりと合いません(足りない: {sorted(trip_ids - set(SITES["kuratabiTrips"]))}、余分: {sorted(set(SITES["kuratabiTrips"]) - trip_ids)})。3つのリポジトリの data/sites.json を直してください')
errors += [f'data/sites.json の kuratabiTrips の {i} の名前「{n}」が data/kura.json の「{kura[i]["name"]}」と違います'
           for i, n in SITES["kuratabiTrips"].items() if i in kura and kura[i]["name"] != n]
if errors:
    sys.exit("データに誤りがあります:\n" + "\n".join(errors))

trips = sorted(data["trips"], key=lambda t: kura_order.index(t["kura"]))
all_tags = []
for t in trips:
    for g in t.get("tags", []):
        if g not in all_tags:
            all_tags.append(g)


SITEMAP = []  # 作ったページ(sitemap.xml に載せる)


def shell(title, desc, body, path, current="", extra_head="", tail=""):
    SITEMAP.append(path)
    cur = ' aria-current="page"'
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:site_name" content="蔵旅 by 一献">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;700&family=Zen+Kaku+Gothic+New:wght@400;700&display=swap">
{extra_head}<link rel="stylesheet" href="assets/style.css?v={VERSION}">
</head>
<body>
<header class="site-head">
  <div class="wrap">
    <a class="logo" href="index.html"><span class="mark" aria-hidden="true"></span><b>蔵旅</b><small>by 一献</small></a>
    <nav class="nav"><a href="index.html"{cur if current == "index" else ""}>旅のしおり</a><a href="kura.html"{cur if current == "kura" else ""}>宮城の蔵</a></nav>
  </div>
</header>

<main>
{body}
</main>

<footer class="site-foot">
  <div class="wrap">
    <span>見学の受け入れや店の営業は変わることがあります。出かける前に必ず各蔵・各施設へ確かめてください。情報は{e(data["checked"])}に確認しました。</span>
    <span>試飲をする日は、電車やバス、運転しない人と。お酒は20歳になってから。飲酒運転は法律で禁止されています。</span>
{AD_NOTICE}    <span>蔵旅は、日本酒案内「<a href="{e(URL["ikkon"])}">一献</a>」がつくる酒蔵の旅のしおりです。地図 © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors</span>
    {family(["ikkon", "cupzukan"])}
  </div>
</footer>
{tail}</body>
</html>
'''


# ---------- 楽天トラベル(宿の情報) ----------
# 公開の仕組み(GitHub Actions)の中だけで、楽天のアプリIDとアクセスキーを使って宿を取ってくる。
# キーがない・楽天が応答しないときは、宿のカードを出さずに公開を続ける。結果は rakuten-status.json に書く。
TRAVEL_API = "https://openapi.rakuten.co.jp/engine/api/Travel/KeywordHotelSearch/20260731"
APP_ID = os.environ.get("RAKUTEN_APP_ID", "").strip()
ACCESS_KEY = os.environ.get("RAKUTEN_ACCESS_KEY", "").strip()
rk_status = {"fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "ok": [], "empty": [], "errors": []}


def basic_infos(node):
    """応答の形(formatVersion)に関係なく、hotelBasicInfo と評価を探し出す"""
    found = []
    if isinstance(node, dict):
        if "hotelBasicInfo" in node:
            found.append(node["hotelBasicInfo"])
        for v in node.values():
            found += basic_infos(v)
    elif isinstance(node, list):
        for v in node:
            found += basic_infos(v)
    return found


def fetch_hotels(keyword, n=3):
    if not APP_ID or not ACCESS_KEY:
        return []
    q = {"applicationId": APP_ID, "accessKey": ACCESS_KEY, "affiliateId": RAKUTEN_AFF, "keyword": keyword,
         "hits": 10, "datumType": 1, "formatVersion": 2}
    req = urllib.request.Request(TRAVEL_API + "?" + urllib.parse.urlencode(q), headers={
        "User-Agent": "kuratabi-site/1.0", "Referer": "https://rehab-info.github.io/", "Origin": "https://rehab-info.github.io", "accessKey": ACCESS_KEY})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
    except urllib.error.HTTPError as ex:
        rk_status["errors"].append(f"「{keyword}」: HTTP {ex.code} {ex.read().decode('utf-8', 'replace')[:200]}")
        return []
    except Exception as ex:
        rk_status["errors"].append(f"「{keyword}」: {ex}")
        return []
    finally:
        time.sleep(1.1)  # 楽天への負担を減らすため、1秒に1回まで
    out = []
    for h in basic_infos(data):
        url = h.get("hotelInformationUrl") or h.get("planListUrl")
        img = h.get("hotelImageUrl") or h.get("hotelThumbnailUrl")
        if not url or not h.get("hotelName"):
            continue
        out.append({"name": h["hotelName"], "url": url, "img": img or "", "min": h.get("hotelMinCharge"),
                    "review": h.get("reviewAverage"), "count": h.get("reviewCount"), "access": (h.get("access") or "")[:60]})
        if len(out) >= n:
            break
    (rk_status["ok"] if out else rk_status["empty"]).append(keyword)
    return out


def hotel_cards(hotels):
    if not hotels:
        return ""
    def one(h):
        img = f'<img src="{e(h["img"])}" alt="" loading="lazy" referrerpolicy="no-referrer">' if h["img"] else '<span class="kt-hotel-noimg"></span>'
        price = f'<b>1人 {int(h["min"]):,}円〜</b>' if h.get("min") else ""
        review = f'<span class="kt-hotel-review">評価 {float(h["review"]):.1f}({int(h["count"] or 0)}件)</span>' if h.get("review") else ""
        return f'<li><a href="{e(h["url"])}" target="_blank" rel="sponsored noopener">{img}<span class="kt-hotel-name">{e(h["name"])}</span>{price}{review}</a></li>'
    return '<ul class="kt-hotels">' + "".join(one(h) for h in hotels) + "</ul>"


def rakuten(url):
    """楽天のページへのリンクを、アフィリエイトID付きのリンクに包む"""
    return f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_AFF}/?pc={quote(url, safe='')}&m={quote(url, safe='')}"


def travel_link(q):
    return rakuten(f"https://kw.travel.rakuten.co.jp/keyword/Search.do?charset=utf-8&f_query={quote(q)}")


def map_link(q):
    return f"https://www.google.com/maps/search/?api=1&query={quote(q)}"


def cover(t, k, size="lg"):
    """表紙。写真があれば写真、なければ青海波の地に縦書きの表題。"""
    c = t.get("cover")
    if c and (ROOT / c["src"]).exists():
        credit = f'<figcaption>{e(c.get("credit", ""))}</figcaption>' if c.get("credit") else ""
        return f'<figure class="kt-cover kt-cover-{size} has-photo"><img src="{e(c["src"])}" alt="{e(c.get("alt", ""))}" loading="{"eager" if size == "lg" else "lazy"}">{credit}</figure>'
    return f'<div class="kt-cover kt-cover-{size}" aria-hidden="true"><span class="kt-cover-sugi"></span><span class="kt-cover-name">{"".join(f"<span>{e(ch)}</span>" for ch in k["brands"][0])}</span></div>'


def dist_km(a, b):
    r = math.radians
    dlat, dlon = r(b[0] - a[0]), r(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(r(a[0])) * math.cos(r(b[0])) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


# ---------- 蔵ごとのページ ----------
for t in trips:
    k = kura[t["kura"]]
    kg = kura_geo.get(k["id"])
    label, cls = TOUR[k["tour"]]
    brands = "".join(f"<span>{e(b)}</span>" for b in k["brands"])
    others = "".join(f'<dt>近くの蔵</dt><dd><a href="kura.html#{e(w)}">{e(kura[w]["name"])}</a>(見学:{TOUR[kura[w]["tour"]][0]})</dd>' for w in t.get("with", []))

    # 地図の点:蔵・駅・見どころ(遠いものは地図に入れず一覧だけ)
    markers, n = [], 0
    if kg:
        markers.append({"t": "kura", "label": "蔵", "name": k["name"], "lat": kg[0], "lng": kg[1]})
    st = t.get("station")
    if st and st.get("geo"):
        markers.append({"t": "station", "label": "駅", "name": st["name"], "lat": st["geo"][0], "lng": st["geo"][1]})
    spot_rows = []
    for s in t["spots"]:
        n += 1
        on_map = ""
        if s.get("atKura"):
            on_map = '<span class="kt-onmap">地図の「蔵」</span>'
        elif s.get("geo") and not s.get("far"):
            markers.append({"t": "spot", "label": str(n), "name": s["name"], "lat": s["geo"][0], "lng": s["geo"][1]})
            on_map = ""
        elif s.get("geo") and s.get("far") and kg:
            on_map = f'<span class="kt-onmap">蔵から約{round(dist_km(kg, s["geo"]))}km</span>'
        info = ""
        if s.get("info"):
            info = '<dl class="kt-info">' + "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in s["info"].items()) + "</dl>"
        links = [f'<a href="{e(map_link(s.get("map") or s["name"]))}" target="_blank" rel="noopener">地図</a>']
        if s.get("url"):
            links.append(f'<a href="{e(s["url"])}" target="_blank" rel="noopener">公式サイト</a>')
        spot_rows.append(f'''        <li class="kt-spot" id="spot{n}">
          <span class="kt-num" aria-hidden="true">{n}</span>
          <div class="kt-spot-body">
            <div class="kt-spot-head"><span class="kt-kind">{e(s["kind"])}</span><h3>{e(s["name"])}</h3>{on_map}</div>
            <p>{e(s["note"])}</p>
            {info}
            <div class="kt-spot-links">{"".join(links)}</div>
          </div>
        </li>''')

    course = "\n".join(f'          <li><time>{e(c["time"])}</time><span class="dot" aria-hidden="true"></span><span>{e(c["text"])}</span></li>' for c in t["course"])
    tips = '<ul class="kt-tips">' + "".join(f"<li>{e(x)}</li>" for x in t.get("tips", [])) + "</ul>" if t.get("tips") else ""
    def stay_html(s):
        maplink = f'<a href="{e(map_link(s.get("map") or s["name"]))}" target="_blank" rel="noopener">地図で見る</a>'
        if not RAKUTEN_ON:
            return f'<div class="kt-stay"><h3>{e(s["name"])}</h3><p>{e(s["note"])}</p><div class="kt-stay-links">{maplink}</div></div>'
        kw = s.get("travel") or s["name"]
        return (f'<div class="kt-stay"><h3>{e(s["name"])}</h3><p>{e(s["note"])}</p>{hotel_cards(fetch_hotels(kw))}'
                f'<div class="kt-stay-links"><a class="kt-stay-btn" href="{e(travel_link(kw))}" target="_blank" rel="sponsored noopener">楽天トラベルで宿を探す</a>{maplink}</div></div>')
    stays = "".join(stay_html(s) for s in t.get("stay", []))
    sake_note = f'<p class="kt-body">旅のおともに:{"、".join(e(s) for s in t["sakes"])}</p>' if t.get("sakes") else ""
    sake_links = [f'<a href="kura.html#{e(k["id"])}">宮城の蔵の一覧で見る</a>',
                  f'<a href="{e(URL["ikkon"])}kura.html#{e(k["id"])}">この蔵の酒を一献で見る</a>',
                  f'<a href="{e(URL["cupzukan"])}kura.html">宮城のカップ酒(カップ酒図鑑)</a>']
    if k.get("url"):
        sake_links.append(f'<a href="{e(k["url"])}" target="_blank" rel="noopener">蔵の公式サイト</a>')
    nexts = "".join(f'''<a class="kt-trip kt-trip-sm" href="{e(o["kura"])}.html">{cover(o, kura[o["kura"]], "sm")}<div class="kt-trip-body"><small>{e(kura[o["kura"]]["city"])} ・ {e(o["length"])}</small><h3>{e(o["title"])}</h3></div></a>'''
                    for o in trips if o is not t)
    tags = "".join(f"<span>{e(g)}</span>" for g in t.get("tags", []))

    map_html, tail, head = "", "", ""
    if len(markers) >= 2:
        head = f'<link rel="stylesheet" href="{LEAFLET}leaflet.css">\n'
        tail = f'''<script src="{LEAFLET}leaflet.js"></script>
<script>window.KT_MARKERS = {json.dumps(markers, ensure_ascii=False)};</script>
<script src="assets/map.js?v={VERSION}"></script>
'''
        map_html = f'''  <section class="section">
    <div class="wrap">
      <div class="section-head"><h2>地図</h2><p>番号は下の見どころと同じです</p></div>
      <div class="kt-map" id="kt-map" role="region" aria-label="{e(k["name"])}と見どころの地図"><p class="kt-map-fallback">地図を読み込んでいます</p></div>
      <div class="kt-legend"><span><i class="kt-pin kt-pin-kura">蔵</i>{e(k["name"])}</span>{f'<span><i class="kt-pin kt-pin-station">駅</i>{e(st["name"])}</span>' if st else ""}<span><i class="kt-pin kt-pin-spot">1</i>見どころ</span></div>
    </div>
  </section>
'''

    # 検索エンジン向けの構造化データ(旅程と観光地)
    items = []
    for i, s in enumerate(t["spots"], start=1):
        place = {"@type": "TouristAttraction", "name": s["name"], "description": s["note"]}
        g = kg if s.get("atKura") else s.get("geo")
        if g:
            place["geo"] = {"@type": "GeoCoordinates", "latitude": g[0], "longitude": g[1]}
        items.append({"@type": "ListItem", "position": i, "item": place})
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "TouristTrip", "name": t["title"], "description": t["lead"], "url": f'{SITE}{k["id"]}.html',
             "touristType": ["日本酒が好きな人", "酒蔵めぐり"],
             "itinerary": {"@type": "ItemList", "itemListElement": items}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "蔵旅", "item": f"{SITE}index.html"},
                {"@type": "ListItem", "position": 2, "name": t["title"], "item": f'{SITE}{k["id"]}.html'}]},
        ],
    }
    head += f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'

    body = f'''  <div class="wrap"><nav class="kt-crumb" aria-label="現在地"><a href="index.html">蔵旅</a><span>›</span><span>{e(k["area"])}</span><span>›</span><span>{e(k["name"])}</span></nav></div>
  <section class="kt-hero-trip">
    <div class="wrap">
      <div class="kt-hero-grid">
        {cover(t, k)}
        <div class="kt-hero-text">
          <div class="eyebrow">{e(k["city"])} ・ {e(k["name"])}をたずねて</div>
          <h1>{e(t["title"]).replace("、", "、<br>")}</h1>
          <div class="kt-tags">{tags}</div>
          <p class="kt-lead">{e(t["lead"])}</p>
        </div>
      </div>
      <dl class="kt-keyfacts">
        <div><dt>所要時間</dt><dd>{e(t["length"])}</dd></div>
        <div><dt>おすすめの季節</dt><dd>{e(t.get("season", "通年"))}</dd></div>
        <div><dt>蔵の見学</dt><dd><span class="tour {cls}">{label}</span></dd></div>
        <div><dt>最寄り駅</dt><dd>{e(st["name"]) if st else "—"}</dd></div>
      </dl>
    </div>
  </section>

  <section class="section">
    <div class="wrap kt-two">
      <div>
        <div class="section-head"><h2>蔵のこと</h2></div>
        <div class="brands">{brands}</div>
        <p class="kt-body">{e(k["intro"])}</p>
      </div>
      <div class="kt-facts">
        <dl class="info">
          <dt>見学</dt><dd><span class="tour {cls}">{label}</span> {e(k["tourNote"])}</dd>
          <dt>創業</dt><dd>{e(k["founded"])}</dd>
          <dt>行き方</dt><dd>{e(t["access"])}</dd>
          {others}
        </dl>
      </div>
    </div>
  </section>

{map_html}  <section class="section">
    <div class="wrap">
      <div class="section-head"><h2>まちの見どころ</h2><p>蔵とあわせて歩きたい場所</p></div>
      <ol class="kt-spots">
{chr(10).join(spot_rows)}
      </ol>
    </div>
  </section>

  <section class="section">
    <div class="wrap kt-two">
      <div>
        <div class="section-head"><h2>旅程の一例</h2><p>{e(t["length"])}</p></div>
        <ol class="kt-course">
{course}
        </ol>
      </div>
      <div>
        <div class="section-head"><h2>出かける前に</h2></div>
        {tips}
      </div>
    </div>
  </section>

  {f"""<section class="section">
    <div class="wrap">
      <div class="section-head"><h2>泊まるなら</h2><p>旅を一泊にのばすなら</p></div>
      {'<p class="kt-pr">このコーナーのリンクは広告(楽天アフィリエイト)です。</p>' if RAKUTEN_ON else ''}
      <div class="kt-stays">{stays}</div>
    </div>
  </section>""" if stays else ""}

  <section class="section">
    <div class="wrap stack">
      <div class="section-head"><h2>この蔵の酒</h2></div>
      <div class="brands">{brands}</div>
      {sake_note}
      <div class="links">{"".join(sake_links)}</div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><h2>ほかの蔵旅</h2></div>
      <div class="kt-next">{nexts}</div>
    </div>
  </section>'''
    desc = f'{k["name"]}({k["city"]})をたずねる旅。{t["lead"]}'[:120]
    page = f'{k["id"]}.html'
    (ROOT / page).write_text(shell(f'{t["title"]}|{k["name"]}をたずねる 蔵旅 by 一献', desc, body, page, extra_head=head, tail=tail), encoding="utf-8")

# ---------- 入口のページ ----------
cards = "\n".join(f'''        <a class="kt-trip" href="{e(t["kura"])}.html" data-tags="{e("|".join(t.get("tags", [])))}" data-length="{e(t["lengthKey"])}">
          {cover(t, kura[t["kura"]], "md")}
          <div class="kt-trip-body">
            <small>{e(kura[t["kura"]]["city"])} ・ {e(t["length"])}</small>
            <h3>{e(t["title"])}</h3>
            <span class="kt-kura">{e(kura[t["kura"]]["name"])}({"・".join(e(b) for b in kura[t["kura"]]["brands"])})</span>
            <p>{e(t["lead"])}</p>
            <div class="kt-tags">{"".join(f"<span>{e(g)}</span>" for g in t.get("tags", []))}</div>
          </div>
        </a>''' for t in trips)
side = "".join(f'<a href="{e(t["kura"])}.html">{e(t["title"])}</a>' for t in trips)
tag_chips = "".join(f'<button type="button" class="chip" data-tag="{e(g)}" aria-pressed="false">{e(g)}</button>' for g in all_tags)
len_chips = "".join(f'<button type="button" class="chip" data-len="{k}" aria-pressed="false">{v}</button>' for k, v in LENGTH.items())

months = "".join(f'<span class="kt-m">{m}</span>' for m in range(1, 13))
cal_rows = "".join(
    f'<div class="kt-cal-row"><div class="kt-cal-name"><b>{e(nm)}</b><small>{e(note)}</small></div><div class="kt-cal-bar">'
    + "".join(f'<span class="{"on" if m in ms else ""}"></span>' for m in range(1, 13)) + "</div></div>"
    for nm, note, ms in CALENDAR)

rest_html = []
for a in AREAS:
    ks = [k for k in kura.values() if k["area"] == a and k["id"] not in seen]
    if ks:
        items = "".join(f'<li><a href="kura.html#{e(k["id"])}">{e(k["name"])}</a><span class="kt-city">{e(k["city"])}・{TOUR[k["tour"]][0]}</span></li>' for k in ks)
        rest_html.append(f'      <div class="kt-area-name">{e(a)}</div>\n      <ul class="kt-rest">{items}</ul>')

body = f'''  <section class="hero-c kt-hero">
    <div class="wrap">
      <div class="hc-body">
        <div class="kt-sugi" role="img" aria-label="酒蔵の軒先に吊るされた杉玉"><i></i></div>
        <div class="hc-tate">
          <h1>蔵をたずね、<br>町をあるく。</h1>
          <p>杉玉の下から、旅がはじまる。</p>
        </div>
        <nav class="hc-side" aria-label="旅のしおり">
          <small>宮城の蔵旅 {len(trips)}編</small>
          {side}
        </nav>
      </div>
    </div>
    <div class="hc-foot"><span class="hc-seal" aria-hidden="true">旅</span></div>
  </section>

  <section class="section" id="trips">
    <div class="wrap">
      <div class="section-head"><h2>旅のしおり</h2><p>蔵と、そのまわりの見どころと、一日の流れ</p></div>
      <div class="kt-filter" role="group" aria-label="旅のしおりを絞り込む">
        <div class="chips">{tag_chips}</div>
        <div class="chips">{len_chips}</div>
      </div>
      <p class="kt-count" id="kt-count" aria-live="polite"></p>
      <div class="kt-trips" id="kt-trips">
{cards}
      </div>
      <p class="kt-empty" id="kt-empty" hidden>この組み合わせの旅は、まだありません。条件を一つ外してみてください。</p>
    </div>
  </section>

  <section class="section" id="calendar">
    <div class="wrap">
      <div class="section-head"><h2>酒蔵の一年</h2><p>いつ訪ねるかを決める目安に</p></div>
      <div class="kt-cal">
        <div class="kt-cal-row kt-cal-head"><div></div><div class="kt-cal-bar">{months}</div></div>
        {cal_rows}
      </div>
      <p class="notice">時期は一般的な目安で、蔵によって前後します。仕込みの季節は見学を休む蔵もあるので、行く前に確かめてください。</p>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><h2>これから訪ねる蔵</h2><p>旅のしおりは順に増やしていきます</p></div>
{chr(10).join(rest_html)}
      <p class="notice">蔵の名前を押すと、「宮城の蔵」で蔵の紹介と見学の受け入れを読めます。</p>
    </div>
  </section>'''
tail = f'<script src="assets/filter.js?v={VERSION}"></script>\n'
ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "蔵旅 by 一献", "url": SITE}
head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
(ROOT / "index.html").write_text(shell("蔵旅 by 一献|酒蔵をたずねる旅のしおり", f"宮城の酒蔵をたずね、蔵のまわりの見どころと一日の旅程を紹介する旅のしおり。いまは{len(trips)}編。", body, "", current="index", extra_head=head, tail=tail), encoding="utf-8")
if RAKUTEN_ON:
    (ROOT / "rakuten-status.json").write_text(json.dumps(rk_status, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- 宮城の蔵(蔵の一覧) ----------
trip_of = {t["kura"]: t for t in trips}


def kura_card(k):
    label, cls = TOUR[k["tour"]]
    links = []
    if k["id"] in trip_of:
        links.append(f'<a href="{e(k["id"])}.html">旅のしおりを見る</a>')
    if k.get("url"):
        links.append(f'<a href="{e(k["url"])}" target="_blank" rel="noopener">公式サイト</a>')
    links.append(f'<a href="https://miyagisake.jp/kuramoto/{e(k["id"])}/" target="_blank" rel="noopener">宮城県酒造組合の紹介</a>')
    trip = f'<p class="kt-kura-trip">旅のしおり:<a href="{e(k["id"])}.html">{e(trip_of[k["id"]]["title"])}</a></p>' if k["id"] in trip_of else ""
    return f'''        <article class="place kura" id="{e(k["id"])}" data-tour="{e(k["tour"])}">
          <div class="place-head"><h3>{e(k["name"])}</h3><span class="area">{e(k["city"])}</span></div>
          <div class="brands">{"".join(f"<span>{e(b)}</span>" for b in k["brands"])}</div>
          <p>{e(k["intro"])}</p>
          <dl class="info"><dt>創業</dt><dd>{e(k["founded"])}</dd><dt>見学</dt><dd><span class="tour {cls}">{label}</span> {e(k["tourNote"])}</dd></dl>
          {trip}
          <div class="links">{"".join(links)}</div>
        </article>'''


kura_secs = []
for i, a in enumerate(AREAS, start=1):
    ks = [k for k in kura.values() if k["area"] == a]
    kura_secs.append(f'''  <section class="section area-sec" id="area{i}">
    <div class="wrap">
      <div class="section-head"><h2>{e(a)}</h2><p>{len(ks)}蔵</p></div>
      <div class="places">
{chr(10).join(kura_card(k) for k in ks)}
      </div>
    </div>
  </section>''')
jump = "".join(f'<a href="#area{i}">{e(a)}</a>' for i, a in enumerate(AREAS, start=1))
n_yes = sum(1 for k in kura.values() if k["tour"] == "yes")
body = f'''  <section class="section">
    <div class="wrap stack">
      <div class="section-head"><h1>宮城の蔵</h1><p>{len(kura)}蔵 ・ 旅のしおりは{len(trips)}編</p></div>
      <p class="kt-body">宮城県酒造組合に加盟する{len(kura)}の蔵を、地域ごとに並べました。訪ねる蔵を選ぶときに、見学の受け入れとあわせて見てください。</p>
      <nav class="jump" aria-label="地域">{jump}</nav>
      <div class="chips"><button type="button" class="chip" id="only-tour" aria-pressed="false">見学できる蔵だけ表示({n_yes}蔵)</button></div>
      <p class="notice">見学の受け入れや時期は変わることがあります。訪問前に必ず各蔵へ問い合わせてください。蔵の情報は<a href="https://miyagisake.jp/kuramoto/" target="_blank" rel="noopener">宮城県酒造組合</a>の蔵元紹介をもとにしています。</p>
    </div>
  </section>

{chr(10).join(kura_secs)}'''
tail = '''<script>
(function () {
  var b = document.getElementById('only-tour');
  b.addEventListener('click', function () {
    var on = b.getAttribute('aria-pressed') !== 'true';
    b.setAttribute('aria-pressed', String(on));
    Array.prototype.forEach.call(document.querySelectorAll('.kura'), function (c) {
      c.hidden = on && c.getAttribute('data-tour') !== 'yes';
    });
    Array.prototype.forEach.call(document.querySelectorAll('.area-sec'), function (s) {
      s.hidden = !s.querySelector('.kura:not([hidden])');
    });
  });
})();
</script>
'''
(ROOT / "kura.html").write_text(shell("宮城の蔵|蔵旅 by 一献", f"宮城県の酒蔵{len(kura)}蔵の紹介と見学の受け入れ。旅のしおりのある蔵は、そのまま旅程へ。", body, "kura.html", current="kura", tail=tail), encoding="utf-8")
# ---------- 検索エンジン向けのページ一覧 ----------
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{SITE}{p}</loc></url>\n" for p in sorted(set(SITEMAP)))
    + "</urlset>\n", encoding="utf-8")
print("蔵旅", len(trips), "編")
print("楽天トラベル:", "取得 " + str(len(rk_status["ok"])) + " / 空 " + str(len(rk_status["empty"])) + " / エラー " + str(len(rk_status["errors"])) if RAKUTEN_ON else "止めています")
