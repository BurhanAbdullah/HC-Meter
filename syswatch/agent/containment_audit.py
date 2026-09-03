#!/usr/bin/env python3
"""Bounded, deterministic audit ledger for containment state transitions.

The ledger is intentionally local and in-memory. It does not grant privilege,
perform host mutation, or claim durable storage. Entries are chained with
SHA-256 digests so accidental or replay modification is detectable when the
ledger is exported or verified by a trusted caller.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable

MAX_ENTRIES = 256
MAX_FIELD = 256
GENESIS = "0" * 64


@dataclass(frozen=True)
class AuditEntry:
    sequence: int
    event: str
    plan_id: str
    grant_id: str
    status: str
    actions_taken: bool
    timestamp: int
    previous_hash: str
    entry_hash: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "event": self.event,
            "plan_id": self.plan_id,
            "grant_id": self.grant_id,
            "status": self.status,
            "actions_taken": self.actions_taken,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class ContainmentAuditLedger:
    """Bounded append-only ledger with deterministic integrity verification."""

    def __init__(self, *, max_entries: int = MAX_ENTRIES) -> None:
        if not isinstance(max_entries, int) or not 1 <= max_entries <= MAX_ENTRIES:
            raise ValueError("max_entries must be between 1 and 256")
        self._max_entries = max_entries
        self._entries: list[AuditEntry] = []

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        return tuple(self._entries)

    def append(
        self,
        *,
        event: str,
        plan_id: str,
        grant_id: str,
        status: str,
        actions_taken: bool,
        timestamp: int,
    ) -> AuditEntry:
        values = (event, plan_id, grant_id, status)
        if not all(isinstance(value, str) and 0 < len(value.strip()) <= MAX_FIELD for value in values):
            raise ValueError("audit fields are invalid")
        if type(actions_taken) is not bool:
            raise ValueError("actions_taken must be boolean")
        if type(timestamp) is not int or timestamp < 0:
            raise ValueError("timestamp must be a non-negative integer")
        if len(self._entries) >= self._max_entries:
            raise RuntimeError("containment audit ledger capacity reached")

        sequence = len(self._entries)
        previous_hash = self._entries[-1].entry_hash if self._entries else GENESIS
        payload = {
            "sequence": sequence,
            "event": event.strip(),
            "plan_id": plan_id.strip(),
            "grant_id": grant_id.strip(),
            "status": status.strip(),
            "actions_taken": actions_taken,
            "timestamp": timestamp,
            "previous_hash": previous_hash,
        }
        entry = AuditEntry(**payload, entry_hash=_digest(payload))
        self._entries.append(entry)
        return entry

    def verify(self, entries: Iterable[AuditEntry] | None = None) -> bool:
        chain = tuple(self._entries if entries is None else entries)
        if len(chain) > self._max_entries:
            return False
        previous = GENESIS
        for expected_sequence, entry in enumerate(chain):
            if entry.sequence != expected_sequence or entry.previous_hash != previous:
                return False
            payload = entry.as_dict()
            actual = payload.pop("entry_hash")
            if actual != _digest(payload):
                return False
            previous = entry.entry_hash
        return True

    def export(self) -> tuple[dict[str, Any], ...]:
        """Return immutable-value records; no persistence is performed."""
        return tuple(entry.as_dict() for entry in self._entries)
