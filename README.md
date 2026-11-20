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
scripts/         shorts_standard.py（検査・変換）／render_yorimichi.py（新規の描画）／render_short.py（旧描画・比較用）／cdp_client.py（生CDPの共通処理）
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
**`status: ready` は、証跡を作ってオーナーの承認を取ってから。** `needs_research` が残っている間は `ready` にできない。

```powershell
python scripts/approve.py prepare <slug>   # 出典・商品・表記・レビューを照合し verification.json を作る
python scripts/approve.py sign <slug> --by owner   # 承認（有効期限14日）→ status: ready
```
承認後に `result.json` を変えると承認は無効になる（SHA-256 で検査）。`--plan` は承認より前に実行する。
詳細は [`docs/WORKFLOW.md`](docs/WORKFLOW.md)。

## 動画の作り方（描画）

新規動画は**寄り道ラボ方式**（`render_yorimichi.py`）で描画する。旧 `render_short.py` は既存動画の再描画・比較用に残す。

```powershell
python scripts/render_yorimichi.py <slug> --plan   # 音声を合成し、実測尺を result.json に書き戻す
python scripts/shorts_standard.py check shorts/<slug>/result.json   # 尺が変わったので検査し直す
# 承認（approve.py prepare → sign）の後で spec を作る
python scripts/shorts_standard.py to-spec shorts/<slug>/result.json --slug <slug>
python scripts/render_yorimichi.py <slug>          # MP4・SRT・説明欄・固定コメント・サムネを作る
python scripts/gate.py <slug>                      # 承認・成果物・指紋・リンクを公開前に検査
```

- `render_yorimichi.py` は `shorts/<slug>/short_spec.json` を直接読む。`data/` には自動コピーしない。
- 画面は寄り道ラボの `make_short2.py` 風（タイトル・大テロップ・Ken Burns・字幕・BGM）に、
  **PR・種別ラベル・出典**を全編で重ねる（このプロジェクトの規約を維持）。
- `status` が `ready` 以外なら **`out/draft/` にしか書かない**（公開用の `out/` には出さない）。
- 「PR」・「イメージ（AI生成）」・「模式図」・出典は描画時に焼き込む。詳しくは [`docs/RENDER_PIPELINE.md`](docs/RENDER_PIPELINE.md)。
- 背景の動画クリップは FreeVideo（ローカル ComfyUI）で作る: `python scripts/gen_freevideo.py shorts/<slug>/clips.json --slug <slug>`。
- BGM は `shorts/<slug>/render.json` の `bgm` で指定（クレジットは説明欄に自動で入る）。

## アップロード（YouTube Studio）

```powershell
python scripts/upload_short.py <slug>            # 非公開で保存
python scripts/upload_short.py <slug> --publish  # 保存後に公開へ切り替える
python scripts/upload_short.py <slug> --check-only  # Studioを開かず、公開前検査だけ
```

- アップロード前に `gate.py` と同じ検査を通す（`status=ready`・承認が期限内・指紋一致・PR表記・リンク生存）。

- 分離Chrome（CDP 9222）が必要。起動方法は [`docs/CHANNEL_SETUP.md`](docs/CHANNEL_SETUP.md)。
- 各ボタンは「見えて有効になるまで待ってから実マウス相当で押す」。JSの `.click()` では
  Polymer の状態が更新されず、保存ボタンが無効のままになる。
- **1日のアップロード上限**を検出すると exit 2 で止まる（24時間待つか、Studioのワンタイム認証が必要）。
- アップロード後の公開切り替え・コメント投稿は個別スクリプト（`docs/CHANNEL_SETUP.md` 参照）。

## 必要なもの

- Python 3（`pip install -r requirements.txt`）
- 台本の検査だけならこれで足りる。描画するなら VOICEVOX（`127.0.0.1:50021`）と FFmpeg が別途必要。

## 現在の状態

チャンネル: **暮らしの判断メモ**（`@kurashi_hantei` / `UCBQ8nx5q0_P9NrtStUkSTEg`）。

