#!/usr/bin/env python3
"""Fail-closed, reversible containment planning.

This module intentionally does not mutate host state. It validates a requested
containment target and returns a deterministic plan that a future privileged
adapter may consume after an explicit authorization boundary is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any

MAX_TARGETS = 32
MAX_REASON = 240
ALLOWED_TARGET_KINDS = {"ip"}


@dataclass(frozen=True)
class ContainmentRequest:
    target: str
    kind: str = "ip"
    reason: str = ""


def _target(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip()
    try:
        return str(ip_address(value))
    except ValueError:
        return ""


def plan_containment(request: ContainmentRequest | dict[str, Any] | None) -> dict[str, Any]:
    """Return a bounded no-side-effect containment plan.

    The returned plan is advisory only. No firewall command, process action,
    socket operation, or other host mutation is performed here.
    """
    if request is None:
        return _rejected("missing_request")
    if isinstance(request, dict):
        request = ContainmentRequest(
            target=request.get("target", ""),
            kind=request.get("kind", "ip"),
            reason=request.get("reason", ""),
        )
    kind = request.kind if request.kind in ALLOWED_TARGET_KINDS else ""
    target = _target(request.target) if kind else ""
    if not kind or not target:
        return _rejected("invalid_target")
    reason = request.reason if isinstance(request.reason, str) else ""
    reason = reason.strip()[:MAX_REASON]
    return {
        "status": "PLAN_ONLY",
        "target": {"kind": kind, "value": target},
        "action": "BLOCK_EGRESS",
        "reason": reason,
        "reversible": True,
        "actions_taken": False,
        "security_verdict": "NONE",
        "authorization_required": True,
        "privileged_adapter": "NOT_IMPLEMENTED",
    }


def _rejected(reason: str) -> dict[str, Any]:
    return {
        "status": "REJECTED",
        "reason": reason,
        "reversible": True,
        "actions_taken": False,
        "security_verdict": "NONE",
        "authorization_required": True,
        "privileged_adapter": "NOT_IMPLEMENTED",
    }
