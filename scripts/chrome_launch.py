"""Chrome を**最小化**して起動する（チャンネル用 / レビュー用）。

usage:
  python scripts/chrome_launch.py channel   # 9222 / .chrome-gemienox / Profile 3 （YouTube Studio・楽天）
  python scripts/chrome_launch.py review    # 9223 / .chrome-automation      （ChatGPT・Gemini・Muse）

- すでにそのポートが開いていれば何もしない（二重起動しない）。
- 起動は最小化。ウィンドウを前に出したくないときも、CDP 経由の操作はそのまま動く。
- 起動待ちは「CDP のポートが開いたか」で判定する（唯一の確実な合図）。
"""
import argparse
import ntpath
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

PROFILES = {
    'channel': {
        'port': 9222,
        'user_data_dir': r'%USERPROFILE%\.chrome-gemienox',
        'profile_directory': 'Profile 3',
        'url': 'https://studio.youtube.com/',
    },
    'review': {
        'port': 9223,
        'user_data_dir': r'C:\Users\neoen\.chrome-automation',
        'profile_directory': None,
        'url': 'https://muse.ai/',
    },
}


def expand_user_data_dir(value):
    """argv で渡す Windows パスの環境変数を展開する（PowerShell に依存しない）。"""
    expanded = ntpath.expandvars(value)
    if expanded == value and value.startswith('%USERPROFILE%'):
        expanded = str(Path.home()) + value[len('%USERPROFILE%'):]
    return expanded


def port_open(port, timeout=1.0):
    try:
        socket.create_connection(('127.0.0.1', port), timeout).close()
        return True
    except OSError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('profile', choices=sorted(PROFILES))
    ap.add_argument('--url', default=None, help='開くURL（既定はプロファイルごとの画面）')
    ap.add_argument('--wait', type=int, default=60, help='CDPポートが開くまで待つ秒数')
    a = ap.parse_args()

    conf = PROFILES[a.profile]
    port = conf['port']
    if port_open(port):
        print(f'port {port} は既に開いている（起動しない）')
        return 0

    user_data_dir = expand_user_data_dir(conf['user_data_dir'])
    args = [
        CHROME,
        f'--user-data-dir={user_data_dir}',
        f'--remote-debugging-port={port}',
        '--no-first-run',
        '--no-default-browser-check',
    ]
    if conf['profile_directory']:
        args.append(f"--profile-directory={conf['profile_directory']}")
    args.append(a.url or conf['url'])

    # `cmd /c start "" /min` で最小化起動を試みる（PowerShell の Start-Process は引数の解釈で崩れる）
    subprocess.run(['cmd', '/c', 'start', '', '/min', *args], check=True)

    for _ in range(a.wait):
        if port_open(port):
            break
        time.sleep(1)
    else:
        print(f'CDP {port} が開かない。ウィンドウを一度クリックしてから再実行する', file=sys.stderr)
        return 1

    # Chrome は前回のウィンドウ状態（最大化など）を復元するので、起動後に最小化する。
    # セッション復元と競合するため、数回リトライする。
    for _ in range(5):
        time.sleep(2)
        pids = _chrome_pids(user_data_dir)
        _minimize_windows(pids)
    print(f'起動した（最小化・CDP {port}）')
    return 0


def _chrome_pids(user_data_dir):
    """そのプロファイルで動いている chrome.exe の PID を集める。"""
    ps = (
        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
        "Where-Object { $_.CommandLine -like '*" + user_data_dir.replace('*', '') + "*' } | "
        "Select-Object -ExpandProperty ProcessId"
    )
    try:
        out = subprocess.run(['pwsh', '-NoProfile', '-Command', ps],
                             capture_output=True, text=True, timeout=30).stdout
        return {int(x) for x in out.split() if x.strip().isdigit()}
    except Exception:
        return set()


def _minimize_windows(pids):
    """指定 PID のトップレベルウィンドウを最小化する。"""
    if not pids:
        return 0
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    SW_MINIMIZE = 6
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_proc(hwnd, lparam):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids and user32.IsWindowVisible(hwnd):
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, 256)
            if title.value:                       # タイトルのあるウィンドウだけ
                found.append(hwnd)
        return True

    user32.EnumWindows(enum_proc, 0)
    for hwnd in found:
        user32.ShowWindow(hwnd, SW_MINIMIZE)
    return len(found)


if __name__ == '__main__':
    sys.exit(main())
