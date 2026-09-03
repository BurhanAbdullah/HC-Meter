import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "api"))

import server


def test_policy_evidence_uses_production_causal_confidence(monkeypatch):
    monkeypatch.setattr(server, "agent_summary", lambda: {
        "events": [
            {"type": "reverse_shell", "severity": "CRITICAL"},
            {"type": "outbound_c2", "severity": "HIGH"},
        ]
    })
    monkeypatch.setattr(server, "network_intelligence", lambda: {"connections": []})

    result = server.policy_evidence()

    assert result["status"] == "EVALUATED"
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"
    assert result["decisions"][0]["policy"] == "correlated_high_risk"
    assert result["decisions"][0]["recommendation"] == "ESCALATE"


def test_policy_evidence_clamps_supplied_confidence(monkeypatch):
    monkeypatch.setattr(server, "agent_summary", lambda: {
        "events": [{"type": "reverse_shell", "severity": "CRITICAL", "confidence": 9.0}]
    })
    monkeypatch.setattr(server, "network_intelligence", lambda: {"connections": []})

    captured = {}
    def capture(evidence):
        captured["evidence"] = evidence
        return {"status": "EVALUATED", "decisions": [], "actions_taken": False, "security_verdict": "NONE"}
    monkeypatch.setattr(server, "policy_evaluate", capture)

    server.policy_evidence()
    assert captured["evidence"][0]["confidence"] == 1.0


def test_policy_evidence_does_not_invoke_stateful_filesystem_collector(monkeypatch):
    monkeypatch.setattr(server, "agent_summary", lambda: {"events": []})
    monkeypatch.setattr(server, "network_intelligence", lambda: {"connections": []})
    monkeypatch.setattr(server, "filesystem_collect", lambda **_: (_ for _ in ()).throw(AssertionError("stateful filesystem collector must not run")))
    result = server.policy_evidence()
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"


def test_policy_evidence_fails_closed_when_engine_is_unavailable(monkeypatch):
    monkeypatch.setattr(server, "policy_evaluate", None)
    result = server.policy_evidence()
    assert result["status"] == "UNAVAILABLE"
    assert result["decisions"] == []
    assert result["actions_taken"] is False
    assert result["security_verdict"] == "NONE"
