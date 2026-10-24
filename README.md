# 蔵旅 by 一献

酒蔵をたずね、蔵のまわりの見どころと一日の旅程を紹介する「旅のしおり」のサイトです。日本酒案内「一献」の姉妹サイトで、デザインの土台は一献と共通です。

## ファイル構成

```
index.html          入口(tools/build.py が自動で作る)
<蔵のID>.html        蔵ごとの旅のしおり(自動で作る)
data/kuratabi.json  旅のしおりのデータ(ここを編集して旅を追加)
data/kura.json      宮城の蔵のデータ(一献の data/kura.json を写したもの)
assets/style.css    デザイン(一献の style.css に蔵旅の部品を足したもの)
tools/build.py      ページを作り直すスクリプト
assets/map.js       しおりの地図(Leaflet と OpenStreetMap)
assets/filter.js    入口の絞り込み
images/             写真(撮影したもの・許可を得たもの)
.nojekyll           GitHub Pages の Jekyll 処理を無効化
```

## GitHub Pages で公開する

1. GitHub で新しいリポジトリを作成(例:`kuratabi`)
2. このフォルダの中身をすべてアップロード
3. Settings → Pages → Source を「GitHub Actions」にする
4. 上げるたびに `tools/build.py` が自動で動き、`https://<ユーザー名>.github.io/kuratabi/` に公開されます

## 旅のしおりを足す

`data/kuratabi.json` の `trips` に1件追加し、`python3 tools/build.py` を実行します(GitHub に上げれば自動でも実行されます)。蔵の地図上の位置は `kuraGeo` に書きます。

```json
{
  "kura": "otokoyama",          // data/kura.json の蔵 ID
  "with": [],                   // 同じ町にあるほかの蔵の ID(任意)
  "ikkon": [{"id": "soutenden", "name": "蒼天伝 …"}],  // 一献で紹介している銘柄(任意)
  "title": "旅の名前(◯◯と、◯◯)",   // 「、」のところで改行して表示します
  "lead": "2〜3文の紹介",
  "access": "行き方",
  "station": {"name": "最寄り駅", "geo": [緯度, 経度]},
  "length": "半日 / 1日 など(表示用)",
  "lengthKey": "half",          // half=半日 day=1日(絞り込み用)
  "season": "おすすめの季節",
  "tags": ["電車で行ける", "温泉"],  // 入口の絞り込みに使われます
  "cover": {"src": "images/otokoyama.jpg", "alt": "写真の説明", "credit": "撮影:◯◯"},  // 写真がない間は null
  "spots": [{"kind": "港", "name": "見どころ", "note": "一言", "map": "地図検索の言葉",
             "geo": [緯度, 経度],          // 任意。あると地図に番号で出ます
             "far": true,                  // 任意。蔵から遠い場所は地図に入れず距離だけ出す
             "atKura": true,               // 任意。蔵と同じ場所(直営店など)
             "info": {"営業": "…", "定休": "…", "料金": "…"},  // 任意。確かめた情報だけ
             "url": "公式サイト"}],
  "course": [{"time": "10:00", "text": "することの説明"}],
  "stay": [{"name": "◯◯温泉", "note": "一言", "map": "◯◯温泉 旅館",
            "rakuten": "https://hb.afl.rakuten.co.jp/…"}],  // 任意。楽天トラベルへのリンク(下の「楽天トラベルとつなぐ」)
  "tips": ["出かける前の注意"]
}
```

- 写真は `images/` に置き、`cover` に書くと表紙になります。自分で撮影したもの・許可を得たものだけを使ってください。写真がない間は、青海波の地に銘柄を縦に置いた表紙になります。
- 緯度・経度は、Google マップで場所を長押しすると出る数字(例:38.3164, 141.0193)をそのまま書けます。
- 見どころの情報は、実際に行ったときや公式サイトで確かめてから書いてください。

## 楽天トラベルとつなぐ

「泊まるなら」の各項目に `rakuten` を書くと、「楽天トラベルで宿を探す」のボタンが出ます(地図のリンクは脇に残ります)。書かない間は、これまでどおり地図で宿を探すリンクだけです。

1. 楽天トラベルで、その温泉地や町の宿の一覧ページを開きます。
2. 楽天アフィリエイトの管理画面の「リンク作成」で、そのページのリンクを作ります。
3. できたリンク(`https://hb.afl.rakuten.co.jp/` で始まるもの)を `rakuten` にそのまま貼り、`python3 tools/build.py` を実行します。

- 楽天トラベルのページの住所(`https://travel.rakuten.co.jp/…`)をそのまま貼ってもボタンは出ます。その場合は紹介料は入りません。
- それ以外の住所を書くと、作り直すときに誤りとして止まります。
- 提携リンク(`hb.afl.rakuten.co.jp`)が1つでもあると、そのしおりの「泊まるなら」に「PR」の印が付き、すべてのページの下に楽天アフィリエイトに参加している旨が出ます。広告であることを示す決まり(ステルスマーケティング規制)への対応なので、消さないでください。

## 蔵の情報を更新する

見学の可否などは一献の `data/kura.json` が元です。一献側を直したら、このリポジトリの `data/kura.json` にも写してください。

## 手元で確認する

```
python3 tools/build.py
python3 -m http.server 8000
# → http://localhost:8000
```
