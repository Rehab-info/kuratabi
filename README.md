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
.nojekyll           GitHub Pages の Jekyll 処理を無効化
```

## GitHub Pages で公開する

1. GitHub で新しいリポジトリを作成(例:`kuratabi`)
2. このフォルダの中身をすべてアップロード
3. Settings → Pages → Source を「GitHub Actions」にする
4. 上げるたびに `tools/build.py` が自動で動き、`https://<ユーザー名>.github.io/kuratabi/` に公開されます

## 旅のしおりを足す

`data/kuratabi.json` の `trips` に1件追加し、`python3 tools/build.py` を実行します(GitHub に上げれば自動でも実行されます)。

```json
{
  "kura": "otokoyama",          // data/kura.json の蔵 ID
  "with": [],                   // 同じ町にあるほかの蔵の ID(任意)
  "ikkon": [{"id": "soutenden", "name": "蒼天伝 …"}],  // 一献で紹介している銘柄(任意)
  "title": "旅の名前(◯◯と、◯◯)",
  "lead": "2〜3文の紹介",
  "access": "行き方",
  "length": "半日 / 1日 など",
  "spots": [{"kind": "港", "name": "見どころの名前", "note": "一言", "map": "地図検索の言葉"}],
  "course": [{"time": "10:00", "text": "することの説明"}],
  "tips": ["出かける前の注意"]
}
```

- `kind` は見どころの種類を1〜2文字で(社・城・湯・港・市場・館 など)。金色の印に入ります。
- 見どころの情報は、実際に行ったときや公式サイトで確かめてから書いてください。

## 蔵の情報を更新する

見学の可否などは一献の `data/kura.json` が元です。一献側を直したら、このリポジトリの `data/kura.json` にも写してください。

## 手元で確認する

```
python3 tools/build.py
python3 -m http.server 8000
# → http://localhost:8000
```
