import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

import pytest

from protected_state import MAX_PAYLOAD_BYTES, MIN_KEY_BYTES, ProtectedState, seal_state, verify_state

KEY = b"k" * MIN_KEY_BYTES


def test_seal_and_verify_are_deterministic():
    payload = {"policy": "observe", "counter": 3}
    first = seal_state(payload, key=KEY)
    second = seal_state(payload, key=KEY)
    assert first == second
    assert verify_state(first, key=KEY) == payload


def test_payload_order_does_not_change_integrity_tag():
    left = seal_state({"a": 1, "b": 2}, key=KEY)
    right = seal_state({"b": 2, "a": 1}, key=KEY)
    assert left.mac == right.mac


def test_tampering_fails_closed():
    state = seal_state({"policy": "observe"}, key=KEY).as_dict()
    state["payload"]["policy"] = "contain"
    with pytest.raises(ValueError, match="integrity check failed"):
        verify_state(state, key=KEY)


def test_wrong_key_fails_closed():
    state = seal_state({"policy": "observe"}, key=KEY)
    with pytest.raises(ValueError, match="integrity check failed"):
        verify_state(state, key=b"x" * MIN_KEY_BYTES)


def test_unsupported_version_fails_closed():
    state = seal_state({"policy": "observe"}, key=KEY).as_dict()
    state["version"] = 2
    with pytest.raises(ValueError, match="unsupported protected-state version"):
        verify_state(state, key=KEY)


def test_short_key_is_rejected():
    with pytest.raises(ValueError, match="at least 32 bytes"):
        seal_state({}, key=b"short")


def test_oversized_payload_is_bounded():
    oversized = {"data": "x" * (MAX_PAYLOAD_BYTES + 1)}
    with pytest.raises(ValueError, match="exceeds bounded size"):
        seal_state(oversized, key=KEY)


def test_boolean_and_null_values_are_supported_without_implicit_coercion():
    payload = {"enabled": True, "value": None, "count": 0}
    state = seal_state(payload, key=KEY)
    assert verify_state(state, key=KEY) == payload


def test_exported_envelope_has_no_key_material():
    state = seal_state({"policy": "observe"}, key=KEY).as_dict()
    assert "key" not in state
    assert KEY.decode() not in str(state)
    assert isinstance(ProtectedState(**state), ProtectedState)
