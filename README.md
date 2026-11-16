# rakuten-shorts-affiliate

楽天アフィリエイト向け YouTube Shorts の制作プロジェクト。
**商品画像を使わずに成立する**フォーマットを前提に、規約・法規・ジャンル選定・台本を管理する。

既存の歴史系 Shorts プロジェクト（`E:\rekishikaisetu-honnoji`）から、アフィリエイト関連の調査・設計・台本だけを移設した独立プロジェクト。

## まず読む

| 順 | 文書 | 内容 |
| --- | --- | --- |
| 1 | [`AGENTS.md`](AGENTS.md) | 制作時に守るルール（これを破ると規約違反・アカウント停止） |
| 2 | [`docs/RAKUTEN_AFFILIATE_PIPELINE.md`](docs/RAKUTEN_AFFILIATE_PIPELINE.md) | 制約を踏まえた設計メモ・収益試算・前提条件 |
| 3 | [`docs/research/20261116_rakuten_api_and_terms.md`](docs/research/20261116_rakuten_api_and_terms.md) | 楽天アフィリエイト規約 / 楽天ウェブサービスAPI の一次資料調査 |
| 4 | [`docs/research/20261116_ad_rules_and_platform_policy.md`](docs/research/20261116_ad_rules_and_platform_policy.md) | 景表法・ステマ規制・薬機法・著作権・YouTubeポリシー |
| 5 | [`docs/research/20261116_shorts_genre_scan.md`](docs/research/20261116_shorts_genre_scan.md) | 商品画像なしで成立するジャンルの実測 |
| 6 | [`docs/RENDER_PIPELINE.md`](docs/RENDER_PIPELINE.md) | 台本から MP4 を作る工程（PR・種別ラベル・BGM・動画背景の焼き込み） |
| 7 | [`docs/RIGHTS_LEDGER.md`](docs/RIGHTS_LEDGER.md) | 素材ごとの権利条件と表記 |
| 8 | [`docs/PRODUCTION_LOG.md`](docs/PRODUCTION_LOG.md) | 作ったもの・確認したこと・残っていること |

## この企画の要点（迷ったらここに戻る）

1. **商品画像は動画に使えない。** 楽天のAPI由来情報は「商品紹介＋リンク」目的に限定・複製改変禁止。リンク作成ページの画像も「一部を切り取って使用」「画像上の文字」が禁止。動画への焼き込みを許諾する明文は無い。
2. **レビュー本文は使えない。** 「みんなのレビューを転載、転用、編集、複製すること」が禁止行為。レビューAPIも存在しない（ゲートウェイが404）。
3. **Shorts の説明欄 URL はクリックできない。** 導線はチャンネルプロフィールのリンク、または YouTube ショッピングの商品タグ（YPP参加が前提）。
4. **AI量産はスパムポリシーに近い。** 「AI を使用して類似したコンテンツを最小限の変更で大量に量産する行為」が例示されている。
5. **「物の形が中身」のジャンルは画像なしでは勝てない。** 実測ではスマホ設定／電気代／一人暮らし節約が画像なしで成立、収納・掃除・キッチン・防災・高齢者グッズは実写必須だった。

## 構成

```
docs/            設計メモと調査（一次資料の引用つき）
shorts-standard/ 台本の制作標準（JSONスキーマと検査器）
scripts/         shorts_standard.py（検査・変換）／render_short.py（描画）
shorts/          作品ごとの台本（brief.yaml / result.json / render.json / art/）
out/             完成物（下書きは out/draft/。.gitignore 済み）
```

## 台本の作り方

```powershell
python scripts/shorts_standard.py new <slug> --topic "題材"
# brief.yaml の source_urls / verified_facts を、実際に開いて確認した内容で埋める
python scripts/shorts_standard.py brief-check shorts/<slug>/brief.yaml
# result.json を作る（shorts-standard/PROMPT.md の指示に従う）
python scripts/shorts_standard.py check shorts/<slug>/result.json
```

`check` は `validate.py`（形式）＋追加規則。ERROR 0 が合格。
**`status: ready` は人の原文照合が済んでから。** `needs_research` が残っている間は `ready` にできない（`to-spec` も通らない）。

## 動画の作り方（描画）

```powershell
python scripts/render_short.py <slug> --plan   # 音声を合成し、実測尺を result.json に書き戻す
python scripts/shorts_standard.py check shorts/<slug>/result.json   # 尺が変わったので検査し直す
python scripts/render_short.py <slug>          # MP4・SRT・説明欄・固定コメント・サムネを作る
```

- `status` が `ready` 以外なら **`out/draft/` にしか書かない**（公開用の `out/` には出さない）。
- 「PR」・「イメージ（AI生成）」・「模式図」・出典は描画時に焼き込む。詳しくは [`docs/RENDER_PIPELINE.md`](docs/RENDER_PIPELINE.md)。
- 背景の動画クリップは FreeVideo（ローカル ComfyUI）で作る: `python scripts/gen_freevideo.py shorts/<slug>/clips.json --slug <slug>`。
- BGM は `shorts/<slug>/render.json` の `bgm` で指定（クレジットは説明欄に自動で入る）。

## 必要なもの

- Python 3（`pip install -r requirements.txt`）
- 台本の検査だけならこれで足りる。描画するなら VOICEVOX（`127.0.0.1:50021`）と FFmpeg が別途必要。

## 現在の状態（2026-11-17）

- 調査・設計は完了。台本 `shorts/kaito_plate`（解凍プレート）は `needs_review` のまま。
- **描画パイプラインを追加し、下書き1本目を書き出した**（`out/draft/kaito_plate_DRAFT.mp4` / 34.34秒）。
  PR全編・種別ラベル・キャプション・出典の焼き込みは実装済み（[`docs/PRODUCTION_LOG.md`](docs/PRODUCTION_LOG.md)）。
- **未着手**: 新チャンネル作成、楽天アフィリエイトへのサイト登録、楽天のAPIキー取得（管理画面が 2026-11-09 から停止中）。
- 公開のブロッカー: 楽天ROOMのURLが無い（動画の最後で「プロフィールの楽天ルームにまとめています」と言っている）。
- `shorts/kaito_plate` は「キッチン時短」＝実写必須と判定されたジャンルの題材なので、**画像なしの不利を確かめるテストケース**という位置づけ。
