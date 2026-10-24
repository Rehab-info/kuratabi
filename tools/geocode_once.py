import json, time, urllib.parse, urllib.request
Q = [("otokoyama","男山本店","宮城県気仙沼市入沢3-8"),("otoko_shop","男山本店 魚町","宮城県気仙沼市魚町2-2-12"),
 ("uminoichi","海の市","宮城県気仙沼市魚市場前7-13"),("ichiba","気仙沼市魚市場","宮城県気仙沼市魚市場前8-25"),
 ("st_kesennuma","気仙沼駅",""),("orishi","巨釜",""),("kameyama","亀山 気仙沼大島",""),("naiwan","気仙沼 内湾 ムカエル",""),
 ("sasaki","佐々木酒造店","宮城県名取市閖上中央1-12-3"),("kawamachi","かわまちてらす閖上","宮城県名取市閖上中央1-6"),
 ("asaichi","ゆりあげ港朝市",""),("hiyoriyama","日和山 閖上",""),("st_natori","名取駅",""),
 ("onuma","大沼酒造店",""),("yamasho","やましょう記念館",""),("murata_annai","蔵の観光案内所 村田",""),("murata_yakuba","村田町役場","宮城県柴田郡村田町大字村田字迫6"),
 ("ishikoshi","石越醸造",""),("st_ishikoshi","石越駅",""),("izunuma","伊豆沼・内沼サンクチュアリセンター",""),("naganuma","長沼フートピア公園",""),("kyoiku","教育資料館 登米","")]
UA = {"User-Agent": "kuratabi-geocode/1.0 (https://github.com/Rehab-info/kuratabi)"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.load(r)
out = {}
for key, name, addr in Q:
    row = {"name": name}
    try:
        n = get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": name, "format": "json", "limit": 3, "countrycodes": "jp", "viewbox": "140.2,39.1,141.8,37.7", "bounded": 1}))
        row["osm"] = [(x["lat"], x["lon"], x["display_name"][:80]) for x in n]
    except Exception as ex:
        row["osm_err"] = str(ex)
    time.sleep(1.2)
    if addr:
        try:
            g = get("https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + urllib.parse.quote(addr))
            row["gsi"] = [(x["geometry"]["coordinates"][1], x["geometry"]["coordinates"][0], x["properties"]["title"]) for x in g[:2]]
        except Exception as ex:
            row["gsi_err"] = str(ex)
    out[key] = row
print(json.dumps(out, ensure_ascii=False, indent=1))
