"""照合の証跡（verification.json）を作り、オーナーの承認を記録する。

usage:
  python scripts/approve.py prepare <slug> [--frames-ok] [--conditions-ok]
      [--expressions-ok] [--product-ok] [--resolve "N=解決内容"]... [--limitation "留保"]...
  python scripts/approve.py sign <slug> --by owner
  python scripts/approve.py revoke <slug> --reason "理由"

prepare は機械で確認できる項目を埋め、人が判断する項目をフラグで記録する。
failures が空でないと sign できない。sign は result.json を ready にし、
needs_research を空にする（準備時に全項目の解決内容を記録済みであることが条件）。
"""
import argparse
import html
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import gate  # noqa: E402

APPROVAL_DAYS = 14
MANUAL_KEYS = ('frames', 'conditions', 'expressions', 'product')


def now_iso():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def load(path):
    return gate.load_json(path)


def dump(path, obj):
    gate.dump_json(path, obj)


def check_format(path):
    """shorts_standard.py の形式検査を実行し、(成否, ERROR行) を返す。"""
    p = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'shorts_standard.py'),
                        'check', str(path)],
                       text=True, encoding='utf-8', errors='replace', capture_output=True)
    errors = [line for line in (p.stdout + p.stderr).splitlines() if line.startswith('ERROR')]
    return p.returncode == 0, errors


def parse_resolves(resolves, needs_count):
    """--resolve の "N=解決内容" を {N: 解決内容} に変換する。"""
    by_index = {}
    for entry in resolves:
        if '=' not in entry:
            raise SystemExit('--resolve は "N=解決内容" の形式で指定する: %s' % entry)
        raw, text = entry.split('=', 1)
        try:
            n = int(raw)
        except ValueError:
            raise SystemExit(f'--resolve の番号は整数で指定する: {entry}') from None
        if n < 1 or n > needs_count:
            raise SystemExit(f'--resolve の番号が範囲外: {n}')
        by_index[n] = text.strip()
    return by_index


def normalize_numbers(text):
    """全角数字・カンマを正規化し、数値の集合を作る。"""
    table = str.maketrans('０１２３４５６７８９．', '0123456789.')
    t = html.unescape(re.sub(r'<[^>]+>', ' ', str(text))).translate(table)
    t = t.replace(',', '').replace('，', '')
    vals = set()
    for m in re.findall(r'\d+(?:\.\d+)?', t):
        try:
            vals.add(round(float(m), 6))
        except ValueError:
            pass
    return vals


def fetch_source(url, timeout=25):
    r = requests.get(url, headers={'User-Agent': gate.UA}, timeout=timeout)
    if r.content[:4] == b'%PDF':
        # ハンドブックのような一次資料は PDF のまま配布される。本文を抽出して数値を照合する
        try:
            import io

            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(r.content))
            return r.status_code, '\n'.join((page.extract_text() or '') for page in reader.pages)
        except Exception:
            return r.status_code, ''
    return r.status_code, r.text


