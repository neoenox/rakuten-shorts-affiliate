# 状態（生成物）

このファイルは `python scripts/status.py` が生成します。**手で編集しない。**
正は `shorts/<slug>/result.json` / `verification.json` / `publish.json`。

| slug | タイトル | 台本 | 承認 | 公開 | 残件 | 留保 | 次 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ac_heater_saving` | 暖房を1℃下げても、年490円 | needs_review | 未承認 | 公開（yFXNYLgMzmY） | 0 | 0 | —（公開済み） |
| `fridge_habits` | 冷蔵庫の4つのクセ、直すと年4,450円 | ready | 承認済み（〜2026-12-03） | 公開（1m-6W8Hnfms） | 0（解決 1） | 0 | —（公開済み） |
| `furniture_anchor` | 家具の転倒防止、突っ張り棒だけで大丈夫？ | ready | 承認済み（〜2026-12-03） | 公開（T-ERvf5yy2s） | 0 | 3 | —（公開済み） |
| `hot_carpet` | 電気カーペット、強のままで年5,770円 | needs_review | 未承認 | 公開（zVQ7UoER4xM） | 0 | 0 | —（公開済み） |
| `iphone_battery` | iPhoneのバッテリー、充電500回でどうなる？ | ready | 承認済み（〜2026-12-03） | 公開（UKNQdUxTi7A） | 0（解決 1） | 0 | —（公開済み） |
| `kaito_plate` | レンジの解凍がうまくいかない理由 | needs_review | 未承認 | 公開（aVawDx0PiVg） | 0 | 2 | —（公開済み） |
| `kettle_heat` | 電気ポットの保温、年3,330円 | ready | 承認済み（〜2026-12-02） | 公開（KeUn5IsdLeU） | 0（解決 2） | 4 | —（公開済み） |
| `led_light` | 白熱電球のまま、年2,880円の差 | ready | 承認済み（〜2026-12-03） | 公開（uWOcg8G6BXM） | 0（解決 2） | 0 | —（公開済み） |
| `peak_hours` | 節電すべき時間は昼？夕方？答えは二つのピーク | ready | 承認済み（〜2026-12-03） | 公開（RJb8jLt37fE） | 0 | 0 | —（公開済み） |
| `wifi_band` | Wi-Fiが遅いとき、まず見るべきは2.4GHzか5GHz | ready | 承認済み（〜2026-12-03） | 公開（eEUDSP4bKfs） | 0 | 3 | —（公開済み） |
| `winter_three` | 冬の暖房、3つの行動で年2,770円 | needs_review | 未承認 | 保留 | 0 | 0 | 改稿して再開 |

公開 10本 / 保留 1本 / 未公開 0本（全11本）

## 見方

- **台本**: `result.json` の `status`（`ready` は承認済み・期限内のときだけ）
- **承認**: `verification.json` の状態。`失効（台本変更）` は `result.json` が承認後に変わった
- **公開**: `publish.json` の `visibility`。公開済みでも旧フローなら台本は `needs_review` のまま
- **残件**: `needs_research` の件数（0 でないと `ready` にできない）
- **留保**: `limitations` と `legacy_open_items`（open/accepted）の件数
