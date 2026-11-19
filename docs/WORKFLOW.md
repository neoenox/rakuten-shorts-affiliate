# 制作・公開のワークフロー（2026-11-19 決定）

`AGENTS.md` は「破ってはいけない契約」、この文書は「手順の詳細」。
食い違ったときは `AGENTS.md` を優先する。

## 1. 状態の意味

| 場所 | 値 | 意味 |
| --- | --- | --- |
| `result.json` `status` | `needs_review` | 台本が未承認（未照合・照合中・承認失効を含む） |
| | `ready` | 原文照合済み・オーナー承認済み・期限内 |
| `verification.json` `status` | `pending` | 照合の準備だけ済み（承認前） |
| | `approved` | オーナー承認済み（`result.json` も `ready`） |
| | `revoked` | 承認を取り消した |
| `publish.json` `visibility` | `public` / `unlisted` / `private` | 公開の事実（YouTube 側の状態） |
| | `unpublished` | まだ上げていない在庫 |
| | `held` | 意図的に保留（例：重複のため） |

- **公開の事実は `publish.json` が持つ。** `result.json` の `status` は「台本の検証状態」だけを表す。
- 公開済みでも `status: needs_review` はあり得る（レビュー体制より前に公開した動画）。それは「承認を捏造しない」という意味で正しい。

## 2. 公開までの順序

```
brief.yaml（事実と出典）
  → result.json
  → clips.json（情景のシーンのプロンプト）→ gen_freevideo.py <slug>   # FreeVideo でシーンごとのクリップ
  → render_short.py <slug> --plan        # 実測尺を result.json に書き戻す
  → shorts_standard.py check             # ERROR 0
  → approve.py prepare <slug>            # 照合・証跡の作成（下記10項目）
  → オーナーが承認
  → approve.py sign <slug> --by owner    # verification.json を approved にし status=ready
  → render_short.py <slug>               # out/ へ再描画
  → gate.py <slug>                       # ハッシュ・期限・指紋・表記・リンクを検査
  → upload_short.py <slug> [--publish]
```

- 情景のシーンは **FreeVideo のクリップ**で作る（2026-11-19 決定）。図解・模式図は PIL。
  クリップ生成は `--plan` より前に済ませる（尺が確定してから、クリップの長さを合わせるため）。
  詳しくは [`RENDER_PIPELINE.md`](RENDER_PIPELINE.md) の「動画背景」。

**承認は `--plan` の後**に取る。`--plan` は `result.json` を書き換えるため、先に承認するとハッシュが即座に無効になる。

### 承認の失効

次のどれかで承認は無効になる。`gate.py` と `upload_short.py` が拒否する。

1. `result.json` の SHA-256 が `verification.json` の `result_sha256` と一致しない（台本を書き換えた）
2. `expires_at`（承認日 + 14日）を過ぎた
3. `verification.json` の `status` が `approved` でない

## 3. 照合の合格ライン（10項目）

`approve.py prepare` が機械で確認できる項目を埋め、人が判断する項目は明示フラグで記録する。

| # | 項目 | 確認方法 |
| --- | --- | --- |
| 1 | 出典の実在 | 全 `claims` の `source_url` を取得し、HTTP 200 と本文を確認 |
| 2 | 数値の一致 | `claim.statement` の数値トークンが原文に存在するか |
| 3 | 条件の一致 | 機種・地域・単価（31円/kWh）・使用時間が原文と一致（人が確認） |
| 4 | 断定・煽りの排除 | 最上級・保証・効能効果の表現がない（機械の候補抽出＋人が確認） |
| 5 | 商品の一致 | `product_name` と商品ページの名称・型番が対応（人が確認） |
| 6 | リンクの生存 | 301 → `item.rakuten.co.jp`、`scid=af_pc_etc` 付き |
| 7 | 表記 | 全編PR、AI／イラスト／模式図ラベル、説明欄冒頭PR、固定コメントPR |
| 8 | レビュー | `review_muse.md` が draft MP4 より新しく、「公開可」がある |
| 9 | 形式 | `shorts_standard.py check` が ERROR 0 |
| 10 | 残件 | `needs_research` が空。留保は `limitations` に記録 |

