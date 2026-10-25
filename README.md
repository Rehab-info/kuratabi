# 蔵旅 by 一献

酒蔵をたずね、蔵のまわりの見どころと一日の旅程を紹介する「旅のしおり」のサイトです。日本酒案内「一献」がつくっています。蔵の紹介も旅程もこのサイトの中で完結させ、しおりの「この蔵の酒」とフッターの「一献のなかま」から、一献とカップ酒図鑑へつないでいます。

## ファイル構成

```
index.html          入口(tools/build.py が自動で作る)
<蔵のID>.html        蔵ごとの旅のしおり(自動で作る)
kura.html           宮城の蔵の一覧(data/kura.json から自動で作る)
data/kuratabi.json  旅のしおりのデータ(ここを編集して旅を追加)
data/kura.json      宮城の蔵のデータ(名前・地域・見学の可否・紹介文など)
assets/style.css    デザイン
tools/build.py      ページを作り直すスクリプト
sitemap.xml         検索エンジン向けのページ一覧(tools/build.py が自動で作る)
data/sites.json     一献のなかま4サービスの住所(一献・カップ酒図鑑と同じ内容。独自ドメインに移すときはここを直す)
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
  "sakes": ["蒼天伝 …"],        // 「この蔵の酒」で旅のおともに挙げる酒(任意)
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
  "stay": [{"name": "◯◯温泉", "note": "一言", "map": "◯◯温泉 旅館"}],
  "tips": ["出かける前の注意"]
}
```

- 写真は `images/` に置き、`cover` に書くと表紙になります。自分で撮影したもの・許可を得たものだけを使ってください。写真がない間は、青海波の地に銘柄を縦に置いた表紙になります。
- 緯度・経度は、Google マップで場所を長押しすると出る数字(例:38.3164, 141.0193)をそのまま書けます。
- 「泊まるなら」には、楽天トラベルの宿のカードと予約リンクを出す仕組みがありますが、いまは止めています(宿の地名・一言・地図だけを出します)。再開するときは `tools/build.py` の `RAKUTEN_ON` を `True` にします。広告の表示も自動で戻ります。週1回宿を取り直すなら、`.github/workflows/pages.yml` に `schedule` を足します。検索の言葉を変えたいときは `stay` に `"travel": "鳴子温泉"` のように書きます。
- 見どころの情報は、実際に行ったときや公式サイトで確かめてから書いてください。

## 蔵の情報を更新する

見学の可否や紹介文は `data/kura.json` を直して `python3 tools/build.py` を実行します。宮城の蔵の一覧(`kura.html`)と、各しおりの「蔵のこと」に反映されます。

## 手元で確認する

```
python3 tools/build.py
python3 -m http.server 8000
# → http://localhost:8000
```

## 独自ドメインに移すとき

- `data/sites.json` が3つのリポジトリで同じかは、`tools/check_sites.py` が確かめます。`data/sites.json` を変えるプルリクエスト・main への反映・毎週月曜に GitHub Actions(Check sites.json)で自動で動き、食い違いがあれば項目ごとに理由を表示します。サイトの公開とは別の仕組みなので、食い違っていても公開は止まりません。3つを同時に直すときは、3つのリポジトリで同じ名前のブランチを使うと、そのブランチどうしで比べます。

1. 一献・蔵旅・カップ酒図鑑の3つのリポジトリの `data/sites.json` の `url` を新しい住所にそろえて書き換える(canonical・OGP・サイトマップ・ほかのサイトへのリンクはここから作られます)
2. それぞれ main に反映する(公開の仕組みがページを作り直す)
3. 楽天トラベルを再開するなら、`tools/build.py` の楽天への問い合わせの Referer・Origin と、楽天ウェブサービスのアプリの登録ドメインも新しい住所にする
4. Search Console に新しい住所を登録し直し、サイトマップを送り直す
