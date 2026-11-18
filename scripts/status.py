"""状態の一覧（docs/STATUS.md）を生成する。

usage:
  python scripts/status.py            # docs/STATUS.md を書き換える
  python scripts/status.py --check    # 差分があれば exit 1（CI向け）

正はファイル：shorts/<slug>/result.json / verification.json / publish.json。
このスクリプトは表示だけを作る（状態を書き換えない）。
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import gate  # noqa: E402

OUT = ROOT / 'docs' / 'STATUS.md'


def approval_state(slug, sd):
    vp = sd / 'verification.json'
    if not vp.is_file():
        return '未承認'
    ver = gate.load_json(vp)
    status = ver.get('status')
    if status == 'pending':
        return '承認待ち'
    if status == 'revoked':
        return '取消'
    if status != 'approved':
        return str(status)
    rp = sd / 'result.json'
    if ver.get('result_sha256') != gate.sha256_file(rp):
        return '失効（台本変更）'
    if gate.is_expired(ver.get('expires_at')):
        return '期限切れ'
    return '承認済み（〜%s）' % str(ver.get('expires_at'))[:10]


def publish_state(sd):
    pp = sd / 'publish.json'
    if not pp.is_file():
        return '未公開', None
    pub = gate.load_json(pp)
    vis = pub.get('visibility')
    if vis == 'public':
        return '公開', pub.get('video_id')
    if vis == 'held':
        return '保留', pub.get('video_id')
    if vis in ('unlisted', 'private'):
        return vis, pub.get('video_id')
    return '未公開', pub.get('video_id')


def count_limitations(sd):
    n = 0
    vp = sd / 'verification.json'
    if vp.is_file():
        n += len(gate.load_json(vp).get('limitations') or [])
    pp = sd / 'publish.json'
    if pp.is_file():
        items = gate.load_json(pp).get('legacy_open_items') or []
        n += sum(1 for i in items if i.get('status') in ('open', 'accepted'))
    return n


def next_action(slug, pub_state, appr, needs):
    if pub_state == '公開':
        return '—（公開済み）'
    if pub_state == '保留':
        return '改稿して再開'
    if appr.startswith('承認済み'):
        if (ROOT / 'out' / ('%s.mp4' % slug)).is_file():
            return 'アップロード（週1）'
        return '再描画 → gate → アップロード'
    if needs:
        return '残件を解消 → prepare'
    return 'prepare → 承認'


def rows():
    out = []
    for sd in sorted((ROOT / 'shorts').iterdir()):
        rp = sd / 'result.json'
        if not sd.is_dir() or not rp.is_file():
            continue
        data = gate.load_json(rp)
        appr = approval_state(sd.name, sd)
        pub, vid = publish_state(sd)
        needs = len(data.get('needs_research') or [])
        out.append({
            'slug': sd.name,
            'title': str(data.get('title') or ''),
            'status': str(data.get('status') or ''),
            'approval': appr,
            'publish': pub,
            'video_id': vid,
            'needs': needs,
            'limitations': count_limitations(sd),
            'next': next_action(sd.name, pub, appr, needs),
        })
    order = {'公開': 0, '保留': 1, '未公開': 2}
    out.sort(key=lambda r: (order.get(r['publish'], 3), r['slug']))
    return out


def render(rs):
    lines = []
    lines.append('# 状態（生成物）')
    lines.append('')
    lines.append('このファイルは `python scripts/status.py` が生成します。**手で編集しない。**')
    lines.append('正は `shorts/<slug>/result.json` / `verification.json` / `publish.json`。')
    lines.append('')
    lines.append('| slug | タイトル | 台本 | 承認 | 公開 | 残件 | 留保 | 次 |')
    lines.append('| --- | --- | --- | --- | --- | --- | --- | --- |')
    for r in rs:
        pub = r['publish'] + ('（%s）' % r['video_id'] if r['video_id'] else '')
        lines.append('| `%s` | %s | %s | %s | %s | %d | %d | %s |' % (
            r['slug'], r['title'].replace('|', '\\|'), r['status'], r['approval'],
            pub, r['needs'], r['limitations'], r['next']))
    lines.append('')
    pub_n = sum(1 for r in rs if r['publish'] == '公開')
    lines.append('公開 %d本 / 保留 %d本 / 未公開 %d本（全%d本）' % (
        pub_n, sum(1 for r in rs if r['publish'] == '保留'),
        sum(1 for r in rs if r['publish'] == '未公開'), len(rs)))
    lines.append('')
    lines.append('## 見方')
    lines.append('')
    lines.append('- **台本**: `result.json` の `status`（`ready` は承認済み・期限内のときだけ）')
    lines.append('- **承認**: `verification.json` の状態。`失効（台本変更）` は `result.json` が承認後に変わった')
    lines.append('- **公開**: `publish.json` の `visibility`。公開済みでも旧フローなら台本は `needs_review` のまま')
    lines.append('- **残件**: `needs_research` の件数（0 でないと `ready` にできない）')
    lines.append('- **留保**: `limitations` と `legacy_open_items`（open/accepted）の件数')
    lines.append('')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description='状態表を生成する')
    ap.add_argument('--check', action='store_true', help='差分があれば exit 1')
    a = ap.parse_args()
    text = render(rows())
    if a.check:
        current = OUT.read_text(encoding='utf-8') if OUT.is_file() else ''
        if current != text:
            print('差分あり: %s を更新してください' % OUT)
            return 1
        print('OK: %s' % OUT)
        return 0
    OUT.write_text(text, encoding='utf-8')
    print('wrote:', OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
