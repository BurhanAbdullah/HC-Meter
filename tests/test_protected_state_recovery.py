import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from protected_state_store import MAX_STATE_FILE_BYTES, ProtectedStateStore


def test_malformed_state_fails_closed_without_repair(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.save({"counter": 7})
    original_key = store.key_path.read_bytes()
    store.state_path.write_bytes(b"{not-json")
    with pytest.raises(json.JSONDecodeError):
        store.load()
    assert store.key_path.read_bytes() == original_key
    assert store.state_path.read_bytes() == b"{not-json"
    assert store.check() == {"state": "CORRUPT", "integrity": "FAIL", "recoverable": False}


def test_oversized_state_fails_closed(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.save({"counter": 7})
    store.state_path.write_bytes(b"x" * (MAX_STATE_FILE_BYTES + 1))
    with pytest.raises(ValueError, match="exceeds bounded size"):
        store.load()
    assert store.check() == {"state": "CORRUPT", "integrity": "FAIL", "recoverable": False}


def test_incomplete_state_is_reported_without_key_creation(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.directory.mkdir(mode=0o700)
    store.state_path.write_text("{}", encoding="utf-8")
    assert store.check() == {"state": "INCOMPLETE", "integrity": "FAIL", "recoverable": False}
    assert not store.key_path.exists()


def test_atomic_save_preserves_previous_state_on_replace_failure(tmp_path, monkeypatch):
    store = ProtectedStateStore(tmp_path / "state")
    store.save({"counter": 1})
    original = store.state_path.read_bytes()

    def fail_replace(src, dst):
        raise OSError("simulated interrupted publication")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match="interrupted"):
        store.save({"counter": 2})

    assert store.state_path.read_bytes() == original
    assert store.load() == {"counter": 1}
    assert not list(store.directory.glob(".state-*"))
