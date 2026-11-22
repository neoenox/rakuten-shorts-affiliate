"""レビュー支援スクリプトの回帰テスト（dry run の副作用と返答判定）。"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    path = SCRIPTS / f'{name}.py'
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'load failed: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


muse = load('muse_review')
review = load('script_review')


def test_muse_dry_run_does_not_compress_or_open_browser(tmp_path, monkeypatch):
    sd = tmp_path / 'shorts' / 'demo'
    sd.mkdir(parents=True)
    (sd / 'result.json').write_text(json.dumps({'title': '題名', 'duration_sec': 35}), encoding='utf-8')
    draft = tmp_path / 'out' / 'draft' / 'demo_DRAFT.mp4'
    draft.parent.mkdir(parents=True)
    draft.write_bytes(b'video')
    monkeypatch.setattr(muse, 'ROOT', tmp_path)
    monkeypatch.setattr(muse, 'compress', lambda *a, **kw: (_ for _ in ()).throw(AssertionError('compress called')))
    monkeypatch.setattr(muse, 'C', lambda *a, **kw: (_ for _ in ()).throw(AssertionError('browser opened')))
    monkeypatch.setattr(sys, 'argv', ['muse_review.py', 'demo', '--dry-run'])

    assert muse.main() == 0


def test_muse_reply_can_be_short():
    assert muse.reply_ready('短いが完成した返答', '短いが完成した返答', 3, False, 5)
    assert not muse.reply_ready('短い', '短い', 3, False, 5)



def test_muse_extract_reply_takes_only_last_exchange():
    log = (
        '過去の会話一覧（サイドバー）\n'
        f'{muse.MARK}\n古い依頼への返答\n'
        '== 現在のスレッド ==\n'
        f'{muse.MARK}\n'
        'これが正しい返答です。\n二行目。'
    )
    assert muse.extract_reply(log) == 'これが正しい返答です。\n二行目。'


def test_muse_extract_reply_drops_trailing_ui():
    log = f'{muse.MARK}\n公開可です。\n最新の応答\nこのパーソナリティは気に入りましたか'
    assert muse.extract_reply(log) == '公開可です。'


def test_muse_extract_reply_without_log_is_empty():
    assert muse.extract_reply('') == ''
    assert muse.extract_reply('マーカーが無い本文') == ''

def test_script_reply_can_be_short():
    assert review.reply_ready('短いが完成した返答', '短いが完成した返答', 3, False, 5)
    assert not review.reply_ready('短い', '短い', 3, False, 5)