def prepare(slug, flags, resolves, limitations):
    sd = ROOT / 'shorts' / slug
    result_path = sd / 'result.json'
    render_path = sd / 'render.json'
    ver_path = sd / 'verification.json'
    draft_dir = ROOT / 'out' / 'draft'
    stem = slug + '_DRAFT'
    draft_mp4 = draft_dir / (stem + '.mp4')
    draft_thumb = draft_dir / (stem + '_thumb.jpg')
    draft_desc = draft_dir / (stem + '_description.md')
    draft_comment = draft_dir / (stem + '_fixed_comment.md')
    review_path = sd / 'review_muse.md'

    failures = []
    data = load(result_path)
    conf = load(render_path)
    title = str(data.get('title') or '').strip()
    product_name = str(conf.get('product_name') or '').strip()
    affiliate_url = str((conf.get('affiliate') or {}).get('url') or '').strip()

    if data.get('status') == 'ready':
        raise SystemExit('すでに ready です。再承認するなら先に revoke してください。')

    # --- 残件の解決記録
    needs = list(data.get('needs_research') or [])
    resolved = []
    by_index = parse_resolves(resolves, len(needs))
    for i, item in enumerate(needs, 1):
        if i in by_index:
            resolved.append({'item': item, 'resolution': by_index[i]})
        else:
            failures.append('needs_research[%d] の解決内容が未指定: %s' % (i, item))

    # --- draft 成果物
    for path, label in ((draft_mp4, 'draft 動画'), (draft_thumb, 'draft サムネイル'),
                        (draft_desc, 'draft 説明欄'), (draft_comment, 'draft 固定コメント')):
        if not path.is_file() or path.stat().st_size == 0:
            failures.append('%sが見つかりません: %s' % (label, path))

    presentation = {'failures': []}
    if draft_desc.is_file() and draft_comment.is_file():
        presentation['failures'] = gate.check_presentation(
            draft_desc.read_text(encoding='utf-8'),
            draft_comment.read_text(encoding='utf-8'),
            title, product_name, affiliate_url)
        failures.extend(presentation['failures'])

    # --- リンク
    link = {}
    try:
        link['final'] = gate.resolve_affiliate_link(affiliate_url)
        link['passed'] = True
    except (ValueError, requests.RequestException) as exc:
        link['error'] = str(exc)
        link['passed'] = False
        failures.append('リンク: %s' % exc)

    # --- 商品ページ
    product = {'name_in_config': product_name, 'manual': True,
               'passed': bool(flags.get('product'))}
    if link.get('passed'):
        try:
            info = gate.fetch_item_page(link['final'])
            product.update(info)
            if info.get('http_status') != 200:
                failures.append('商品ページの HTTP が %s です' % info.get('http_status'))
        except requests.RequestException as exc:
            failures.append('商品ページを取得できません: %s' % exc)
    if not flags.get('product'):
        failures.append('未確認: 商品名・価格・販売状態の一致（--product-ok）')

    # --- 出典と数値
    sources = []
    source_cache = {}
    for c in data.get('claims') or []:
        url = c.get('source_url') or ''
        rec = {'claim_id': c.get('id'), 'url': url}
        if c.get('source_type') != 'primary' or not url:
            rec['note'] = '一次資料URLなし（ai_assistant）'
            rec['numbers_missing'] = []
            sources.append(rec)
            continue
        if url not in source_cache:
            try:
                status, body = fetch_source(url)
                source_cache[url] = (status, normalize_numbers(body))
            except requests.RequestException as exc:
                source_cache[url] = (0, set())
                rec['error'] = str(exc)
        status, values = source_cache[url]
        rec['http_status'] = status
        want = normalize_numbers(c.get('statement') or '')
        missing = sorted(v for v in want if v not in values)
        rec['numbers_total'] = len(want)
        rec['numbers_missing'] = missing
        rec['numbers_found'] = not missing
        if status != 200:
            failures.append('出典の HTTP が %s: %s' % (status, url))
        if missing:
            failures.append('原文に見つからない数値 %s（%s）: %s'
                            % (missing, rec['claim_id'], url))
        sources.append(rec)

    # --- 形式検査
    fmt_ok, fmt_errors = check_format(result_path)
    fmt = {'passed': fmt_ok, 'errors': fmt_errors}
    if not fmt['passed']:
        failures.append('形式検査が ERROR: %s' % (' / '.join(fmt['errors'][:3]) or 'check 失敗'))

    # --- Muse レビュー
    review = {'file': review_path.name, 'exists': review_path.is_file(), 'passed': False}
    if review_path.is_file():
        review['mtime'] = datetime.fromtimestamp(review_path.stat().st_mtime).astimezone().isoformat(timespec='seconds')
        text = review_path.read_text(encoding='utf-8')
        review['verdict'] = next((l.strip() for l in text.splitlines() if '公開可' in l), None)
        if draft_mp4.is_file():
            review['newer_than_draft'] = review_path.stat().st_mtime > draft_mp4.stat().st_mtime
        else:
            review['newer_than_draft'] = False
        review['passed'] = bool(review['verdict']) and review['newer_than_draft']
    if not review['passed']:
        failures.append('Muse レビュー: review_muse.md が無い／draft より古い／「公開可」が無い')

    # --- 人の判断
    manual = {}
    for key, label in (('frames', 'フレーム3点の目視'), ('conditions', '試算条件の一致'),
                       ('expressions', '断定・効能表現の排除')):
        ok = bool(flags.get(key))
        manual[key] = {'manual': True, 'label': label, 'passed': ok}
        if not ok:
            failures.append('未確認: %s（--%s-ok）' % (label, key))

    # --- 指紋
    artifacts = {'file': str(draft_mp4.relative_to(ROOT))}
    if draft_mp4.is_file():
        try:
            artifacts.update(gate.stream_fingerprints(draft_mp4))
        except RuntimeError as exc:
            failures.append(str(exc))

    ver = {
        'slug': slug,
        'status': 'pending',
        'checked_at': now_iso(),
        'approved_at': None,
        'approved_by': None,
        'expires_at': None,
        'result_sha256': gate.sha256_file(result_path),
        'review': review,
        'artifacts': artifacts,
        'checks': {
            'sources': sources,
            'product': product,
            'link': link,
            'presentation': presentation,
            'format': fmt,
            'frames': manual['frames'],
            'conditions': manual['conditions'],
            'expressions': manual['expressions'],
        },
        'failures': failures,
        'resolved_needs': resolved,
        'limitations': list(limitations),
    }
    dump(ver_path, ver)

    print('検証: %s / %s' % ('PASS' if not failures else 'FAIL', slug))
    for f in failures:
        print('  ERROR:', f)
    print('  証跡:', ver_path)
    return 0 if not failures else 1


