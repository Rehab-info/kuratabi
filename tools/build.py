"""data/kuratabi.json と data/kura.json から「蔵旅 by 一献」のページを作るスクリプト。
使い方: python3 tools/build.py

旅のしおりを足すときは data/kuratabi.json の trips に1件追加して、このスクリプトを実行してください。
蔵の名前・見学の可否・創業などは data/kura.json から読み込みます(一献の data/kura.json を写したもの)。
GitHub に上げると、公開の仕組みでも自動で実行されます。
assets/style.css を直したら、下の VERSION を1つ上げてください(閲覧者のブラウザに古い版が残らなくなります)。
"""
import html
import json
import sys
from pathlib import Path
from urllib.parse import quote

VERSION = "1"
IKKON = "https://rehab-info.github.io/ikkon/"  # 一献の住所(独自ドメインに移したらここを直す)

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data/kuratabi.json").read_text(encoding="utf-8"))
kura = {k["id"]: k for k in json.loads((ROOT / "data/kura.json").read_text(encoding="utf-8"))}
kura_order = list(kura)
e = html.escape

AREAS = ["仙台・県央", "県南", "塩竈", "大崎・加美・遠田", "栗原・登米", "石巻・気仙沼"]
TOUR = {"yes": ("見学できる", "tour-yes"), "partial": ("一部見学", "tour-ask"), "ask": ("要相談", "tour-ask"), "no": ("見学不可", "tour-no")}

# 打ち間違いで旅のしおりが黙って消えたり壊れたりしないよう、先に確かめる
TRIP_KEYS = ["kura", "title", "lead", "access", "length", "spots", "course"]
errors, seen = [], set()
for i, t in enumerate(data["trips"], start=1):
    where = t.get("kura") or f"{i}番目の旅"
    errors += [f"{where}: 「{k}」がありません" for k in TRIP_KEYS if not t.get(k)]
    if t.get("kura") not in kura:
        errors.append(f"{where}: 蔵 ID「{t.get('kura')}」が data/kura.json にありません")
    if t.get("kura") in seen:
        errors.append(f"{where}: 同じ蔵の旅が2つあります")
    seen.add(t.get("kura"))
    for w in t.get("with", []):
        if w not in kura:
            errors.append(f"{where}: with の蔵 ID「{w}」が data/kura.json にありません")
    for j, s in enumerate(t.get("spots", []), start=1):
        errors += [f"{where}: 見どころ{j}に「{k}」がありません" for k in ["kind", "name", "note"] if not s.get(k)]
    for j, c in enumerate(t.get("course", []), start=1):
        errors += [f"{where}: 旅程{j}に「{k}」がありません" for k in ["time", "text"] if not c.get(k)]
for k in kura.values():
    if k["area"] not in AREAS:
        errors.append(f'{k["id"]}: 地域「{k["area"]}」が AREAS にありません')
    if k["tour"] not in TOUR:
        errors.append(f'{k["id"]}: 見学「{k["tour"]}」が TOUR にありません')
if errors:
    sys.exit("データに誤りがあります:\n" + "\n".join(errors))

trips = sorted(data["trips"], key=lambda t: kura_order.index(t["kura"]))


def shell(title, desc, body, home=False):
    cur = ' aria-current="page"' if home else ""
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;700&family=Zen+Kaku+Gothic+New:wght@400;700&display=swap">
<link rel="stylesheet" href="assets/style.css?v={VERSION}">
</head>
<body>
<header class="site-head">
  <div class="wrap">
    <a class="logo" href="index.html"><span class="mark" aria-hidden="true"></span><b>蔵旅</b><small>by 一献</small></a>
    <nav class="nav"><a href="index.html"{cur}>旅のしおり</a><a href="{IKKON}kura.html">宮城の蔵</a><a href="{IKKON}">一献</a></nav>
  </div>
</header>

<main>
{body}
</main>

<footer class="site-foot">
  <div class="wrap">
    <span>見学の受け入れや店の営業は変わることがあります。出かける前に必ず各蔵・各施設へ確かめてください。情報は{e(data["checked"])}に確認しました。</span>
    <span>試飲をする日は、電車やバス、運転しない人と。お酒は20歳になってから。飲酒運転は法律で禁止されています。</span>
    <span>蔵旅は、日本酒案内「<a href="{IKKON}">一献</a>」の旅のしおりです。</span>
  </div>
