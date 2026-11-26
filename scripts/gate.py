"""公開前ゲート（承認・成果物・表記・リンク・指紋の検査を一元化する）。

usage:
  python scripts/gate.py <slug> [--no-network] [--no-fingerprint] [--json]

判定:
  - result.json の status が ready
  - needs_research が空
  - verification.json が approved / 期限内 / result.json の SHA-256 が一致
  - out/<slug>.mp4 などが存在
  - 説明欄・固定コメントの先頭が【PR】で、タイトル・商品名・リンク・種別表記がある
  - アフィリエイトリンクが item.rakuten.co.jp に着地し scid が付く（--no-network で省略）
  - 再描画した動画のストリーム指紋が、承認時に記録した draft の指紋と一致

このモジュールは upload_short.py と approve.py から import される。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests
from safe_http import safe_get

ROOT = Path(__file__).resolve().parents[1]
PR_MARKER = '【PR】'
LINK_HOST = 'hb.afl.rakuten.co.jp'
ITEM_HOST = 'item.rakuten.co.jp'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'


# ---------------------------------------------------------------- 基本ユーティリティ

def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def today():
    return date.today()


def is_expired(expires_at, on=None):
    """expires_at（YYYY-MM-DD）が過ぎていたら True。当日は有効。"""
    if not expires_at:
        return True
    try:
        d = date.fromisoformat(str(expires_at)[:10])
    except ValueError:
        return True
    return (on or today()) > d


def ffmpeg_bin():
    cands = [os.environ.get('FFMPEG'), shutil.which('ffmpeg'),
             r'E:\rekishikaisetu-honnoji\tools\ffmpeg\bin\ffmpeg.exe']
    for c in cands:
        if c and Path(c).exists():
            return str(c)
    raise RuntimeError('ffmpeg が見つからない。PATH か環境変数 FFMPEG で指定する')


def stream_fingerprints(path):
    """映像の framemd5 レポートの SHA-256 と、音声の MD5 を返す。

    MP4 全体のハッシュは creation_time などのメタデータで変わるため使わない。
    """
    ff = ffmpeg_bin()
    v = subprocess.run([ff, '-v', 'error', '-i', str(path), '-map', '0:v:0',
                        '-f', 'framemd5', '-'], capture_output=True)
    if v.returncode:
        raise RuntimeError('映像の指紋を計算できません: %s' % v.stderr.decode('utf-8', 'replace')[:200])
    lines = [l for l in v.stdout.decode('utf-8', 'replace').splitlines() if not l.startswith('#')]
    video = hashlib.sha256('\n'.join(lines).encode('utf-8')).hexdigest()

    a = subprocess.run([ff, '-v', 'error', '-i', str(path), '-map', '0:a:0',
                        '-f', 'md5', '-'], capture_output=True)
    if a.returncode:
        raise RuntimeError('音声の指紋を計算できません: %s' % a.stderr.decode('utf-8', 'replace')[:200])
    m = re.search(rb'MD5=([0-9a-f]{32})', a.stdout)
    audio = m.group(1).decode('ascii') if m else None
    return {'video_framemd5_sha256': video, 'audio_md5': audio}


# ---------------------------------------------------------------- リンク・商品ページ

def check_link_url(url):
    """ネットワーク不要の形式検査。"""
    try:
        parsed = urlparse(str(url))
    except ValueError:
        return 'アフィリエイトリンクが URL ではありません'
    if parsed.scheme not in ('http', 'https'):
        return 'アフィリエイトリンクが http(s) URL ではありません'
    if parsed.hostname != LINK_HOST:
        return 'アフィリエイトリンクが %s ではありません' % LINK_HOST
    return None


def resolve_affiliate_link(url, timeout=20):
    """hb.afl → 商品ページ（301）を追い、最終URLを返す。"""
    bad = check_link_url(url)
    if bad:
        raise ValueError(bad)
    response = safe_get(url, headers={'User-Agent': UA}, timeout=timeout, max_bytes=1_000_000)
    final = response.url
    status = response.status_code
    if status < 200 or status >= 300:
        raise ValueError('アフィリエイトリンクの最終応答が失敗: HTTP %s' % status)
    parsed = urlparse(final)
    if parsed.hostname != ITEM_HOST:
        raise ValueError('アフィリエイトリンクの最終URLが商品ページではありません: %s' % final)
    if 'scid=af_pc_etc' not in final:
        raise ValueError('アフィリエイト計測用の scid=af_pc_etc が最終URLにありません')
    return final


def fetch_item_page(url, timeout=25):
    """商品ページのタイトルと価格を取得する（監査用。判定は人が行う）。"""
    r = safe_get(url, headers={'User-Agent': UA}, timeout=timeout, max_bytes=2_000_000)
    if urlparse(r.url).hostname != ITEM_HOST:
        raise ValueError('商品ページの最終URLが商品ページではありません')
    title = None
    m = re.search(r'<title>(.*?)</title>', r.text, re.S)
    if m:
        title = re.sub(r'\s+', ' ', m.group(1)).strip()
    price = None
    m = re.search(r'itemprop="price"[^>]*content="([\d,]+)"', r.text)
    if m:
        price = int(m.group(1).replace(',', ''))
    return {'http_status': r.status_code, 'title': title, 'price': price}


# ---------------------------------------------------------------- 表記

def check_presentation(desc, comment, title, product_name, affiliate_url):
    """説明欄・固定コメントの必須表記を検査する。"""
    failures = []
    if not desc.startswith(PR_MARKER):
        failures.append('説明欄の先頭に【PR】がありません')
    if not comment.startswith(PR_MARKER):
        failures.append('固定コメントの先頭に【PR】がありません')
    for label, text in (('説明欄', desc), ('固定コメント', comment)):
        if title and title not in text:
            failures.append('%sに動画タイトルがありません' % label)
        if product_name and product_name not in text:
            failures.append('%sに商品名「%s」がありません' % (label, product_name))
        if affiliate_url and affiliate_url not in text:
            failures.append('%sにアフィリエイトリンクがありません' % label)
        if 'AI生成' not in text:
            failures.append('%sに「AI生成」の表記がありません' % label)
        if not ('模式図' in text or 'イラスト' in text):
            failures.append('%sに「模式図」または「イラスト」の表記がありません' % label)
        if 'クリックして' in text or 'クリックをお願い' in text:
            failures.append('%sにクリック依頼の表現があります' % label)
    return failures


# ---------------------------------------------------------------- 検証・承認

def check_verification(ver, result_path, on=None):
    failures = []
    if not ver:
        return ['verification.json がありません（approve.py prepare → sign が必要）']
    if ver.get('status') != 'approved':
        failures.append('verification.json の status が approved ではありません: %s' % ver.get('status'))
    if not str(ver.get('approved_by') or '').strip():
        failures.append('verification.json に approved_by がありません')
    if is_expired(ver.get('expires_at'), on):
        failures.append('承認の有効期限が切れています: %s' % ver.get('expires_at'))
    if ver.get('result_sha256') != sha256_file(result_path):
        failures.append('承認後に result.json が変更されています（SHA-256 不一致）')
    if ver.get('failures'):
        failures.append('verification.json に未解消の failures が残っています')
    return failures


# ---------------------------------------------------------------- 本体

def evaluate(slug, root=None, network=True, fingerprints=True, run_format=True):
    root = Path(root) if root else ROOT
    sd = root / 'shorts' / slug
    result_path = sd / 'result.json'
    render_path = sd / 'render.json'
    ver_path = sd / 'verification.json'
    out = root / 'out'

    failures = []
    warnings = []
    info = {'slug': slug, 'passed': False, 'failures': failures, 'warnings': warnings}

    for path, label in ((result_path, '台本'), (render_path, '描画設定')):
        if not path.is_file() or path.stat().st_size == 0:
            failures.append('%sが見つかりません: %s' % (label, path))
    if failures:
        return info

    data = load_json(result_path)
    conf = load_json(render_path)
    title = str(data.get('title') or '').strip()
    product_name = str(conf.get('product_name') or '').strip()
    affiliate_url = str((conf.get('affiliate') or {}).get('url') or '').strip()

    info.update({
        'title': title,
        'product_name': product_name,
        'affiliate_url': affiliate_url,
        'status': data.get('status'),
        'needs_research': data.get('needs_research') or [],
    })

    if data.get('status') != 'ready':
        failures.append("公開不可: status=%r。原文照合を終え、承認を得て ready にしてください"
                        % data.get('status'))
    if info['needs_research']:
        failures.append('needs_research が残っています: ' + ' / '.join(info['needs_research']))
    if not product_name:
        failures.append('render.json に product_name がありません')
    if not affiliate_url:
        failures.append('render.json に affiliate.url がありません')

    ver = load_json(ver_path) if ver_path.is_file() else None
    failures.extend(check_verification(ver, result_path))

    video = out / ('%s.mp4' % slug)
    thumb = out / ('%s_thumb.jpg' % slug)
    desc_path = out / ('%s_description.md' % slug)
    comment_path = out / ('%s_fixed_comment.md' % slug)
    for path, label in ((video, '動画'), (thumb, 'サムネイル'),
                        (desc_path, '説明欄'), (comment_path, '固定コメント')):
        if not path.is_file() or path.stat().st_size == 0:
            failures.append('%sが見つかりません: %s' % (label, path))
    info.update({'video': video, 'thumb': thumb, 'desc': desc_path, 'comment': comment_path})

    if desc_path.is_file() and comment_path.is_file():
        desc = desc_path.read_text(encoding='utf-8')
        comment = comment_path.read_text(encoding='utf-8')
        info['description'] = desc
        info['comment'] = comment
        failures.extend(check_presentation(desc, comment, title, product_name, affiliate_url))

    if network and affiliate_url:
        try:
            info['final_url'] = resolve_affiliate_link(affiliate_url)
        except (ValueError, requests.RequestException) as exc:
            failures.append('アフィリエイトリンクを確認できません: %s' % exc)
    else:
        bad = check_link_url(affiliate_url) if affiliate_url else 'リンクが空'
        if bad:
            failures.append(bad)

    if fingerprints and ver and video.is_file():
        want = ver.get('artifacts') or {}
        if want.get('video_framemd5_sha256') or want.get('audio_md5'):
            try:
                got = stream_fingerprints(video)
            except RuntimeError as exc:
                failures.append(str(exc))
            else:
                if want.get('video_framemd5_sha256') and got['video_framemd5_sha256'] != want['video_framemd5_sha256']:
                    failures.append('映像の指紋が承認時と一致しません（Google AI モードの再レビューが必要）')
                if want.get('audio_md5') and got['audio_md5'] != want['audio_md5']:
                    failures.append('音声の指紋が承認時と一致しません（Google AI モードの再レビューが必要）')
        else:
            warnings.append('verification.json に指紋がありません（approve.py prepare で作成）')

    if run_format:
        p = subprocess.run([sys.executable, str(root / 'scripts' / 'shorts_standard.py'),
                            'check', str(result_path)],
                           text=True, encoding='utf-8', errors='replace', capture_output=True)
        if p.returncode != 0:
            errors = [l for l in (p.stdout + p.stderr).splitlines() if l.startswith('ERROR')]
            failures.append('形式検査が ERROR: %s' % (' / '.join(errors[:3]) or 'check 失敗'))

    info['passed'] = not failures
    return info


def main():
    ap = argparse.ArgumentParser(description='公開前ゲート')
    ap.add_argument('slug')
    ap.add_argument('--no-network', action='store_true', help='リンクの疎通確認をしない')
    ap.add_argument('--no-fingerprint', action='store_true', help='ストリーム指紋を計算しない')
    ap.add_argument('--json', action='store_true', help='結果をJSONで出す')
    a = ap.parse_args()

    info = evaluate(a.slug, network=not a.no_network, fingerprints=not a.no_fingerprint)
    if a.json:
        out = {k: str(v) if isinstance(v, Path) else v for k, v in info.items()}
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print('PASS' if info['passed'] else 'FAIL', '/', a.slug)
        if info.get('title'):
            print('  タイトル:', info['title'])
        if info.get('product_name'):
            print('  商品:', info['product_name'])
        if info.get('final_url'):
            print('  リンク:', info['final_url'])
        for f in info['failures']:
            print('  ERROR:', f)
        for w in info['warnings']:
            print('  WARN:', w)
    return 0 if info['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
