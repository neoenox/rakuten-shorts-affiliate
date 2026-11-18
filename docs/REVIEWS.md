# レビューの手順と記録

寄り道ラボと同じやり方に揃えた。**台本はChatGPTとGemini、完成動画はMuseで見る。**

## 1. 台本の査読（ChatGPT・Gemini）

```powershell
python scripts/script_review.py <slug>              # 両方に送る
python scripts/script_review.py <slug> --target chatgpt
python scripts/script_review.py <slug> --dry-run    # 依頼文を表示するだけ
```

- レビュー用Chrome（`--user-data-dir=C:\Users\neoen\.chrome-automation --remote-debugging-port=9223`）で
  ChatGPT / Gemini にログインしておく。**チャンネル操作用のプロファイル（9222）とは分ける。**
- 依頼文は `result.json` と `brief.yaml` から自動で作る。観点は A事実の正確さ／B出典と主張の対応／
  C聞きやすさ／D構成と引き／E抜けている文脈。**書き直し禁止・新事実には出典必須**を明記する。
- 返答は `shorts/<slug>/review_chatgpt.md` と `review_gemini.md` に保存する。
- 出力は**表を使わず箇条書き**に指定する（表だと本文抽出が崩れる）。

## 2. 完成動画のレビュー（Muse）

```powershell
python scripts/muse_review.py <slug> [--note "追記"] [--dry-run]
```

- 360pに圧縮して `muse.ai` の同じ会話に添付し、依頼文を送って返答を `out/muse_reply_<slug>.txt` に保存する。
- 見てもらう点: 字幕と音声の一致／読み間違い・音割れ・無音／文字の重なり・はみ出し／数字と出典の整合／
  冒頭の引き／図の分かりやすさ／公開可否。
- Museは**音声も見られる**（書き起こしを返す）ので、ChatGPTやGeminiでは代われない。

## 3. 記録の置き場

| ファイル | 内容 |
| --- | --- |
| `shorts/<slug>/review_chatgpt.md` | ChatGPTの査読（台本） |
| `shorts/<slug>/review_gemini.md` | Geminiの査読（台本） |
| `shorts/<slug>/review_muse.md` | Museの判定（完成動画） |

## 4. 実際に見つかったこと（2026-11-18・`fridge_habits`）

| 指摘元 | 内容 | 対応 |
| --- | --- | --- |
| Gemini | シーン6「温度を下げると食品が傷みやすい」は**逆**。弱にすると庫内温度は上がる | ナレーション・テロップ・図を修正 |
| ChatGPT | 合計4,450円を「4つ実行した節約額」と誤解させない注記が必要 | 「単純な足し算。合計は目安」を図と説明欄に |
| ChatGPT | シーン4は冷凍室8回→4回の条件も図に要る | 冷蔵室・冷凍室の両方を図示 |
| 両方 | 「壁から離す」だけでは比較条件が伝わらない（上と両側が壁 vs 片側だけ壁） | 2条件の上面図を並べた |
| 両方 | 「年約」「中から弱」はTTSで誤読しやすい | 「一年でおよそ」「中から弱に変える」に書き換え |
| Muse | シーン3の金額が字幕帯に隠れ、上端しか見えない（18秒） | 全シーンを字幕帯 y=1252 より上に再配置し、再レビューで「このまま公開可」 |

## 5. 運用上の注意

- 指摘は**そのまま採用しない**。出典をこちらで確かめてから反映する（寄り道ラボと同じ方針）。
- Museは1本の長い会話を使う。新規チャットを作らない。
- 送信は ChatGPT がボタン、Gemini と Muse は Enter が確実（実測）。
- Chromeが落ちていたら、レビュー用プロファイルを `--remote-debugging-port=9223` で起動し直す。
