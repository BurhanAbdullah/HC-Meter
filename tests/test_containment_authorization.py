import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from containment import ContainmentRequest, plan_containment
from containment_authorization import (
    AuthorizationGrant,
    audit_event,
    authorize_plan,
    containment_plan_id,
)


def _plan():
    return plan_containment(ContainmentRequest("192.0.2.10", reason="test signal"))


def test_plan_id_is_stable():
    assert containment_plan_id(_plan()) == containment_plan_id(_plan())


def test_missing_authorization_fails_closed():
    result = authorize_plan(_plan(), None, now=100)
    assert result["status"] == "REJECTED"
    assert result["reason"] == "missing_authorization"
    assert result["actions_taken"] is False


def test_mismatched_plan_cannot_be_authorized():
    plan = _plan()
    grant = AuthorizationGrant("g-1", "wrong", approved_by="operator", expires_at=200)
    result = authorize_plan(plan, grant, now=100)
    assert result["status"] == "REJECTED"
    assert result["reason"] == "plan_mismatch"


def test_expired_grant_fails_closed():
    plan = _plan()
    grant = AuthorizationGrant("g-1", containment_plan_id(plan), approved_by="operator", expires_at=99)
    result = authorize_plan(plan, grant, now=100)
    assert result["status"] == "REJECTED"
    assert result["reason"] == "authorization_expired"


def test_valid_grant_produces_authorized_plan_without_action():
    plan = _plan()
    grant = AuthorizationGrant("g-1", containment_plan_id(plan), approved_by="operator", expires_at=200)
    result = authorize_plan(plan, grant, now=100)
    assert result["status"] == "AUTHORIZED_PLAN"
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"
    assert result["privileged_adapter"] == "NOT_IMPLEMENTED"


def test_wrong_scope_fails_closed():
    plan = _plan()
    grant = AuthorizationGrant("g-1", containment_plan_id(plan), scope="containment:unknown", approved_by="operator", expires_at=200)
    result = authorize_plan(plan, grant, now=100)
    assert result["status"] == "REJECTED"
    assert result["reason"] == "invalid_scope"


def test_audit_event_is_deterministic_and_non_mutating():
    plan = _plan()
    grant = AuthorizationGrant("g-1", containment_plan_id(plan), approved_by="operator", expires_at=200)
    authorization = authorize_plan(plan, grant, now=100)
    first = audit_event(plan, authorization)
    second = audit_event(plan, authorization)
    assert first == second
    assert first["actions_taken"] is False
    assert first["security_verdict"] == "NONE"
    assert first["event"] == "CONTAINMENT_AUTHORIZATION"
