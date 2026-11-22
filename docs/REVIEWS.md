# レビューの手順と記録

**台本は ChatGPT と Gemini、完成動画は Google AI モード（`https://www.google.com/ai/`）で見る。**
Muse レビューは 2026-11-22 の方針変更で廃止した（旧 `review_muse.md` は履歴として残す）。

## 1. 台本の査読（ChatGPT・Gemini）

```powershell
python scripts/script_review.py <slug>              # 両方に送る
python scripts/script_review.py <slug> --target chatgpt
python scripts/script_review.py <slug> --dry-run    # 依頼文を表示するだけ
```

- レビュー用Chrome（`python scripts/chrome_launch.py review` / 9223 / `.chrome-automation`）で
  ChatGPT / Gemini にログインしておく。**チャンネル操作用のプロファイル（9222）とは分ける。**
- 依頼文は `result.json` と `brief.yaml` から自動で作る。観点は A事実の正確さ／B出典と主張の対応／
  C聞きやすさ／D構成と引き／E抜けている文脈。**書き直し禁止・新事実には出典必須**を明記する。
- 返答は `shorts/<slug>/review_chatgpt.md` と `review_gemini.md` に保存する。
- 出力は**表を使わず箇条書き**に指定する（表だと本文抽出が崩れる）。

## 2. 完成動画のレビュー（Google AI モード）

```powershell
python scripts/google_ai_review.py <slug> [--note "追記"] [--dry-run]
```

- 360p に圧縮した MP4 を AI モードの「ファイルとツールを追加」→「ファイルを追加」で添付し、
  **毎回「新しいスレッド」から**依頼文を送る。返答の生テキストは `out/ai_reply_<slug>.txt`。
- 見てもらう点: 字幕と音声の一致／読み間違い・音割れ・無音／文字の重なり・はみ出し／数字と出典の整合／
  冒頭の引き／図の分かりやすさ／公開可否（公開可／要修正）。
- 2026-11-22 の実動確認では、書き起こし・時刻つきの指摘・出典リンクまで返った。動画の映像と音声を
  実際に解析できるので、台本だけの ChatGPT / Gemini では代われない。
- 判定と採否は人が `shorts/<slug>/review_ai.md` に残す。承認ゲートはこのファイルの「公開可」を見る。
- AI モードは指摘が厳しい（Shorts UI の被りを気にする等）。**指摘はそのまま採用せず、出典と画面で確認する。**

## 3. 記録の置き場

| ファイル | 内容 |
| --- | --- |
| `shorts/<slug>/review_chatgpt.md` | ChatGPT の査読（台本） |
| `shorts/<slug>/review_gemini.md` | Gemini の査読（台本） |
| `shorts/<slug>/review_ai.md` | Google AI モードの判定（完成動画） |
| `shorts/<slug>/review_muse.md` | 旧方式の判定（2026-11-22 以前の履歴のみ） |

## 4. 実際に見つかったこと

| 日付・指摘元 | 内容 | 対応 |
| --- | --- | --- |
| 2026-11-22・Google AI モード (`tv_eco_mode`) | 00:22〜00:30 で出典ラベルと素材側の文字「省エネモード＋電源オフの効果」が重なる | 素材の当該文字を削除して再描画（公開済み動画の修正方針はオーナー判断） |
| 2026-11-18・Gemini (`fridge_habits`) | シーン6「温度を下げると食品が傷みやすい」は**逆**。弱にすると庫内温度は上がる | ナレーション・テロップ・図を修正 |
| 2026-11-18・ChatGPT | 合計4,450円を「4つ実行した節約額」と誤解させない注記が必要 | 「単純な足し算。合計は目安」を図と説明欄に |
| 2026-11-18・ChatGPT | シーン4は冷凍室8回→4回の条件も図に要る | 冷蔵室・冷凍室の両方を図示 |
| 2026-11-18・両方 | 「壁から離す」だけでは比較条件が伝わらない | 2条件の上面図を並べた |
| 2026-11-18・両方 | 「年約」「中から弱」はTTSで誤読しやすい | 「一年でおよそ」「中から弱に変える」に書き換え |
| 2026-11-18・旧 Muse | シーン3の金額が字幕帯に隠れる（18秒） | 全シーンを字幕帯より上に再配置 |

## 5. 運用上の注意

- 指摘は**そのまま採用しない**。出典をこちらで確かめてから反映する。
- AI モードは毎回「新しいスレッド」を使う（旧 Muse は1本の長い会話を使っていた）。
- 送信はボタン操作（`送信`）が確実。Chrome が落ちていたら `python scripts/chrome_launch.py review`
  で起動し直す（`google_ai_review.py` / `script_review.py` は自動で呼ぶ）。
