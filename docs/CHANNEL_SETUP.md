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

### 2026-11-18 非公開アップロードを完遂（生CDPで自動化）

**結果: 1本目を非公開でアップロード完了。**
- 動画ID: ``VsQqOfVrJk4`` / https://youtube.com/shorts/VsQqOfVrJk4（非公開のため外部からは見えない）
- タイトル・PR説明文・サムネイル・子ども向け=いいえ・**公開設定=非公開** を設定済み。
- Studio の「コンテンツ → ショート」タブに出る（**Shortsは「動画」タブに出ない**ので一覧が空に見える）。

**Playwright が不安定だったため、最終的には生CDPだけで通した**（``scripts/cdp_raw.py`` 方式:
Target.attachToTarget + Runtime.evaluate / DOM.setFileInputFiles / Page.captureScreenshot）。
掴んだ罠と対処:

| 置 | 何が起きたか | 対処 |
| --- | --- | --- |
| Playwright connect_over_cdp | 接続が頻繁にタイムアウト（接続後もフリーズ） | 使わない。生CDPのブラウザWebSocketへ直結 |
| ``#next-button`` の有効判定 | ``aria-disabled`` が文字列 ``"false"`` で返るので ``!attr`` は常に false | ``attr !== 'true'`` と比較する |
| 「子ども向け」のラジオ | 中の葉テキストをクリックしても選択されない | host の ``tp-yt-paper-radio-button`` を ``.click()`` する |
| ページ判定 | 遷移しても前ステップの要素が DOM に残る | ``getBoundingClientRect()`` で「見えているか」で判定 |
| 保存直後 | レンダラーが数十秒〜分単位で無応答になる。失敗トーストも出る | **トーストは古い情報のことがある。成否は編集ページ or ショートタブで確認する** |
| ファイル選択 | Playwright が落ちる環境では不可能 | ``DOM.getDocument(depth:-1, pierce:true)`` で木を辿り ``DOM.setFileInputFiles`` |
| コンテンツ一覧 | 「動画」タブには Shorts が出ない | 「ショート」タブ（``tp-yt-paper-tab``）をクリックしてから読む |

**公開の手順（人間が判断する）**: Studio → コンテンツ → ショート → 当該動画 → 公開設定を「公開」へ。
その前に、動画・サムネ・説明欄を目視確認し、固定コメント（``out/draft/*_fixed_comment.md``）の投稿を忘れないこと。

### 2026-11-17 夜: 非公開アップロードの自動化を試した（未完了）

- Studio の アップロード → 詳細 → 動画の要素 → チェック までは自動で通った。
  タイトル・説明・サムネイル・子ども向け=いいえ まで入力し、著作権チェックも「問題は検出されませんでした」。
- ただし最後の「保存」に到達する前に、**分離Chrome（.chrome-gemienox）が落ちる**現象が繰り返した。
  CDP の接続も同時に切れるため、保存だけが残る。
- 原因は未特定。アップロード中にプロセスが終了している（メモリ不足か、ウィンドウを閉じた可能性）。
  対策案: アップロード中は他の重い処理（FreeVideo/ComfyUI）を止める、Chrome を前面に保つ、
  もしくは YouTube Data API の resumable upload に切り替える（OAuth クライアントの用意が必要）。

現状: チャンネルに動画は0本（コンテンツ一覧が空）。下書きのMP4は out/draft/ に残っている。
