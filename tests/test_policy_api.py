import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "api"))

import server


def test_policy_evidence_uses_bounded_causal_and_network_inputs(monkeypatch):
    monkeypatch.setattr(server, "agent_summary", lambda: {
        "events": [
            {"type": "reverse_shell", "severity": "CRITICAL", "confidence": 0.9},
            {"type": "outbound_c2", "severity": "HIGH", "confidence": 0.8},
        ]
    })
    monkeypatch.setattr(server, "network_intelligence", lambda: {
        "connections": [{"remote": "203.0.113.10:443"}]
    })
    monkeypatch.setattr(server, "filesystem_collect", lambda **_: (_ for _ in ()).throw(AssertionError("stateful filesystem collector must not run")))

    result = server.policy_evidence()

    assert result["status"] == "EVALUATED"
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"
    assert result["decisions"][0]["policy"] == "correlated_high_risk"
    assert result["decisions"][0]["recommendation"] == "ESCALATE"


def test_policy_evidence_fails_closed_when_engine_is_unavailable(monkeypatch):
    monkeypatch.setattr(server, "policy_evaluate", None)
    result = server.policy_evidence()
    assert result["status"] == "UNAVAILABLE"
    assert result["decisions"] == []
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"
