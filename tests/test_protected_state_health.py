from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from protected_state_store import ProtectedStateStore


def test_health_does_not_create_missing_state(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    assert store.check() == {"state": "ABSENT", "integrity": "NOT_CHECKED", "recoverable": True}
    assert not (tmp_path / "state").exists()


def test_health_reports_valid_state(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.save({"counter": 1})
    assert store.check() == {"state": "PRESENT", "integrity": "PASS", "recoverable": True}


def test_health_reports_corruption_fail_closed(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.save({"counter": 1})
    store.state_path.write_text("{\"version\":999}", encoding="utf-8")
    assert store.check() == {"state": "CORRUPT", "integrity": "FAIL", "recoverable": False}


def test_health_rejects_incomplete_state(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.directory.mkdir(mode=0o700)
    store.state_path.write_text("{}", encoding="utf-8")
    assert store.check() == {"state": "INCOMPLETE", "integrity": "FAIL", "recoverable": False}


def test_health_rejects_symlinked_state(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.save({"counter": 1})
    target = tmp_path / "real-state.json"
    target.write_bytes(store.state_path.read_bytes())
    store.state_path.unlink()
    store.state_path.symlink_to(target)
    assert store.check() == {"state": "CORRUPT", "integrity": "FAIL", "recoverable": False}
