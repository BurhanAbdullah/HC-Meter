#!/usr/bin/env python3
"""Least-privilege containment execution boundary.

This module is an execution *broker*, not a platform implementation. It
accepts only an already validated plan plus a matching authorization result
and delegates to an explicitly injected adapter. The default adapter is
unavailable, so ordinary SYSWATCH execution cannot mutate host state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any


class ContainmentAdapter(Protocol):
    """Minimal capability surface for a future privileged adapter."""

    def apply(self, plan: dict[str, Any]) -> str: ...

    def rollback(self, token: str) -> bool: ...


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    actions_taken: bool
    security_verdict: str
    rollback_token: str | None = None
    reason: str | None = None


class UnavailableAdapter:
    """Safe default: never performs host mutation."""

    def apply(self, plan: dict[str, Any]) -> str:
        raise RuntimeError("privileged containment adapter is not implemented")

    def rollback(self, token: str) -> bool:
        raise RuntimeError("privileged containment adapter is not implemented")


def execute_authorized_plan(
    plan: dict[str, Any] | None,
    authorization: dict[str, Any] | None,
    *,
    adapter: ContainmentAdapter | None = None,
) -> ExecutionResult:
    """Execute only an explicitly authorized plan through an injected adapter.

    The default path is fail-closed. The broker itself performs no shell,
    firewall, process, socket, filesystem, or privilege operation.
    """
    if not isinstance(plan, dict) or plan.get("status") != "PLAN_ONLY":
        return ExecutionResult("REJECTED", False, "NONE", reason="invalid_plan")
    if not isinstance(authorization, dict):
        return ExecutionResult("REJECTED", False, "NONE", reason="missing_authorization")
    if authorization.get("status") != "AUTHORIZED_PLAN":
        return ExecutionResult("REJECTED", False, "NONE", reason="unauthorized_plan")
    if authorization.get("actions_taken") is not False:
        return ExecutionResult("REJECTED", False, "NONE", reason="invalid_authorization_state")
    if authorization.get("security_verdict") != "NONE":
        return ExecutionResult("REJECTED", False, "NONE", reason="invalid_security_state")
    if adapter is None:
        return ExecutionResult("UNAVAILABLE", False, "NONE", reason="privileged_adapter_not_configured")
    try:
        token = adapter.apply(plan)
    except Exception:
        return ExecutionResult("FAILED", False, "NONE", reason="adapter_apply_failed")
    if not isinstance(token, str) or not token.strip():
        return ExecutionResult("FAILED", False, "NONE", reason="invalid_rollback_token")
    return ExecutionResult("APPLIED", True, "NONE", rollback_token=token.strip())


def rollback_containment(token: str | None, *, adapter: ContainmentAdapter | None = None) -> ExecutionResult:
    """Rollback a previously applied containment action through the adapter."""
    if not isinstance(token, str) or not token.strip():
        return ExecutionResult("REJECTED", False, "NONE", reason="invalid_rollback_token")
    if adapter is None:
        return ExecutionResult("UNAVAILABLE", False, "NONE", reason="privileged_adapter_not_configured")
    try:
        restored = adapter.rollback(token.strip())
    except Exception:
        return ExecutionResult("FAILED", False, "NONE", reason="adapter_rollback_failed")
    if restored is not True:
        return ExecutionResult("FAILED", False, "NONE", reason="rollback_not_confirmed")
    return ExecutionResult("ROLLED_BACK", True, "NONE")
