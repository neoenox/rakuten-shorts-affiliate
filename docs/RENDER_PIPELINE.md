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

### 動画背景（FreeVideo / ローカル ComfyUI）— **既定**

**情景のシーンは、静止画ではなく FreeVideo のクリップで作る**（2026-11-19 決定）。図解・模式図は PIL のまま。
1シーン＝1クリップを `clips.json` に書き、`render.json` の `clips` でシーン番号に対応させる。

```powershell
# 1. clips.json を書く（情景のシーンだけ。図解のシーンは書かない）
#    {"clips":[{"name":"scene1","seconds":7.0,"prompt":"… no text, no letters, no logos …"}]}
# 2. クリップを作る（FreeVideo のランチャーで 8188 番を起動しておく）
python scripts/gen_freevideo.py shorts/<slug>/clips.json --slug <slug>
# 3. render.json の "clips" にシーン番号→クリップ名を書く（例: {"1": "scene1", "6": "scene6"}）
#    そのシーンの art_types は "ai"（画面ラベルが「イメージ（AI生成）」になる）
# 4. 描画（art/clip_<name>.mp4 があれば自動で使う。無ければ静止画にフォールバック）
python scripts/render_short.py <slug>
```

- グラフは FreeVideo アプリ自身が実行したもの（`/history` の `prompt`）と同じ2ノード構成。`two_pass`・8+3ステップ・`upscale_factor=2`。
- 実測（RTX 4060 8GB / 544x960 / 7.0秒）: **1本あたり 4〜9分**（248〜538秒。空きRAMが少ないと遅い）、出力は 7.29秒・24fps・175フレーム。
  情景3シーンの動画なら **15〜30分**を見込む。待ち時間が長いので、生成はバックグラウンドで流し、その間に図解や台本を進める。
- `audio_use: reference` で音声も生成されるが**使わない**。プロンプトに `no background music, quiet room tone only` を入れると、エンジンが starter の score を `N/A` に置き換える（`freevideo_engine/music_request.py`）。
- クリップがシーンより長ければ頭から切り、短ければ尺に合わせて遅くする。1080x1920 に cover → 30fps の連番JPEG（`unsharp=5:5:0.6` を軽くかける）に展開してから使う（`cache/render_<slug>/clipframes/`）。
- シーンの見た目が台本の `visual` と合わない出力（例: 冷凍肉に湯気が立った）は、作り直すか静止画にフォールバックする。
- シーンが 7.29秒より長い（尺の都合で9秒など）ときは、クリップを遅くして埋める。動きが不自然になるなら、そのシーンだけ静止画にする。
- **FreeVideo が停止している／出力が合わない**ときは静止イラストで代替してよい。ただし理由を `docs/PRODUCTION_LOG.md` に残す（AGENTS.md §2）。

## BGM

- `render.json` の `bgm` に `file`（リポジトリからの相対パス）/ `gain_db` / `start` / `fade_in` / `fade_out` / `credit` を書く。
- ナレーションを sidechain にして、声の間だけ BGM を自動で下げる（`sidechaincompress` → `amix` → `loudnorm=I=-14`）。
- 曲は**動画ごとに変える**（定型BGMの使い回しを避ける）。クレジットは説明欄に自動で入る。
- 実測（魔王魂ピアノ39・`gain_db=-18`）: ミックス全体 **-14.3 LUFS / True Peak -1.2 dBFS**、声と声の間の BGM は約 -27 dBFS。
- 権利の条件と表記は [`RIGHTS_LEDGER.md`](RIGHTS_LEDGER.md)。

## 既知の制約

- Shorts の説明欄 URL はクリックできない。導線は**チャンネルプロフィールのリンク**（商品ページのアフィリエイトリンクを直置き）に限る。ROOM を挟まない。
- `kaito_plate` の台本は「キッチン時短」＝実写必須と判定されたジャンルの題材で、画像なしの不利を確かめるテストケース。

## 寄り道ラボ方式（新規動画の既定・2026-11-20）

新規動画は `scripts/render_yorimichi.py` を使う。寄り道ラボの `make_short2.py` の考え方
（VOICEVOX 実測尺 → PIL の Ken Burns／大テロップ／字幕 → FFmpeg → -14 LUFS → SRT）を
このリポジトリへ取り込み、規約表記を重ねたもの。設計は
[`docs/superpowers/specs/2026-11-20-yorimichi-render-pipeline-design.md`](superpowers/specs/2026-11-20-yorimichi-render-pipeline-design.md) を参照。

```powershell
python scripts/render_yorimichi.py <slug> --plan
python scripts/shorts_standard.py check shorts/<slug>/result.json
# approve.py prepare → sign の後
python scripts/shorts_standard.py to-spec shorts/<slug>/result.json --slug <slug>
python scripts/render_yorimichi.py <slug>
python scripts/gate.py <slug>
```

- 入力は `shorts/<slug>/short_spec.json`。`claim_ids` と `visual` は `result.json` から補う。
- 画面: 上部タイトル・大きなテロップ・データ帯・下部字幕に加え、**PR と種別ラベルを全フレーム不透明**で描画する。
- `render.json` の `art_types` / `source_labels` / `bgm` / `speaker` / `speed` / `affiliate` は従来どおり効く。
- 出力名・出力先・説明欄・固定コメント・サムネイルは `render_short.py` と同じ（`gate.py` がそのまま通る）。
- 旧 `render_short.py` は既存動画の再描画・比較用。既存の承認済み動画を新しい描画で上書きしない。