**状態の一覧は [`docs/STATUS.md`](docs/STATUS.md) を見る。** これは `python scripts/status.py` が
`result.json` / `verification.json` / `publish.json` から生成する（手で編集しない）。

- 公開済み3本（`yFXNYLgMzmY` / `aVawDx0PiVg` / `zVQ7UoER4xM`）は**レビュー体制より前の旧フロー**。
  承認を捏造しないため `status` は `needs_review` のままにし、公開の事実は `publish.json` に残している。
- 未公開は4本（`kettle_heat` → `led_light` → `fridge_habits` → `iphone_battery` の順に週1）。
- `winter_three` は `ac_heater_saving` と同一出典・同一数値のため**保留**（`visibility: held`）。
- **1日のアップロード上限**が続いている。次の公開週に1回だけ試し、まだ上限ならワンタイム認証へ切り替える。
- プロフィールの外部リンクは**商品一覧ページ（hub）**を指す（2026-11-19）。動画内の案内は「商品名は説明欄に書いています」に統一。
- ピン留め（固定コメント）は自動化できず、手動 1 クリック。

公開までの順序と承認のルールは [`docs/WORKFLOW.md`](docs/WORKFLOW.md)。


## アフィリエイトリンクの作成

```powershell
python scripts/affiliate_link.py "https://item.rakuten.co.jp/<shop>/<item>/"
```

- 楽天アフィリエイトにログインした分離Chromeが必要。
- 返るURLを `shorts/<slug>/render.json` の `affiliate` に入れ、`python scripts/regen_text.py <slug>` で
  説明欄・固定コメントに反映する。公開済みなら Studio の説明欄を差し替える。

## 商品一覧ページ（hub）

公開リポジトリ [`neoenox/kurashi-hantei`](https://github.com/neoenox/kurashi-hantei) の
<https://neoenox.github.io/kurashi-hantei/>。公開済み動画の商品を1ページにまとめ、チャンネルの
プロフィールリンクの行き先になる。

```powershell
gh repo clone neoenox/kurashi-hantei ../kurashi-hantei   # 初回だけ
python scripts/build_hub.py            # 生成・検査・差分表示（commit しない）
python scripts/build_hub.py --deploy   # 検査を通ったら commit して push
python scripts/build_hub.py --verify   # リンクが生きているか確認（書き込みなし）
```

- 生成物は clone 側の `index.html` だけ。このリポジトリに写しは置かない。
- カードが減る変更は `--allow-remove` を付けない限り中断する。
- 詳細は `docs/superpowers/specs/2026-11-19-revenue-path-design.md`。

## レビュー（台本・動画）

```powershell
python scripts/script_review.py <slug>     # 台本を ChatGPT と Gemini が査読
python scripts/muse_review.py <slug>       # 完成動画を Muse がレビュー（音声も聴ける）
```

- レビュー用Chrome（--remote-debugging-port=9223、プロファイル .chrome-automation）が必要。
- 返答は `shorts/<slug>/review_chatgpt.md` / `review_gemini.md` / `review_muse.md` に残す。
- 指摘は出典を確かめてから反映する。手順と実例は [docs/REVIEWS.md](docs/REVIEWS.md)。

## 数字の見方

- チャンネルの実測は [docs/ANALYTICS.md](docs/ANALYTICS.md) に日付つきで追記する。
- 判断基準（決定事項）: 3か月で**成果1件**＋**再生1,000回/本**。1本の数字で題材を決めない。

## Chrome の起動

```powershell
python scripts/chrome_launch.py channel   # YouTube Studio・楽天（9222 / .chrome-gemienox）
python scripts/chrome_launch.py review    # ChatGPT・Gemini・Muse（9223 / .chrome-automation）
```

- **最小化で開く**（2026-11-19 オーナー指示）。Chrome がセッション復元で最大化に戻る場合も、
  起動後に数回リトライして最小化する。
- 既にそのポートが開いていれば何もしない。`upload_short.py` / `muse_review.py` / `script_review.py` は
  ポートが閉じていれば自動でこのランチャーを呼ぶ。
