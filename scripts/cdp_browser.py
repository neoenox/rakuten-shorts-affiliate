"""CDP で起動済みの Chrome を操作する小さな入口（Playwright）。

前提: Chrome を次のように起動しておくこと。
  chrome.exe --remote-debugging-port=9222 --user-data-dir=%USERPROFILE%\\.chrome-gemienox --profile-directory="Profile 3"

usage:
  python scripts/cdp_browser.py check
       YouTube にどのアカウントでログインしているかを表示する
  python scripts/cdp_browser.py open <url>
      新しいタブで開く
"""
import sys

from playwright.sync_api import sync_playwright

CDP = 'http://127.0.0.1:9222'


def connect():
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    return p, browser, ctx


def new_page(ctx):
    page = ctx.new_page()
    page.set_default_timeout(30000)
    return page


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    p, browser, ctx = connect()
    try:
        if cmd == 'check':
            page = new_page(ctx)
            page.goto('https://www.youtube.com/account', wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            text = page.inner_text('body')
            for line in text.splitlines():
                if 'ログインしています' in line or 'チャンネル' in line and '作成' in line:
                    print(line.strip())
            print('URL:', page.url)
        elif cmd == 'open':
            page = new_page(ctx)
            page.goto(sys.argv[2], wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            print('title:', page.title())
        elif cmd == 'signin':
            # Google のログイン画面を開き、メールだけ入れて前面に出す（パスワードは本人が入力する）
            email = sys.argv[2] if len(sys.argv) > 2 else ''
            page = new_page(ctx)
            page.goto('https://accounts.google.com/signin/v2/identifier?hl=ja&flowName=GlifWebSignIn&flowEntry=ServiceLogin',
                      wait_until='domcontentloaded')
            page.wait_for_timeout(2500)
            if email:
                try:
                    page.fill('input[type="email"]', email)
                    print('メールを入力しました:', email)
                except Exception as e:
                    print('メール入力は手動でお願いします:', e)
            page.bring_to_front()
            print('ウィンドウを前面に出しました。パスワードを入力してログインしてください。')
            print('URL:', page.url)
    finally:
        p.stop()


if __name__ == '__main__':
    main()
