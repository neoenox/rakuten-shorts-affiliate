# BGM の置き場所

音源そのものは**リポジトリに入れない**（魔王魂の規約で二次配布が禁止されているため。`.gitignore` 済み）。

## 手順

1. <https://maou.audio/> の「ピアノ39」の曲ページを開き、mp3 を取得する。
   - 既存プロジェクト `E:\rekishikaisetu-honnoji\assets\bgm_maou\maou_bgm_piano39.mp3` をそのまま複製してもよい。
2. `assets/bgm/maou_bgm_piano39_maoudamashii.mp3` として置く（ファイル名に `maoudamashii` を入れるのは、他サイトへの誤登録を避けるため）。
3. `shorts/<slug>/render.json` の `bgm.file` がこのパスを指していることを確認する。

## 表記（説明欄に自動で入る）

```
音楽：魔王魂「ピアノ39」（作曲：森田交一） https://maou.audio/
```

規約 <https://maou.audio/rule/>：商用・収益化可、著作表記が必要、音量・尺の加工可。
自作と偽る、mp3の二次配布、生成AIへの学習、他サイトへの登録は禁止。
詳細と Content ID の注意は [`docs/RIGHTS_LEDGER.md`](../../docs/RIGHTS_LEDGER.md)。
