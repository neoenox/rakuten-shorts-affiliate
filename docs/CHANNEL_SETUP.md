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

# 起動はこれを使う（最小化で開く・既に開いていれば何もしない）
python scripts/chrome_launch.py channel
```

- **Chrome は最小化で起動する**（2026-11-19 オーナー指示）。`chrome_launch.py` は
  `cmd /c start "" /min` で起動したあと、セッション復元で最大化に戻るのを数回リトライして最小化する。
- `upload_short.py` と `muse_review.py` は、ポートが閉じていれば自分でこのランチャーを呼ぶ。
- 手で起動する場合（トラブル時のみ）:

```powershell
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

---

## 2026-11-18 楽天アフィリエイトにチャンネルをサイト登録

- 楽天アフィリエイトにログインし、「サイト情報の登録」から下記を登録した。

| 項目 | 内容 |
| --- | --- |
| 順位 | 2位（既存の「くらべるお」が1位） |
| 運営サイト名 | 暮らしの判断メモ |
| 運営サイトURL | https://www.youtube.com/@kurashi_hantei |
| 運営サイトのジャンル | 住まい・インテリア・雑貨 |

- 登録画面: https://affiliate.rakuten.co.jp/user/sites/create
  - 項目は 運営サイト名（必須）/ 運営サイトURL（必須）/ 順位（上位5位まで必須）/ ジャンル（任意）。
  - ジャンル候補は45件（日記系・趣味系が中心）。YouTube向けの専用区分は無い。
- 次: 商品ページを開いて「リンク作成」→ できた `hb.afl.rakuten.co.jp` のURLを
  `shorts/<slug>/render.json` の `affiliate` に入れて再生成する。

---

## 2026-11-18 アップロードツールを整備（`scripts/upload_short.py`）

- Studio操作を1コマンドにまとめた。`python scripts/upload_short.py <slug> [--publish]`。
- 実装上の要点:
  - 各ボタンは **見えて有効になるまで待ってから実マウス相当（Input.dispatchMouseEvent）で押す**。
    JSの `.click()` では Polymer の状態が更新されず、保存ボタンが disabled のまま残る。
  - **1日のアップロード上限**（「1 日のアップロード数の上限に達しました」）を検出したら exit 2 で中止。
  - 実測: `upload_short.py iphone_battery` → 上限を検出して exit 2 で停止することを確認済み。
- 途中で定数名とクラス名が衝突するバグ（`CDP`）を踏んだので `CDP_URL` に改名した。

### 固定コメントのピン留め（手動）

- 自動操作では安定しなかった（メニューの「固定」を実クリックしても、ページ上に固定表示が出ない）。
- **手順**: 動画ページ → コメントの「⋯」→「固定」。1クリックなので、必要時に手で行う。

---

## 2026-11-18 楽天アフィリエイト復帰 → リンクを4本分整備

- 一時的に描画されなくなっていた楽天アフィリエイトが復帰（セッションは生きていた）。
- **3本目（公開済み・`zVQ7UoER4xM`）にリンクを追加**。Studioの説明欄を差し替え、外部から
  `hb.afl.rakuten.co.jp` と商品名（TEKNOS）が載っていることを確認した。

| 動画 | 商品 | 価格 | リンク |
| --- | --- | --- | --- |
| `zVQ7UoER4xM`（公開） | ホットカーペット TEKNOS | 3,980円〜 | 設定済み・反映済み |
| `iphone_battery`（待ち） | Anker Zolo Power Bank 20000mAh | 3,980円 | 設定済み（アップ時に反映） |
| `winter_three`（待ち） | エアコン洗浄セット 12点 | 5,980円 | 設定済み（同上） |
| `fridge_habits`（待ち） | シンワ 冷蔵庫用温度計 A | 3,980円 | 設定済み（同上） |

### リンク作成の手順で分かったこと

- `https://affiliate.rakuten.co.jp/freelink?u=<商品URL>` を開くと `/link/pc/item?...` に遷移する。
- **URLは `#codebox` の value に入る**（innerHTML には出ない）。既定は「画像とテキスト」のHTML形式で、
  `?pc=` が2つ（商品とサムネイル）含まれるため、**最初の `?pc=` だけを取り出す**必要がある。
- これを自動化した `scripts/affiliate_link.py` を追加（商品URLを渡すと hb.afl のテキストリンクを返す）。
- 作成したリンクは HTTP で 301 を追跡し、`scid=af_pc_etc` が付いて商品ページに着地することを毎回確認している。
