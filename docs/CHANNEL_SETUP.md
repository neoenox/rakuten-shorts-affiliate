# チャンネルと操作環境

## チャンネル（2026-11-17 開設）

| 項目 | 内容 |
| --- | --- |
| チャンネル名 | 暮らしの判断メモ |
| ハンドル | @kurashi_hantei |
| URL | https://www.youtube.com/@kurashi_hantei |
| チャンネルID | `UCBQ8nx5q0_P9NrtStUkSTEg` |
| Google アカウント | gemienox003@gmail.com |
| 開設日 | 2026-11-17 |

**既存の「寄り道ラボ」（`UCN_do9fcssctmkrNsRWOO9A` / neoenox@gmail.com）とは別アカウント・別チャンネル。**
`scripts/yt_api.py` などが持っている `CHANNEL_ID` は流用できない（誤投稿防止ガードが効いて止まる）。

## 操作環境: 専用Chromeプロファイル + CDP

このブラウザは Google アカウントを4つ同時にログインしているため、`authuser` の取り違えが起きやすい。
そこで **gemienox003 専用のプロファイルを複製し、CDP（デバッグポート）で操作する**。
DSH のブラウザ拡張は使わない（Default プロファイルにしか入っておらず、`--load-extension` は Chrome 157 では無効）。

### 起動

```powershell
# プロファイルを複製（初回のみ。元は Profile 3）
#   %LOCALAPPDATA%\Google\Chrome\User Data\Local State と "Profile 3" を
#   C:\Users\neoen\.chrome-gemienox へコピー

& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --user-data-dir="$env:USERPROFILE\.chrome-gemienox" `
  --profile-directory="Profile 3" `
  --remote-debugging-port=9222 `
  --no-first-run --no-default-browser-check `
  --new-window about:blank
```

### 操作

```powershell
python scripts/cdp_browser.py check   # どのアカウントでログインしているか
python scripts/cdp_browser.py open <url>
python scripts/cdp_browser.py signin <email>   # ログイン画面を開いてメールを入れる
```

Python からは `playwright.sync_api` の `connect_over_cdp('http://127.0.0.1:9222')` でそのまま操作できる。
Studio は `https://studio.youtube.com/` で開く（`authuser` の指定は不要）。

### 注意

- 複製したプロファイルは **Cookie が引き継げない**（Chrome の保護のため）。初回だけ手動でサインインする。
  サインインは `C:\Users\neoen\.chrome-gemienox` に保存されるので、次回以降は不要。
- この Chrome は通常の Chrome とは別プロセス。閉じると CDP 操作も止まる。

### 2026-11-17 チャンネル基本設定（Studio / CDP経由）

- チャンネル説明を設定（252文字）。公的資料・出典表示・AI生成の明記・PR表記の方針を書いた。
- プロフィール画像（`assets/branding/profile.png`・「判」）とバナー（`banner.png` 2048x1152）を生成してアップロード。
  バナーは最初、上がチャンネルヘッダーに隠れたので文字を下げて作り直した。
- 生成スクリプトは `scripts/make_branding.py`。
- 国・キーワード（設定 → チャンネル → 基本情報）は、Studioの設定ダイアログが自動操作で開きにくかったため未設定。急ぎではない。
- 外部リンク（プロフィール）は商品が決まってから追加する。
