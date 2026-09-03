import json
import os
import stat
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from protected_state_store import ProtectedStateStore


def test_store_round_trip_and_permissions(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    payload = {"counter": 7, "mode": "baseline"}
    store.save(payload)

    assert store.load() == payload
    assert stat.S_IMODE(store.directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(store.key_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.state_path.stat().st_mode) == 0o600


def test_tampered_state_fails_closed(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.save({"counter": 7})
    candidate = json.loads(store.state_path.read_text(encoding="utf-8"))
    candidate["payload"]["counter"] = 8
    store.state_path.write_text(json.dumps(candidate), encoding="utf-8")

    with pytest.raises(ValueError, match="integrity"):
        store.load()


def test_tampered_key_fails_closed(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.save({"counter": 7})
    store.key_path.write_bytes(os.urandom(32))

    with pytest.raises(ValueError, match="integrity"):
        store.load()


def test_state_symlink_is_rejected(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.directory.mkdir(mode=0o700)
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    store.state_path.symlink_to(target)

    with pytest.raises(ValueError, match="symlink"):
        store.load()


def test_key_symlink_is_not_followed(tmp_path):
    store = ProtectedStateStore(tmp_path / "state")
    store.directory.mkdir(mode=0o700)
    target = tmp_path / "key-target"
    target.write_bytes(os.urandom(32))
    store.key_path.symlink_to(target)

    with pytest.raises(OSError):
        store.save({"counter": 7})
