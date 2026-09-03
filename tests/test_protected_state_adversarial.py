import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from protected_state import MAX_PAYLOAD_BYTES, MIN_KEY_BYTES, seal_state, verify_state

KEY = b"k" * MIN_KEY_BYTES


def _payload(seed: int) -> dict[str, object]:
    rng = random.Random(seed)
    return {
        "enabled": bool(rng.randrange(2)),
        "counter": rng.randrange(1_000_000),
        "labels": [f"signal-{rng.randrange(100)}" for _ in range(8)],
        "metadata": {f"k{index}": rng.randrange(1_000) for index in range(8)},
    }


def test_deterministic_adversarial_payload_corpus_round_trips():
    for seed in range(64):
        payload = _payload(seed)
        state = seal_state(payload, key=KEY)
        assert verify_state(state, key=KEY) == payload


def test_nested_payload_near_json_recursion_boundary_remains_bounded():
    payload: object = {"leaf": True}
    for _ in range(64):
        payload = {"next": payload}
    with pytest.raises(ValueError, match="exceeds maximum nesting depth"):
        seal_state(payload, key=KEY)  # type: ignore[arg-type]


def test_large_string_corpus_is_rejected_before_integrity_publication():
    for size in (MAX_PAYLOAD_BYTES, MAX_PAYLOAD_BYTES + 1, MAX_PAYLOAD_BYTES * 2):
        payload = {"blob": "x" * size}
        with pytest.raises(ValueError, match="exceeds bounded size"):
            seal_state(payload, key=KEY)
