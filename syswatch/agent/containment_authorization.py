#!/usr/bin/env python3
"""Deterministic authorization and audit primitives for containment planning.

This module deliberately stops before privileged host mutation. It provides
only the data-integrity boundary that a future platform adapter must consume.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

MAX_FIELD = 128
REQUIRED_SCOPE = "containment:block-egress"


@dataclass(frozen=True)
class AuthorizationGrant:
    grant_id: str
    plan_id: str
    scope: str = REQUIRED_SCOPE
    approved_by: str = ""
    expires_at: int = 0


def containment_plan_id(plan: dict[str, Any]) -> str:
    """Return a stable identifier for an immutable containment plan."""
    canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def authorize_plan(
    plan: dict[str, Any] | None,
    grant: AuthorizationGrant | dict[str, Any] | None,
    *,
    now: int,
) -> dict[str, Any]:
    """Validate an explicit authorization grant without executing anything.

    The caller supplies time so validation remains deterministic and testable.
    No privilege escalation, firewall operation, process action, or other host
    mutation is performed here.
    """
    if not isinstance(plan, dict) or plan.get("status") != "PLAN_ONLY":
        return _rejected("invalid_plan")
    if grant is None:
        return _rejected("missing_authorization")
    if isinstance(grant, dict):
        grant = AuthorizationGrant(
            grant_id=grant.get("grant_id", ""),
            plan_id=grant.get("plan_id", ""),
            scope=grant.get("scope", REQUIRED_SCOPE),
            approved_by=grant.get("approved_by", ""),
            expires_at=grant.get("expires_at", 0),
        )
    plan_id = containment_plan_id(plan)
    fields_ok = all(
        isinstance(value, str) and 0 < len(value.strip()) <= MAX_FIELD
        for value in (grant.grant_id, grant.plan_id, grant.approved_by)
    )
    if not fields_ok:
        return _rejected("invalid_authorization")
    if grant.scope != REQUIRED_SCOPE:
        return _rejected("invalid_scope")
    if grant.plan_id != plan_id:
        return _rejected("plan_mismatch")
    if not isinstance(grant.expires_at, int) or grant.expires_at < now:
        return _rejected("authorization_expired")
    return {
        "status": "AUTHORIZED_PLAN",
        "plan_id": plan_id,
        "grant_id": grant.grant_id.strip(),
        "approved_by": grant.approved_by.strip(),
        "expires_at": grant.expires_at,
        "actions_taken": False,
        "security_verdict": "NONE",
        "privileged_adapter": "NOT_IMPLEMENTED",
    }


def audit_event(plan: dict[str, Any], authorization: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic audit record; does not persist or emit it."""
    plan_id = containment_plan_id(plan)
    if authorization.get("plan_id") != plan_id:
        raise ValueError("authorization does not match plan")
    event = {
        "event": "CONTAINMENT_AUTHORIZATION",
        "plan_id": plan_id,
        "grant_id": authorization.get("grant_id", ""),
        "approved_by": authorization.get("approved_by", ""),
        "actions_taken": False,
        "security_verdict": "NONE",
    }
    event["event_id"] = hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return event


def _rejected(reason: str) -> dict[str, Any]:
    return {
        "status": "REJECTED",
        "reason": reason,
        "actions_taken": False,
        "security_verdict": "NONE",
        "privileged_adapter": "NOT_IMPLEMENTED",
    }
