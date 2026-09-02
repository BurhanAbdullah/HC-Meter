from pathlib import Path
import importlib.util
import json
import os

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "filesystem_behavior", ROOT / "syswatch" / "agent" / "filesystem_behavior.py"
)
filesystem = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(filesystem)


def test_snapshot_is_metadata_only_and_does_not_follow_symlinks(tmp_path):
    data = tmp_path / "sample.txt"
    data.write_text("synthetic-secret-content")
    link = tmp_path / "link"
    link.symlink_to(data)
    rows = filesystem.snapshot([tmp_path], max_files=20, max_depth=1)
    by_path = {row["path"]: row for row in rows}
    assert by_path[str(data)]["type"] == "file"
    assert by_path[str(link)]["type"] == "symlink"
    assert "content" not in by_path[str(data)]
    assert "synthetic-secret-content" not in json.dumps(rows)


def test_diff_detects_create_delete_and_metadata_change():
    old = [{"path": "/x", "type": "file", "size": 1, "mode": 0o600, "mtime_ns": 1}]
    new = [
        {"path": "/x", "type": "file", "size": 2, "mode": 0o600, "mtime_ns": 2},
        {"path": "/y", "type": "file", "size": 1, "mode": 0o600, "mtime_ns": 3},
    ]
    result = filesystem.diff_snapshots(old, new)
    assert result["created"] == ["/y"]
    assert result["deleted"] == []
    assert result["modified"] == ["/x"]


def test_collect_first_run_then_monitoring_and_private_state(tmp_path):
    root = tmp_path / "watched"
    root.mkdir()
    (root / "a").write_text("a")
    state = tmp_path / "state" / "baseline.json"

    first = filesystem.collect([root], state_path=state, max_files=20, max_depth=1)
    assert first["status"] == "BASELINING"
    assert first["events"]["created_count"] == 1
    assert state.exists()
    assert stat_mode(state) == 0o600

    (root / "b").write_text("b")
    second = filesystem.collect([root], state_path=state, max_files=20, max_depth=1)
    assert second["status"] == "MONITORING"
    assert second["events"]["created"] == [str(root / "b")]


def test_snapshot_is_bounded(tmp_path):
    for index in range(20):
        (tmp_path / f"f{index}").write_text("x")
    rows = filesystem.snapshot([tmp_path], max_files=5, max_depth=1)
    assert len(rows) == 5


def stat_mode(path):
    return os.stat(path).st_mode & 0o777