</footer>
</body>
</html>
'''


def map_link(q):
    return f"https://www.google.com/maps/search/?api=1&query={quote(q)}"


# ---------- 蔵ごとのページ ----------
for t in trips:
    k = kura[t["kura"]]
    label, cls = TOUR[k["tour"]]
    brands = "".join(f"<span>{e(b)}</span>" for b in k["brands"])
    others = "".join(f'<dt>近くの蔵</dt><dd><a href="{IKKON}kura.html#{e(w)}">{e(kura[w]["name"])}</a>(見学:{TOUR[kura[w]["tour"]][0]})</dd>' for w in t.get("with", []))
    spots = "\n".join(f'''        <li class="kt-spot">
          <span class="kt-kind{" kt-k2" if len(s["kind"]) > 1 else ""}" aria-hidden="true">{e(s["kind"])}</span>
          <div><h3>{e(s["name"])}</h3><p>{e(s["note"])}</p></div>
          <a class="kt-map" href="{e(map_link(s.get("map") or s["name"]))}" target="_blank" rel="noopener">地図で見る</a>
        </li>''' for s in t["spots"])
    course = "\n".join(f'          <li><time>{e(c["time"])}</time><span class="dot" aria-hidden="true"></span><span>{e(c["text"])}</span></li>' for c in t["course"])
    tips = '<ul class="kt-tips">' + "".join(f"<li>{e(x)}</li>" for x in t.get("tips", [])) + "</ul>" if t.get("tips") else ""
    links = [f'<a href="{IKKON}index.html#{e(s["id"])}">{e(s["name"])}を一献で見る</a>' for s in t.get("ikkon", [])]
    links.append(f'<a href="{IKKON}kura.html#{e(k["id"])}">{e(k["name"])}の紹介(一献)</a>')
    if k.get("url"):
        links.append(f'<a href="{e(k["url"])}" target="_blank" rel="noopener">蔵の公式サイト</a>')
    nexts = "".join(f'<a class="kt-trip" href="{e(o["kura"])}.html"><small>{e(kura[o["kura"]]["city"])}</small><h3>{e(o["title"])}</h3><span class="kt-kura">{e(kura[o["kura"]]["name"])}</span></a>'
                    for o in trips if o is not t)

    body = f'''  <div class="wrap"><nav class="kt-crumb" aria-label="現在地"><a href="index.html">蔵旅</a><span>›</span><span>{e(k["area"])}</span><span>›</span><span>{e(k["name"])}</span></nav></div>
  <section class="section" style="padding-top:0">
    <div class="wrap kt-head">
      <div>
        <div class="eyebrow">{e(k["city"])} ・ {e(t["length"])}の旅</div>
        <h1>{e(t["title"])}</h1>
        <p class="kt-title">{e(k["name"])}をたずねて</p>
        <div class="brands">{brands}</div>
        <p class="kt-lead">{e(t["lead"])}</p>
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

  <section class="section">
    <div class="wrap">
      <div class="section-head"><h2>まちの見どころ</h2><p>蔵とあわせて歩きたい場所</p></div>
      <ul class="kt-spots">
{spots}
      </ul>
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
        <div class="links kt-links">{"".join(links)}</div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><h2>ほかの蔵旅</h2></div>
      <div class="kt-next">{nexts}</div>
    </div>
  </section>'''
    desc = f'{k["name"]}({k["city"]})をたずねる旅。{t["lead"]}'[:120]
    (ROOT / f'{k["id"]}.html').write_text(shell(f'{t["title"]} | 蔵旅 by 一献', desc, body), encoding="utf-8")

# ---------- 入口のページ ----------
cards = "\n".join(f'''        <a class="kt-trip" href="{e(t["kura"])}.html">
          <small>{e(kura[t["kura"]]["city"])} ・ {e(t["length"])}</small>
          <h3>{e(t["title"])}</h3>
          <span class="kt-kura">{e(kura[t["kura"]]["name"])}({"・".join(e(b) for b in kura[t["kura"]]["brands"])})</span>
          <p>{e(t["lead"])}</p>
          <span class="series-more">旅のしおりを開く</span>
        </a>''' for t in trips)
side = "".join(f'<a href="{e(t["kura"])}.html">{e(t["title"])}</a>' for t in trips)

rest_html = []
for a in AREAS:
    ks = [k for k in kura.values() if k["area"] == a and k["id"] not in seen]
    if ks:
        items = "".join(f'<li><a href="{IKKON}kura.html#{e(k["id"])}">{e(k["name"])}</a><span class="kt-city">{e(k["city"])}・{TOUR[k["tour"]][0]}</span></li>' for k in ks)
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

  <section class="section">
    <div class="wrap">
      <div class="section-head"><h2>旅のしおり</h2><p>蔵と、そのまわりの見どころと、一日の流れ</p></div>
      <div class="kt-trips">
{cards}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><h2>これから訪ねる蔵</h2><p>旅のしおりは順に増やしていきます</p></div>
{chr(10).join(rest_html)}
      <p class="notice">蔵の名前を押すと、一献の「宮城の蔵」で紹介を読めます。</p>
    </div>
  </section>'''
(ROOT / "index.html").write_text(shell("蔵旅 by 一献", f"宮城の酒蔵をたずね、蔵のまわりの見どころと一日の旅程を紹介する旅のしおり。いまは{len(trips)}編。", body, home=True), encoding="utf-8")
print("蔵旅", len(trips), "編")
