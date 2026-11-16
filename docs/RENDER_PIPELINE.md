# 描画パイプライン（Shorts / 2026-11-17 追加）

`shorts-standard` の台本（`result.json`）から、9:16・1080x1920 の MP4 を作る工程。
**台本の検査（`shorts_standard.py check`）はこの工程の前段**で、ここでは形式検査をやり直さない。

## 手順

```powershell
# 1. 音声を合成して実測尺を台本へ書き戻す（描画はしない）
python scripts/render_short.py <slug> --plan

# 2. 尺が変わったので検査をやり直す（ERROR 0 を確認）
python scripts/shorts_standard.py check shorts/<slug>/result.json

# 3. 描画（MP4・SRT・説明欄・固定コメント・サムネ）
python scripts/render_short.py <slug>
```

- 2 を飛ばすと、検査したタイミングと描画がずれる。`render_short.py` は尺の差が 0.2 秒を超えると中止する。
- `--plan` は `start` / `end` / `duration_sec` だけを書き換える。`narration` などの本文は触らない。

## 出力

| status | 出力先 | 意味 |
| --- | --- | --- |
| `ready` | `out/<slug>.mp4` | 公開してよい（人の原文照合済み） |
| `needs_review` | `out/draft/<slug>_DRAFT.mp4` | **下書き。公開しない。** 未確認事項を表示する |

`out/` と `cache/` は `.gitignore` 済み（`*.mp4` / `*.wav` も除外）。

## 画面に必ず焼くもの

- **「PR」**：全フレームの左上。ステマ告示は冒頭だけでは不十分とされるため、全編に出す。説明欄の冒頭・固定コメントにも入れる。
- **種別ラベル**：AI生成の情景は「イメージ（AI生成）」、自分で描いた図解は「模式図」。実写資料と混同させない。
- **キャプション**：`caption` の2行以内。下部の帯に出す。1行14文字以内は検査済み。
- **出典**：`claim_ids` があるシーンだけ、帯の中に小さく「出典: …」を出す。全文は説明欄に書く（画面下端に押し込まない）。
- **タイトル**：上部。種別ラベルと重ならないよう、ラベルの下に置く。

## 音声

- VOICEVOX ENGINE（`127.0.0.1:50021`）で合成。話者は `shorts/<slug>/render.json` の `speaker` / `style` / `speed`。
- 読みの調整は `shorts/<slug>/pron.json`（任意。辞書形式で置換）。
- ラウドネスは `loudnorm=I=-14:TP=-1.5`。実測は `kaito_plate` で **-15.3 LUFS / True Peak -1.4 dBFS**（TP 制約で -14 に届かないが、ピークは守っている）。
- シーンの尺は**実測音声**から決める（`GAP=0.35` / `TAIL=0.45` / `LEAD=0.10`）。全体が30秒未満なら、9秒を上限に各シーンへ配分する。

## 素材

- `shorts/<slug>/art/scene_01.png …`（シーン数ぶん）。1080x1920 を推奨（違う比率は cover で切る）。
- 図解は `shorts/kaito_plate/art/build_diagrams.py` のように **PIL で描く**。数値・文字を生成AIに任せない。
- 写真が必要なときは、生成AIの**情景イメージ**だけを作る。商品そのもの・ロゴ・パッケージを描かせない（プロンプトに明記し、出力後に目視確認する）。

### 画像生成の経路（2026-11-17 の実測）

- このセッションの `image_generate` ツール（gpt-image-2 / grok）は **403 Forbidden** と「accounts are cooling down」で失敗した。
- 代わりに **ログイン済み Chrome の ChatGPT（Web UI）** で生成した。手順は、`chatgpt.com/?q=<プロンプト>` を開く → 送信 → 縦長画像が出たら `<a download>` で保存 → `Downloads/` のファイルを `shorts/<slug>/art/` へ移動。
- 1回だけ「コンテンツポリシー違反の可能性」で拒否された（朝のキッチン＋弁当のプロンプト）。同じ趣旨を言い換えたら通った。
- 生成サイズは 941x1672（≒9:16）。9:16 を指定すると比率は概ね守られる。

## 既知の制約

- Shorts の説明欄 URL はクリックできない。導線はチャンネルプロフィールのリンク（楽天ROOM）に限る。
- BGM は入れていない（定型BGMの使い回しを避ける方針と、権利処理の単純化のため）。入れる場合はクレジットを説明欄へ。
- `kaito_plate` の台本は「キッチン時短」＝実写必須と判定されたジャンルの題材で、画像なしの不利を確かめるテストケース。
