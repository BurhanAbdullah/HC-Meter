import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from policy_engine import Policy, evaluate


def test_correlated_policy_is_deterministic_and_non_destructive():
    evidence = [
        {"type": "outbound_c2", "severity": "HIGH", "confidence": 0.8, "source": "network"},
        {"type": "reverse_shell", "severity": "CRITICAL", "confidence": 0.9, "source": "process"},
    ]
    first = evaluate(evidence)
    second = evaluate(list(reversed(evidence)))
    assert first == second
    assert first["actions_taken"] is False
    assert first["security_verdict"] == "NONE"
    assert first["decisions"][0]["recommendation"] == "ESCALATE"


def test_missing_signal_does_not_trigger_policy():
    result = evaluate([{"type": "reverse_shell", "severity": "CRITICAL", "confidence": 1.0}])
    assert result["decisions"] == []


def test_invalid_evidence_is_ignored_without_failure():
    result = evaluate([None, {}, {"type": 123}, {"type": "unknown", "severity": "bogus", "confidence": "nan"}])
    assert result["status"] == "EVALUATED"
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"


def test_bounds_and_invalid_recommendation_are_safe():
    policy = Policy("bounded", frozenset({"signal"}), recommendation="DELETE")
    evidence = [{"type": "signal", "severity": "LOW", "confidence": 1.0}]
    result = evaluate(evidence, [policy])
    assert result["decisions"][0]["recommendation"] == "REVIEW"
    assert result["evidence_count"] == 1


def test_non_finite_confidence_is_clamped_safely():
    result = evaluate([{"type": "signal", "severity": "HIGH", "confidence": float("inf")}], [
        Policy("signal_policy", frozenset({"signal"}), min_severity=3, min_confidence=0.0)
    ])
    assert result["decisions"][0]["confidence"] == 1.0
