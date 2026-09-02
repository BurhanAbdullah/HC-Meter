#!/usr/bin/env python3
"""Bounded, read-only filesystem behavioral monitoring.

The monitor records metadata only: path, type, size, mode and mtime. It never
reads file contents, follows symlinks, executes files, or modifies monitored
paths. A small local state file can be used to compare successive snapshots.
"""

import json
import os
import stat
import tempfile
from pathlib import Path

DEFAULT_ROOTS = ("/tmp", "/var/tmp")
DEFAULT_MAX_FILES = 1000
DEFAULT_MAX_DEPTH = 2


def _entry(path):
    try:
        info = path.lstat()
    except OSError:
        return None
    if stat.S_ISLNK(info.st_mode):
        kind = "symlink"
    elif stat.S_ISDIR(info.st_mode):
        kind = "directory"
    elif stat.S_ISREG(info.st_mode):
        kind = "file"
    else:
        kind = "special"
    return {
        "path": str(path),
        "type": kind,
        "size": int(info.st_size),
        "mode": stat.S_IMODE(info.st_mode),
        "mtime_ns": int(info.st_mtime_ns),
    }


def snapshot(roots=DEFAULT_ROOTS, max_files=DEFAULT_MAX_FILES, max_depth=DEFAULT_MAX_DEPTH):
    """Return a bounded metadata-only filesystem snapshot."""
    rows = []
    seen = set()
    for root_value in roots:
        root = Path(root_value)
        if not root.exists() or not root.is_dir():
            continue
        stack = [(root, 0)]
        while stack and len(rows) < max_files:
            current, depth = stack.pop()
            try:
                children = list(os.scandir(current))
            except OSError:
                continue
            for item in children:
                if len(rows) >= max_files:
                    break
                path = Path(item.path)
                if path in seen:
                    continue
                seen.add(path)
                row = _entry(path)
                if row is None:
                    continue
                rows.append(row)
                if item.is_dir(follow_symlinks=False) and depth < max_depth:
                    stack.append((path, depth + 1))
    rows.sort(key=lambda row: row["path"])
    return rows[:max_files]


def diff_snapshots(previous, current):
    """Compare two metadata snapshots without reading file contents."""
    old = {row["path"]: row for row in previous}
    new = {row["path"]: row for row in current}
    created = sorted(set(new) - set(old))
    deleted = sorted(set(old) - set(new))
    modified = sorted(
        path for path in set(old) & set(new) if any(
            old[path].get(key) != new[path].get(key)
            for key in ("type", "size", "mode", "mtime_ns")
        )
    )
    return {
        "created": created,
        "deleted": deleted,
        "modified": modified,
        "created_count": len(created),
        "deleted_count": len(deleted),
        "modified_count": len(modified),
    }


def _load_state(path):
    try:
        data = json.loads(Path(path).read_text())
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def _save_state(path, snapshot_rows):
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp_name = tempfile.mkstemp(prefix=".fs-baseline-", dir=str(target.parent), text=True)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as handle:
            json.dump(snapshot_rows, handle, separators=(",", ":"), sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, target)
        os.chmod(target, 0o600)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def collect(roots=DEFAULT_ROOTS, state_path=None, max_files=DEFAULT_MAX_FILES, max_depth=DEFAULT_MAX_DEPTH):
    """Collect a snapshot and optionally update a private local baseline."""
    current = snapshot(roots=roots, max_files=max_files, max_depth=max_depth)
    if state_path is None:
        return {"status": "SNAPSHOT_ONLY", "files_observed": len(current), "events": diff_snapshots([], current), "snapshot": current}
    previous = _load_state(state_path)
    events = diff_snapshots(previous, current)
    _save_state(state_path, current)
    status = "BASELINING" if not previous else "MONITORING"
    return {"status": status, "files_observed": len(current), "events": events}
