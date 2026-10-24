"""一度だけ座標を調べるための使い捨てスクリプト(Actions で実行してログに出す)。"""
import json, time, urllib.parse, urllib.request
Q = [
 ("saura","浦霞 佐浦","宮城県塩竈市本町2-19"),
 ("abekan","阿部勘酒造",""),
 ("ichinokura","一ノ蔵","宮城県大崎市松山千石字大欅14"),
 ("zao","蔵王酒造","宮城県白石市東小路"),
 ("ichiba","塩釜水産物仲卸市場","宮城県塩竈市新浜町1-20-74"),
 ("jinja","鹽竈神社","宮城県塩竈市一森山1-1"),
 ("gallery","浦霞 酒ギャラリー",""),
 ("marine","マリンゲート塩釜","宮城県塩竈市港町1-4-1"),
 ("museum","松山酒ミュージアム",""),
 ("gohonmaru","御本丸公園",""),
 ("naruko","鳴子温泉駅",""),
 ("tenjikan","蔵王酒造展示館","宮城県白石市東小路120-1"),
 ("shiroishijo","白石城","宮城県白石市益岡町1-16"),
 ("okama","御釜",""),
 ("st_honshiogama","本塩釜駅",""),
 ("st_matsuyama","松山町駅",""),
 ("st_shiroishi","白石駅",""),
]
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
print("GEO_BEGIN")
print(json.dumps(out, ensure_ascii=False, indent=1))
print("GEO_END")
