from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from protected_state_store import KEY_BYTES, ProtectedStateStore


def _save(directory: str, value: int) -> bool:
    store = ProtectedStateStore(Path(directory))
    store.save({"worker": value})
    return store.check()["integrity"] == "PASS"


def test_concurrent_first_writes_share_one_valid_key(tmp_path):
    directory = tmp_path / "state"
    with ProcessPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_save, [str(directory)] * 8, range(8)))

    assert all(results)
    key = (directory / "state.key").read_bytes()
    assert len(key) == KEY_BYTES
    assert (directory / "state.json").exists()
    assert ProtectedStateStore(directory).check() == {
        "state": "PRESENT",
        "integrity": "PASS",
        "recoverable": True,
    }