def sign(slug, by):
    sd = ROOT / 'shorts' / slug
    result_path = sd / 'result.json'
    ver_path = sd / 'verification.json'
    ver = load(ver_path)
    data = load(result_path)

    if ver.get('status') != 'pending':
        raise SystemExit('承認できません: verification.json の status が %r' % ver.get('status'))
    if ver.get('failures'):
        raise SystemExit('承認できません: 未解消の failures がある（prepare をやり直す）')
    for key in MANUAL_KEYS:
        if not (ver.get('checks', {}).get(key) or {}).get('passed'):
            raise SystemExit('承認できません: 未確認の項目がある: %s' % key)
    if ver.get('result_sha256') != gate.sha256_file(result_path):
        raise SystemExit('承認できません: prepare 後に result.json が変更されている')
    needs = list(data.get('needs_research') or [])
    resolved = {r.get('item') for r in (ver.get('resolved_needs') or [])}
    missing = [n for n in needs if n not in resolved]
    if missing:
        raise SystemExit('承認できません: 解決内容が記録されていない残件がある: ' + ' / '.join(missing))

    # ready に変更した後の台本が標準を満たすか先に確認する（needs_review では通らない規則がある）
    ready_data = dict(data)
    ready_data['status'] = 'ready'
    ready_data['needs_research'] = []
    ready_check = result_path.with_name(result_path.stem + '.ready-check.json')
    try:
        dump(ready_check, ready_data)
        fmt_ok, fmt_errors = check_format(ready_check)
    finally:
        ready_check.unlink(missing_ok=True)
    if not fmt_ok:
        raise SystemExit('承認できません: ready 変更後の形式検査に失敗: %s'
                         % (' / '.join(fmt_errors[:3]) or 'check 失敗'))

    # result.json を ready にする（needs_research は解決済みなので空）
    dump(result_path, ready_data)

    approved_at = datetime.now().astimezone()
    ver['status'] = 'approved'
    ver['approved_by'] = by
    ver['approved_at'] = approved_at.isoformat(timespec='seconds')
    ver['expires_at'] = (approved_at.date() + timedelta(days=APPROVAL_DAYS)).isoformat()
    ver['result_sha256'] = gate.sha256_file(result_path)
    dump(ver_path, ver)

    print('承認: %s（%s）' % (slug, by))
    print('  有効期限:', ver['expires_at'])
    print('  次: python scripts/render_short.py %s' % slug)
    print('      python scripts/gate.py %s' % slug)
    print('      python scripts/upload_short.py %s --check-only' % slug)
    return 0


def revoke(slug, reason):
    sd = ROOT / 'shorts' / slug
    ver_path = sd / 'verification.json'
    result_path = sd / 'result.json'
    ver = load(ver_path)
    ver['status'] = 'revoked'
    ver['revoked_at'] = now_iso()
    ver['revoke_reason'] = reason
    dump(ver_path, ver)
    data = load(result_path)
    data['status'] = 'needs_review'
    dump(result_path, data)
    print('取消: %s / %s' % (slug, reason))
    return 0


def main():
    ap = argparse.ArgumentParser(description='照合の証跡と承認')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('prepare', help='照合して verification.json を作る')
    p.add_argument('slug')
    p.add_argument('--frames-ok', action='store_true', help='フレーム3点を目視した')
    p.add_argument('--conditions-ok', action='store_true', help='試算条件が原文と一致する')
    p.add_argument('--expressions-ok', action='store_true', help='断定・効能表現がない')
    p.add_argument('--product-ok', action='store_true', help='商品名・価格・販売状態が一致する')
    p.add_argument('--resolve', action='append', default=[], metavar='N=TEXT',
                   help='needs_research[N] の解決内容')
    p.add_argument('--limitation', action='append', default=[], metavar='TEXT',
                   help='調べても埋まらない留保')

    p = sub.add_parser('sign', help='オーナー承認を記録し status を ready にする')
    p.add_argument('slug')
    p.add_argument('--by', required=True)

    p = sub.add_parser('revoke', help='承認を取り消す')
    p.add_argument('slug')
    p.add_argument('--reason', required=True)

    a = ap.parse_args()
    if a.cmd == 'prepare':
        flags = {'frames': a.frames_ok, 'conditions': a.conditions_ok,
                 'expressions': a.expressions_ok, 'product': a.product_ok}
        return prepare(a.slug, flags, a.resolve, a.limitation)
    if a.cmd == 'sign':
        return sign(a.slug, a.by)
    return revoke(a.slug, a.reason)


if __name__ == '__main__':
    sys.exit(main())
