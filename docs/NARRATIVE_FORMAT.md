# 人物中心のストーリー形式（試作・提案）

**状態: 試作。** `shorts-standard/` のルールは変えない。次回1本で「従来の図解中心」との比較用に試す。

## 1. 狙いと限界

- 現状の動画は図解とテロップが主役で、誰の話かが見えない。1人の人物が
  「違和感 → 原因に気づく → 試す → 根拠を知る → 落ち着く」を辿れば、
  視聴者が自分に置き換えられる「引き」になる（狙いであって効果の保証ではない）。
- **主人公の変化はイメージであって根拠ではない。** 節約額・割合・条件は
  すべて一次資料の試算として出し、架空の人物の成功体験として語らない。
- **解決手段は行動にする。** 設定を変える／確認する、といった行動で終わる。
  商品は「名前・価格・理由」のテロップと説明欄・hubに置き、主人公が商品を買う・
  持つ・使う描写は入れない（`AGENTS.md` §1〜3）。

## 2. 主人公の固定仕様

| 項目 | 固定値 |
| --- | --- |
| 人物 | 成人。性別・年齢は特定しない |
| 髪・服装 | 短い黒髪／からし色のカーディガン＋白シャツ／濃い青のズボン |
| 顔 | 目と口だけの記号。実在人物・ブランド・ロゴなし |
| アンカー | 同じ部屋（窓・ランプ・マグカップ）を全シーンで使い、場所の連続性出す |
| ポーズ | `notice` / `think` / `check` / `act` / `relieved` の5種 |

- 実装: `scripts/story_person.py` の `draw_person(draw, x, y, s, pose)`。
  4ポーズの見本は `docs/assets/story_person_sample.png`（生成コマンド:
  `python scripts/story_person.py --demo`）。
- 人物はテロップ帯の左寄りに置き、タイトル・大テロップ・出典・字幕は
  描画側が上に重ねる。重なりは公開前のフレーム3点目視で確認する。

## 3. 6シーン構成（30〜45秒／5〜7シーンの範囲）

| # | 目安 | 物語の役割 | 画面 | 語る内容 | 種別ラベル |
| --- | --- | --- | --- | --- | --- |
| 1 | 0〜5秒 | 違和感 | 主人公が部屋／明細を見つめる（`notice`） | 問題提起「なぜ今のままだと…？」 | イラスト |
| 2 | 5〜11秒 | 原因に気づく | 同じ部屋＋模式図（`think`） | 結論の方向性「原因はこれ」 | 模式図 |
| 3 | 11〜18秒 | 試す | 主人公が設定を触る（`act`） | 具体的な行動 | 模式図 |
| 4 | 18〜26秒 | 根拠 | 数字カード＋主人公（`check`） | 一次資料の数値と比較条件 | 模式図 |
| 5 | 26〜33秒 | もう一歩 | 別の行動／確認（`check` または `act`） | 条件・注意点 | 模式図 |
| 6 | 33〜40秒 | 結論回収 | 同じ部屋で落ち着く（`relieved`） | 結論の言い直し＋「商品名は説明欄に」 | イラスト |

- 疑問 → 結論の方向性 → 理由・根拠 → 結論回収、という標準の構成は維持する。
  物語はその上に被せる語り方であって、構成の置き換えではない。
- シーン数・尺は `shorts_standard.py check` と `render_yorimichi.py --plan` の実測に従う。

## 4. FreeVideo を使う場合

1シーン1クリップ（`clips.json`）のプロンプト先頭に、人物の固定記述を毎回そのまま入れる。

```
The same adult character in every clip: short dark hair, mustard-yellow cardigan over a white shirt, dark blue trousers, no brand, no logo, minimal facial features. The same small Japanese room with one window and one warm lamp. Scene: <そのシーンの行動>. Slow camera push-in, cinematic, soft light. No text, no letters, no labels, no logos, no product packaging, no real product replica, no other people.
```

- seed は `clips.json` に保存して全クリップで固定する（`gen_freevideo.py` が自動保存する）。
- 別生成のクリップ間で同一人物が保てるかは**未検証**。8188が停止している間は
  `AGENTS.md` §2 の静止フォールバックを使い、`PRODUCTION_LOG.md` に理由を残す。
- 表記は素材に合わせる: 自作イラストなら `art_types: "illustration"` → 画面は「イラスト」、
  AI生成クリップなら `"ai"` → 「イメージ（AI生成）」。両方とも全編でフェードさせない。

## 5. やらないこと

- 「この人が年○円節約した」のような、架空の体験を根拠にする語り。
- 数値の条件（地域・機種・単価・時間）を省いたまま主人公の変化だけを見せること。
- 商品画像・レビュー本文・効能効果・実在商品の再現。「クリックして」「お願いします」。
- PR・種別ラベル・出典の省略（`AGENTS.md` §2）。

## 6. 組み込み手順と検証

1. `brief.yaml` / `result.json` のスキーマは変更しない。`visual` に人物の行動を書く。
2. `render.json` の `art_types` / `clips` で情景（人物）と模式図を選ぶ。
3. `--plan → shorts_standard.py check → approve.py prepare/sign → to-spec →
   render_yorimichi.py → gate.py → フレーム3点目視 → Google AI モードレビュー` は従来どおり。
4. 比較変数は「人物中心かどうか」だけ。尺・BGM・CTA・タイトル型は
   `docs/STRATEGY.md` §3-B に従って固定する。

### 実施済みの検証（2026-11-22）

- `python scripts/story_person.py --demo` で1080x1920の見本を生成し目視。
  4ポーズで輪郭・配色・髪型が一致していることを確認。
- **試作動画を作成**: 公開済み `tv_eco_mode` の台本・音声（ナレーション＋BGM）を流用し、
  人物を中央の安全帯に置いた6シーンを再描画。
  成果物は `out/prototype/story_proto_tv.mp4`（1080x1920 / 30fps / 37.37秒 / H.264＋AAC、
  2.6MB）。`cache/story_proto_tv/build_prototype.py` が生成スクリプト（再現用・Git管理外）。
- 代表フレーム4点（1.5 / 12 / 24 / 35秒）を目視: PR・「イラスト」ラベル・タイトル・
  大テロップ・出典・字幕がすべて可読。人物は毎シーン同じ服装・髪型で、
  表情とポーズだけが変わる。見本は `docs/assets/story_proto_tv_frame.jpg`。
- VOICEVOX stopped のため音声は公開版から抽出して流用。したがって**新しいナレーションの
  実測・承認・公開ゲートは未実施**。この試作は比較用の下書きであり公開しない。
- FreeVideoでの同一人物再現は未検証（静止イラストで代替）。

## 参照

- `docs/STRATEGY.md`（週1本の比較計画）
- `docs/WORKFLOW.md` / `docs/RENDER_PIPELINE.md`
- `docs/assets/story_person_sample.png`
