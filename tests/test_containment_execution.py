import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from containment import ContainmentRequest, plan_containment
from containment_authorization import authorize_plan, containment_plan_id, AuthorizationGrant
from containment_execution import execute_authorized_plan, rollback_containment


def _authorized():
    plan = plan_containment(ContainmentRequest("192.0.2.10", reason="test"))
    grant = AuthorizationGrant("g-1", containment_plan_id(plan), approved_by="operator", expires_at=200)
    auth = authorize_plan(plan, grant, now=100)
    return plan, auth


def test_default_execution_is_fail_closed_without_adapter():
    plan, auth = _authorized()
    result = execute_authorized_plan(plan, auth)
    assert result.status == "UNAVAILABLE"
    assert result.actions_taken is False
    assert result.security_verdict == "NONE"


def test_missing_or_invalid_authorization_cannot_reach_adapter():
    plan, _ = _authorized()

    class ExplodingAdapter:
        def apply(self, _plan):
            raise AssertionError("adapter must not be reached")

        def rollback(self, _token):
            raise AssertionError("adapter must not be reached")

    for authorization in (None, {}, {"status": "REJECTED", "actions_taken": False, "security_verdict": "NONE"}):
        result = execute_authorized_plan(plan, authorization, adapter=ExplodingAdapter())
        assert result.status == "REJECTED"
        assert result.actions_taken is False


def test_non_boolean_action_state_fails_closed():
    plan, auth = _authorized()
    auth = dict(auth)
    auth["actions_taken"] = True
    result = execute_authorized_plan(plan, auth)
    assert result.status == "REJECTED"
    assert result.reason == "invalid_authorization_state"


def test_adapter_success_requires_nonempty_rollback_token():
    plan, auth = _authorized()

    class Adapter:
        def apply(self, _plan):
            return " rollback-1 "

        def rollback(self, token):
            return token == "rollback-1"

    result = execute_authorized_plan(plan, auth, adapter=Adapter())
    assert result.status == "APPLIED"
    assert result.actions_taken is True
    assert result.rollback_token == "rollback-1"


def test_empty_rollback_token_is_not_accepted():
    plan, auth = _authorized()

    class Adapter:
        def apply(self, _plan):
            return "  "

        def rollback(self, _token):
            return True

    result = execute_authorized_plan(plan, auth, adapter=Adapter())
    assert result.status == "FAILED"
    assert result.actions_taken is False
    assert result.reason == "invalid_rollback_token"


def test_apply_failure_does_not_report_action_taken():
    plan, auth = _authorized()

    class Adapter:
        def apply(self, _plan):
            raise OSError("permission denied")

        def rollback(self, _token):
            return True

    result = execute_authorized_plan(plan, auth, adapter=Adapter())
    assert result.status == "FAILED"
    assert result.actions_taken is False


def test_rollback_is_fail_closed_without_adapter():
    result = rollback_containment("rollback-1")
    assert result.status == "UNAVAILABLE"
    assert result.actions_taken is False


def test_rollback_requires_positive_confirmation():
    class Adapter:
        def apply(self, _plan):
            return "rollback-1"

        def rollback(self, _token):
            return False

    result = rollback_containment("rollback-1", adapter=Adapter())
    assert result.status == "FAILED"
    assert result.reason == "rollback_not_confirmed"
    assert result.actions_taken is False