追加で、**フレーム3点（冒頭・中盤・最終）の目視**を行う（ラベルの可読性・文字はみ出し）。

## 4. `verification.json`（承認の証跡）

```json
{
  "slug": "kettle_heat",
  "status": "approved",
  "checked_at": "2026-11-19T10:00:00+09:00",
  "approved_at": "2026-11-19T10:05:00+09:00",
  "approved_by": "owner",
  "expires_at": "2026-12-03",
  "result_sha256": "…",
  "review": {"file": "review_muse.md", "mtime": "…", "verdict": "このまま公開可"},
  "artifacts": {"file": "out/draft/<slug>_DRAFT.mp4", "video_framemd5_sha256": "…", "audio_md5": "…"},
  "checks": {"sources": [ … ], "product": { … }, "link": { … }, "presentation": { … },
             "format": { … }, "frames": { … }},
  "failures": [],
  "resolved_needs": [{"item": "…", "resolution": "…"}],
  "limitations": ["…"]
}
```

- `artifacts` は **Muse が見た draft** の指紋。再描画後の `out/` と一致しなければ公開を止める（メタデータ差を無視するため、映像は framemd5 レポートの SHA-256、音声は md5）。
- `prepare` は公開週ごとに実行し直す（出典は変わり得るため）。承認だけを先にまとめて取らない。
- 人が判断した項目は `checks` に `manual: true` と確認内容を残す。

## 5. `publish.json`（公開の事実）

```json
{
  "slug": "kettle_heat",
  "visibility": "unpublished",
  "video_id": null,
  "published_at": null,
  "title": "電気ポットの保温、年3,330円",
  "product": {"name": "MAXZEN 電気ケトル 1.0L（保温なし・空だき防止）"},
  "affiliate_url": "https://hb.afl.rakuten.co.jp/…",
  "legacy_open_items": [],
  "legacy_check": null,
  "notes": ""
}
```

- 公開済みの動画は `video_id` / `published_at` / `visibility` を埋める。
- レビュー体制より前に公開した動画は、`legacy_open_items` に「公開時点の未確認」を残す（`verification.json` は作らない）。
- `legacy_check` は遡及チェックの結果（`checked_at` / `results` / `status`）。

## 6. 残件と留保の書き分け

| フィールド | 意味 | 例 |
| --- | --- | --- |
| `needs_research` | **これからやる作業**。空でないと `ready` にできない | 「商品を選定してリンクを作る」 |
| `resolved_needs`（verification） | 作業の完了記録（何をして閉じたか） | 「リンク作成 → 301とscidを確認」 |
| `limitations`（verification） | 調べても埋まらない留保。受容して公開する | 「未確認のため6倍という表現は使わない」 |

`limitations` のうち視聴者に影響するものは `render.json` の `description_note` にも書く。

## 7. 公開ペースと順序

- 週1本。承認から公開までを短く保つため、**公開週に1本ずつ**検証→承認する。
- 順序は季節性で決める。2026-11-19 時点：`kettle_heat` → `led_light` → `fridge_habits` → `iphone_battery`。
- `winter_three` は `ac_heater_saving` と同一出典・同一数値のため **保留**（`visibility: held`）。

## 8. 公開後の訂正

| 程度 | 例 | 対応 |
| --- | --- | --- |
| 軽微 | 表記・言い回し・注記漏れ | 説明欄を訂正し、固定コメントで告知。動画は残す |
| 重大 | 金額・数値・比較条件の誤り／因果の逆／商品の取り違え／薬機法・景表法・規約違反／出典なし | 非公開化して新IDで出し直す。旧IDは非公開で残す（削除しない） |

## 9. 状態表の生成

`python scripts/status.py` が `docs/STATUS.md` を生成する。手で編集しない。
`README.md` の「現在の状態」は `docs/STATUS.md` を参照する。
