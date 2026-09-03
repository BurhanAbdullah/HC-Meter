import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from containment import ContainmentRequest, plan_containment


def test_valid_request_is_plan_only_and_reversible():
    result = plan_containment(ContainmentRequest("192.0.2.10", reason="test signal"))
    assert result["status"] == "PLAN_ONLY"
    assert result["action"] == "BLOCK_EGRESS"
    assert result["reversible"] is True
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"
    assert result["authorization_required"] is True
    assert result["privileged_adapter"] == "NOT_IMPLEMENTED"


def test_invalid_target_fails_closed():
    result = plan_containment({"target": "not-an-ip"})
    assert result["status"] == "REJECTED"
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"


def test_unsupported_target_kind_fails_closed():
    result = plan_containment({"target": "192.0.2.10", "kind": "process"})
    assert result["status"] == "REJECTED"
    assert result["authorization_required"] is True


def test_reason_is_bounded():
    result = plan_containment({"target": "2001:db8::1", "reason": "x" * 1000})
    assert result["status"] == "PLAN_ONLY"
    assert len(result["reason"]) == 240


def test_no_request_fails_closed():
    result = plan_containment(None)
    assert result["status"] == "REJECTED"
    assert result["actions_taken"] is False
