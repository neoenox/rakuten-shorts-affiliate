# 寄り道ラボ方式の描画パイプライン設計

作成日: 2026-11-20  
状態: 設計承認済み（実装前）

## 1. 背景と目的

寄り道ラボ（`E:\rekishikaisetu-honnoji`）とこのリポジトリは `shorts-standard/`（v1.1）を共有しているが、
描画・レビュー・公開の実装は異なる。

- 寄り道ラボ: `shorts/<slug>/result.json` → `shorts_standard.py to-spec` → `data/short_<slug>.json`
  → `scripts/make_short2.py`（VOICEVOX + PIL Ken Burns + FFmpeg + BGM + SRT）
- このリポジトリ: `result.json` → `scripts/render_short.py`（逐フレーム描画）→ `gate.py` → CDPアップロード

オーナーから「寄り道ラボと同じような動画作成方法を使いたい」と指示があり、
**描画工程のみ**を寄り道ラボ方式へ寄せる。台本標準、承認・ゲート、Museレビュー、公開経路は維持する。

## 2. 目標 / 非目標

### 目標

- `shorts_standard.py to-spec` の出力をそのまま描画入力にできる経路を作る。
- 寄り道ラボの実績ある見た目（タイトル、大きなテロップ、Ken Burns、字幕、BGM、-14 LUFS、SRT）を再現する。
- このリポジトリの規約（PR全編、種別ラベル、出典、アフィリエイト表記）を描画時に満たす。
- 既存の `approve.py` / `gate.py` / `upload_short.py` を変更せずに成果物を渡す。

### 非目標

- レビューを Google AI モードへ変更しない（Muse を維持）。
- 公開を `yt_api.py` / private→人手公開へ変更しない（CDP アップロードを維持）。
- `ffmpeg-skill` を採用しない（別タスク）。
- `shorts-standard/` のルールを緩めない。
- 既存の公開済み11本を再描画・再承認しない。

## 3. アーキテクチャとデータの流れ

```text
shorts/<slug>/result.json
  ├─ shorts_standard.py check            # 既存のまま
  ├─ render_yorimichi.py <slug> --plan   # 実測音声で start/end/duration を更新
  ├─ shorts_standard.py check            # 尺変更後の再検査
  ├─ shorts_standard.py to-spec          # short_spec.json を生成
  └─ render_yorimichi.py <slug>          # MP4 / SRT / 説明欄 / 固定コメント / サムネ
        ↓
approve.py prepare → sign                # 既存のまま（draft を承認）
        ↓
render_yorimichi.py <slug> --out-dir out # 再描画
        ↓
gate.py <slug> → upload_short.py         # 既存のまま
```

`--plan` は現在の `render_short.py --plan` と同じ役割（VOICEVOX で音声を合成し、実測尺を `result.json`
へ書き戻す）を持つ。描画は `result.json` の境界をそのまま使い、承認後の再描画で指紋が変わらないようにする。

## 4. コンポーネント

### 4.1 `scripts/render_yorimichi.py`（新規）

寄り道ラボの `scripts/make_short2.py` をこのリポジトリへコピーし、以下を改修したもの。元プロジェクトは変更しない。

再利用する考え方:

- 1080x1920 / 30fps / H.264 / AAC
- VOICEVOX（`127.0.0.1:50021`）でシーンごとに音声合成
- PIL で背景を cover + Ken Burns、見出し・大テロップ・データ帯・字幕を描画
- FFmpeg へ `rawvideo` を流し込み、`-14 LUFS` に揃えて mux
- SRT をナレーションと対応させて出力

このプロジェクト用の変更:

| 項目 | 対応 |
| --- | --- |
| PR | 全フレームに `PR` バッジを描画（フェードしない） |
| 種別ラベル | `render.json` の `art_types` から「イメージ（AI生成）」/「模式図」/「実写」を描画 |
| 出典 | `render.json` の `source_labels` を `claim_ids` に対応させて画面に描画 |
| 概要欄 | 既存 `render_short.description()` を再利用（【PR】・商品名・アフィリエイトURL・claims・AI生成表記） |
| 固定コメント | 既存 `render_short.fixed_comment()` を再利用 |
| CTA | `cta: false` を維持（登録呼びかけを追加しない） |
| BGM / 話者 | 寄り道ラボ固定の「四国めたん / 魔王魂 piano12」ではなく、このリポジトリの `render.json` 設定を使用 |
| サムネイル | 既存 `render_short.py` と同じロジックで PR 入りのフレームを保存（`gate.py` が必須とする） |
| 数値表記 | `hn_text.display()` 相当の正規化は、依存を増やさずこのリポジトリ内で最小実装するか、必要なければ使わない |

