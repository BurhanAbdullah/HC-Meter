import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("syswatch_server", ROOT / "syswatch" / "api" / "server.py")
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


def test_process_lineage_shape_and_parent_links():
    rows = server.process_lineage(limit=1000)
    assert rows
    pids = {row['pid'] for row in rows}
    for row in rows:
        assert row['pid'] > 0
        assert row['ppid'] >= 0
        assert row['name']
        assert row['user']
        assert 'cmdline' not in row
        if row['ppid'] in pids:
            assert row['ppid'] != row['pid']


def test_process_lineage_is_bounded():
    rows = server.process_lineage(limit=3)
    assert len(rows) <= 3
