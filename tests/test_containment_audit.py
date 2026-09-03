import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))

from containment_audit import ContainmentAuditLedger, GENESIS


def test_empty_ledger_is_valid():
    ledger = ContainmentAuditLedger()
    assert ledger.verify()
    assert ledger.export() == ()


def test_entries_form_deterministic_hash_chain():
    ledger = ContainmentAuditLedger(max_entries=2)
    first = ledger.append(
        event="CONTAINMENT_AUTHORIZATION", plan_id="p1", grant_id="g1",
        status="AUTHORIZED_PLAN", actions_taken=False, timestamp=100,
    )
    second = ledger.append(
        event="CONTAINMENT_APPLY", plan_id="p1", grant_id="g1",
        status="APPLIED", actions_taken=True, timestamp=101,
    )
    assert first.sequence == 0
    assert first.previous_hash == GENESIS
    assert second.sequence == 1
    assert second.previous_hash == first.entry_hash
    assert ledger.verify()


def test_export_is_value_based_and_tampering_is_detected():
    ledger = ContainmentAuditLedger()
    ledger.append(
        event="CONTAINMENT_AUTHORIZATION", plan_id="p1", grant_id="g1",
        status="AUTHORIZED_PLAN", actions_taken=False, timestamp=100,
    )
    exported = list(ledger.export())
    exported[0]["status"] = "APPLIED"
    assert ledger.verify()
    tampered = dict(ledger.entries[0].as_dict())
    tampered["status"] = "APPLIED"
    assert tampered["entry_hash"] == ledger.entries[0].entry_hash
    assert not ledger.verify([type(ledger.entries[0])(**tampered)])


def test_full_ledger_fails_closed_instead_of_dropping_history():
    ledger = ContainmentAuditLedger(max_entries=1)
    ledger.append(
        event="CONTAINMENT_AUTHORIZATION", plan_id="p1", grant_id="g1",
        status="AUTHORIZED_PLAN", actions_taken=False, timestamp=100,
    )
    try:
        ledger.append(
            event="CONTAINMENT_APPLY", plan_id="p1", grant_id="g1",
            status="APPLIED", actions_taken=True, timestamp=101,
        )
    except RuntimeError as exc:
        assert str(exc) == "containment audit ledger capacity reached"
    else:
        raise AssertionError("capacity exhaustion must fail closed")
    assert len(ledger.entries) == 1
    assert ledger.verify()


def test_fields_and_boolean_state_are_strictly_bounded():
    ledger = ContainmentAuditLedger()
    for kwargs in (
        {"event": "", "plan_id": "p", "grant_id": "g", "status": "S", "actions_taken": False, "timestamp": 1},
        {"event": "E", "plan_id": "p", "grant_id": "g", "status": "S", "actions_taken": 1, "timestamp": 1},
        {"event": "E", "plan_id": "p", "grant_id": "g", "status": "S", "actions_taken": False, "timestamp": -1},
    ):
        try:
            ledger.append(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid audit input must fail closed")
