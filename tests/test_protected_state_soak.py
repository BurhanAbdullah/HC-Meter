import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from protected_state_store import ProtectedStateStore


def _payload(iteration: int) -> dict[str, object]:
    digest = hashlib.sha256(f"syswatch-soak-{iteration}".encode()).hexdigest()
    return {
        "iteration": iteration,
        "digest": digest,
        "signals": [
            {"name": f"signal-{index}", "value": (iteration + index) % 17}
            for index in range(12)
        ],
        "metadata": {"phase": iteration % 5, "active": iteration % 3 != 0},
    }


def test_bounded_persistence_soak_preserves_integrity(tmp_path):
    """Repeated local persistence must remain readable and integrity-valid."""
    store = ProtectedStateStore(tmp_path / "state")

    for iteration in range(256):
        payload = _payload(iteration)
        store.save(payload)
        assert store.load() == payload
        assert store.check() == {
            "state": "PRESENT",
            "integrity": "PASS",
            "recoverable": True,
        }


def test_bounded_persistence_soak_keeps_previous_state_after_failed_write(tmp_path, monkeypatch):
    """A failed atomic replacement must not destroy the last valid state."""
    store = ProtectedStateStore(tmp_path / "state")
    original = _payload(0)
    store.save(original)
    previous_bytes = store.state_path.read_bytes()

    real_replace = __import__("os").replace

    def fail_replace(*args, **kwargs):
        raise OSError("injected replacement failure")

    monkeypatch.setattr("protected_state_store.os.replace", fail_replace)
    try:
        try:
            store.save(_payload(1))
        except OSError as exc:
            assert str(exc) == "injected replacement failure"
    finally:
        monkeypatch.setattr("protected_state_store.os.replace", real_replace)

    assert store.state_path.read_bytes() == previous_bytes
    assert store.load() == original
    assert store.check() == {
        "state": "PRESENT",
        "integrity": "PASS",
        "recoverable": True,
    }
