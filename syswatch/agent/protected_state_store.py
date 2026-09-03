#!/usr/bin/env python3
"""Fail-closed local persistence for protected SYSWATCH state.

The store keeps the integrity key and state in separate 0600 files, creates
missing files without following symlinks, and writes state atomically with an
fsync before replacement. It is intended for local unprivileged state and is
not a substitute for a kernel-backed keyring, TPM, remote append-only log, or
an independent trust anchor.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import tempfile
from typing import Any

from protected_state import MAX_PAYLOAD_BYTES, ProtectedState, seal_state, verify_state

KEY_BYTES = 32
MAX_STATE_FILE_BYTES = MAX_PAYLOAD_BYTES + 512


class ProtectedStateStore:
    """Persist one bounded integrity-protected state object locally."""

    def __init__(self, directory: Path, *, key_name: str = "state.key", state_name: str = "state.json") -> None:
        self.directory = Path(directory)
        self.key_path = self.directory / key_name
        self.state_path = self.directory / state_name

    def _ensure_directory(self) -> None:
        if self.directory.exists() and self.directory.is_symlink():
            raise ValueError("protected state directory must not be a symlink")
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.is_symlink():
            raise ValueError("protected state directory must not be a symlink")
        os.chmod(self.directory, 0o700)

    def _load_or_create_key(self) -> bytes:
        self._ensure_directory()
        try:
            fd = os.open(self.key_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        except FileNotFoundError:
            key = secrets.token_bytes(KEY_BYTES)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(self.key_path, flags, 0o600)
            try:
                written = 0
                while written < len(key):
                    written += os.write(fd, key[written:])
                os.fsync(fd)
            finally:
                os.close(fd)
            os.chmod(self.key_path, 0o600)
            return key
        try:
            key = os.read(fd, KEY_BYTES + 1)
        finally:
            os.close(fd)
        if len(key) != KEY_BYTES:
            raise ValueError("protected state key has invalid length")
        return key

    def save(self, payload: dict[str, Any]) -> ProtectedState:
        """Seal and atomically persist state; fail closed on filesystem errors."""
        key = self._load_or_create_key()
        state = seal_state(payload, key=key)
        encoded = json.dumps(state.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        if len(encoded) > MAX_STATE_FILE_BYTES:
            raise ValueError("protected state file exceeds bounded size")
        self._ensure_directory()
        fd, temp_name = tempfile.mkstemp(prefix=".state-", dir=self.directory, text=False)
        temp_path = Path(temp_name)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, self.state_path)
            os.chmod(self.state_path, 0o600)
        except Exception:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
            raise
        return state

    def load(self) -> dict[str, Any] | None:
        """Load, bound, decode, and verify state; return None when absent."""
        if not self.state_path.exists():
            return None
        if self.state_path.is_symlink():
            raise ValueError("protected state path must not be a symlink")
        stat_result = self.state_path.stat()
        if stat_result.st_size > MAX_STATE_FILE_BYTES:
            raise ValueError("protected state file exceeds bounded size")
        key = self._load_or_create_key()
        raw = self.state_path.read_bytes()
        candidate = json.loads(raw.decode("utf-8"))
        return verify_state(candidate, key=key)
