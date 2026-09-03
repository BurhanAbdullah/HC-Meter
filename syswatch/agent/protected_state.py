#!/usr/bin/env python3
"""Bounded integrity envelope for security-sensitive local state.

This module is deliberately I/O-free. A trusted caller supplies the key and
persists the returned envelope. The envelope provides versioned canonical
encoding and HMAC-SHA256 integrity; it does not provide encryption, key
storage, durable tamper-proof storage, or privilege.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from typing import Any

SCHEMA_VERSION = 1
MAX_PAYLOAD_BYTES = 64 * 1024
MIN_KEY_BYTES = 32


@dataclass(frozen=True)
class ProtectedState:
    version: int
    payload: dict[str, Any]
    mac: str

    def as_dict(self) -> dict[str, Any]:
        return {"version": self.version, "payload": self.payload, "mac": self.mac}


def _validate_key(key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) < MIN_KEY_BYTES:
        raise ValueError("integrity key must contain at least 32 bytes")


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    if not isinstance(payload, dict):
        raise ValueError("state payload must be an object")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise ValueError("state payload exceeds bounded size")
    return encoded


def _mac(key: bytes, version: int, payload_bytes: bytes) -> str:
    message = version.to_bytes(4, "big", signed=False) + b"\0" + payload_bytes
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def seal_state(payload: dict[str, Any], *, key: bytes) -> ProtectedState:
    """Create a deterministic integrity envelope without performing I/O."""
    _validate_key(key)
    payload_bytes = _canonical_payload(payload)
    return ProtectedState(SCHEMA_VERSION, payload, _mac(key, SCHEMA_VERSION, payload_bytes))


def verify_state(state: ProtectedState | dict[str, Any], *, key: bytes) -> dict[str, Any]:
    """Verify and return state payload, failing closed on any mismatch."""
    _validate_key(key)
    if isinstance(state, ProtectedState):
        candidate = state.as_dict()
    elif isinstance(state, dict):
        candidate = state
    else:
        raise ValueError("protected state must be an object")

    if candidate.get("version") != SCHEMA_VERSION:
        raise ValueError("unsupported protected-state version")
    payload = candidate.get("payload")
    mac = candidate.get("mac")
    if not isinstance(mac, str) or len(mac) != 64:
        raise ValueError("invalid integrity tag")
    payload_bytes = _canonical_payload(payload)
    expected = _mac(key, SCHEMA_VERSION, payload_bytes)
    if not hmac.compare_digest(mac, expected):
        raise ValueError("protected state integrity check failed")
    return dict(payload)