### 4.2 `shorts_standard.py to-spec`（既存をそのまま使用）

変換内容は既存どおり:

- `caption[0] → big`, `caption[1] → sub`
- `claims → notes` / `refs`
- `cta: false`
- `status` / `needs_research` は描画 spec にも残す
- `art_map.json` があればシーン別背景を割り当てる

出力先は既定の `shorts/<slug>/short_spec.json` のままとし、`data/` へは自動コピーしない（誤公開防止）。
`render_yorimichi.py` は `short_spec.json` を直接読む。

### 4.3 既存モジュールの扱い

| モジュール | 扱い |
| --- | --- |
| `scripts/render_short.py` | 残す。既存動画の再描画・比較用として維持し、新規の既定は `render_yorimichi.py` にする |
| `scripts/approve.py` | 変更なし |
| `scripts/gate.py` | 変更なし。新しい成果物も同じ指紋・表記検査を通す |
| `scripts/muse_review.py` | 変更なし |
| `scripts/upload_short.py` | 変更なし |
| `AGENTS.md` | 描画コマンドを追記するが、禁止事項と承認ルールは変更しない |

## 5. 規約の充足

| 要件 | 実装箇所 |
| --- | --- |
| 商品画像を使わない | 背景は `art_map.json` / `render.json` の AI生成・自作イラスト・模式図のみ |
| レビュー本文を使わない | claims の `statement` と `source_url` のみを説明欄に載せる |
| PR を全編に表示 | `render_yorimichi.py` の描画関数で毎フレーム描画 |
| AI生成物は「イメージ」と明記 | 種別ラベルと説明欄の両方に出典・種別を記載 |
| 数値は一次資料確認済みだけ | `result.json` の `claims` と `approve.py prepare` が担保 |
| クリック依頼をしない | `cta: false`、説明欄・固定コメントにも嘆願文を入れない |

## 6. テスト

- `tests/test_render_yorimichi.py` を新設
  - `to-spec` の変換結果（`caption → big/sub`、`claims → notes/refs`、`cta:false`）
  - PR バッジが全フレームで不透明であること（描画関数をモックして alpha を検証）
  - 種別ラベルが `art_types` に追随すること
  - 説明欄に【PR】・商品名・アフィリエイトURL・「AI生成」が入ること
  - サムネイルが PR 入りフレームから作られること
- 既存の全テスト（`pytest`）が通ること
- 1本の新規 slug で `--plan → check → to-spec → render → gate` を実際に通し、
  旧 `render_short.py` と成果物を並べて目視比較する（この比較は実装後に行う）

## 7. リスクと対策

| リスク | 対策 |
| --- | --- |
| `make_short2.py` の依存（`hn_text.display`, `rich_text`）が多い | 必要な関数だけをこのリポジトリ内へ取り込み、外部プロジェクトへの参照を作らない |
| 尺が音声で決まり、`result.json` の境界とずれる | `--plan` で実測尺を書き戻し、必ず `shorts_standard.py check` を再実行する |
| 描画変更で指紋が変わり承認が失効する | 新規動画のみに適用し、`prepare → sign → render → gate` の順序を守る。既存動画は触らない |
| 寄り道ラボの CTA / 既定クレジットが混入する | `cta:false` と `render.json` のクレジットを強制し、テストで検証する |
| レビュー・公開まで変わってしまう | 今回の変更範囲を描画のみとし、設計書・`PRODUCTION_LOG.md` に明記する |

## 8. 実装の順序（承認後）

1. `scripts/render_yorimichi.py` の骨格と `--plan` を追加（VOICEVOX 音声と尺書き戻し）
2. 描画関数（Ken Burns / テロップ / 字幕 / PR / 種別 / 出典）を追加
3. mux・SRT・説明欄・固定コメント・サムネイルを追加
4. `tests/test_render_yorimichi.py` を追加
5. `README.md` / `docs/RENDER_PIPELINE.md` / `docs/PRODUCTION_LOG.md` を更新
6. 新規 slug で1本だけ実行し、旧方式と比較してから標準にする

## 9. 決定済みの境界

- レビューは Muse のまま（Google AI モードへの変更は別案件）
- 公開は CDP Studio アップロードのまま
- `ffmpeg-skill` は使わない
- 既存の承認済み動画・証跡は変更しない
