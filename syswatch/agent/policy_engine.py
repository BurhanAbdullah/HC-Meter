#!/usr/bin/env python3
"""Deterministic, local-only policy evaluation over existing evidence.

This module produces auditable recommendations only. It never executes commands,
mutates host state, contacts external services, or performs containment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

MAX_EVIDENCE = 256
MAX_POLICIES = 64
MAX_SIGNALS_PER_POLICY = 32
ALLOWED_ACTIONS = {"NONE", "REVIEW", "ESCALATE"}
SEVERITIES = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass(frozen=True)
class Policy:
    name: str
    required_signals: frozenset[str]
    min_severity: int = 0
    min_confidence: float = 0.0
    recommendation: str = "REVIEW"


DEFAULT_POLICIES = (
    Policy(
        "correlated_high_risk",
        frozenset({"reverse_shell", "outbound_c2"}),
        min_severity=SEVERITIES["HIGH"],
        min_confidence=0.60,
        recommendation="ESCALATE",
    ),
    Policy(
        "persistence_change",
        frozenset({"cron_change", "file_write_tmp"}),
        min_severity=SEVERITIES["MEDIUM"],
        min_confidence=0.50,
        recommendation="REVIEW",
    ),
)


def _normalise_signal(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip().lower()
    return value[:80]


def _normalise_evidence(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    signal = _normalise_signal(item.get("type") or item.get("signal"))
    if not signal:
        return None
    severity = str(item.get("severity", "INFO")).upper()
    if severity not in SEVERITIES:
        severity = "INFO"
    try:
        confidence = float(item.get("confidence", 1.0))
    except (TypeError, ValueError):
        confidence = 0.0
    if not 0.0 <= confidence <= 1.0:
        confidence = max(0.0, min(1.0, confidence))
    return {
        "type": signal,
        "severity": severity,
        "confidence": confidence,
        "source": str(item.get("source", "unknown"))[:80],
    }


def evaluate(evidence: Iterable[dict[str, Any]] | None, policies: Iterable[Policy] | None = None) -> dict[str, Any]:
    """Evaluate bounded evidence against declarative policies without side effects."""
    evidence = list(evidence or [])[:MAX_EVIDENCE]
    clean = [x for x in (_normalise_evidence(item) for item in evidence) if x]
    selected = tuple(policies or DEFAULT_POLICIES)[:MAX_POLICIES]
    decisions: list[dict[str, Any]] = []

    for policy in selected:
        required = frozenset(_normalise_signal(x) for x in policy.required_signals)
        if not required or len(required) > MAX_SIGNALS_PER_POLICY:
            continue
        matched = [x for x in clean if x["type"] in required]
        present = {x["type"] for x in matched}
        if not required.issubset(present):
            continue
        qualifying = [x for x in matched if SEVERITIES[x["severity"]] >= policy.min_severity and x["confidence"] >= policy.min_confidence]
        if len({x["type"] for x in qualifying}) != len(required):
            continue
        confidence = round(sum(x["confidence"] for x in qualifying) / len(qualifying), 3)
        recommendation = policy.recommendation if policy.recommendation in ALLOWED_ACTIONS else "REVIEW"
        decisions.append({
            "policy": policy.name[:80],
            "matched_signals": sorted(present),
            "confidence": confidence,
            "recommendation": recommendation,
            "actions_taken": False,
        })

    decisions.sort(key=lambda x: (-x["confidence"], x["policy"]))
    return {
        "status": "EVALUATED",
        "source": "local_evidence",
        "evidence_count": len(clean),
        "decisions": decisions,
        "actions_taken": False,
        "security_verdict": "NONE",
    }
