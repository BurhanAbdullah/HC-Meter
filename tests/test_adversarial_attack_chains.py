import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "syswatch" / "agent"))
from causal_engine import Engine


def engine(tmp_path, window=120):
    return Engine(tmp_path / "state.json", window=window)


def feed(e, *signals):
    for signal in signals:
        e.ingest(signal, f"synthetic adversarial test: {signal}")
    return e.summary()


def test_reverse_shell_chain(tmp_path):
    s = feed(engine(tmp_path), "new_port", "reverse_shell")
    assert "reverse_shell" in {c["name"].lower().replace(" ", "_") for c in s["chains"]}
    assert s["level"] in ("HIGH", "CRITICAL")


def test_persistence_chain(tmp_path):
    s = feed(engine(tmp_path), "reverse_shell", "file_write_tmp", "cron_change")
    assert any(c["stage"] == "Persistence" for c in s["chains"])


def test_privilege_escalation_chain(tmp_path):
    s = feed(engine(tmp_path), "reverse_shell", "new_suid")
    assert any(c["stage"] == "Privilege Escalation" for c in s["chains"])


def test_credential_access_chain(tmp_path):
    s = feed(engine(tmp_path), "honeypot_access", "outbound_c2")
    assert any(c["stage"] == "Credential Access" for c in s["chains"])


def test_ransomware_chain(tmp_path):
    s = feed(engine(tmp_path), "mass_file_write", "outbound_c2")
    assert any(c["stage"] == "Impact" for c in s["chains"])


def test_cryptominer_chain(tmp_path):
    s = feed(engine(tmp_path), "outbound_c2", "high_cpu_alien")
    assert any(c["stage"] == "Execution" for c in s["chains"])


def test_bruteforce_chain(tmp_path):
    s = feed(engine(tmp_path), "ssh_failure", "new_port")
    assert any(c["stage"] == "Initial Access" for c in s["chains"])


def test_signal_order_does_not_matter(tmp_path):
    s = feed(engine(tmp_path), "cron_change", "new_port", "reverse_shell", "file_write_tmp")
    assert any(c["stage"] == "Persistence" for c in s["chains"])


def test_unrelated_noise_does_not_create_chain(tmp_path):
    s = feed(engine(tmp_path), "file_write_tmp", "high_cpu_alien")
    assert not s["chains"]


def test_chain_expires_after_window(tmp_path):
    e = engine(tmp_path, window=10)
    e.ingest("new_port", "old port")
    e.ingest("reverse_shell", "old shell")
    assert e.summary()["chains"]
    for event in e.events:
        event["ts"] = time.time() - 30
    e.evaluate()
    assert not e.summary()["chains"]


def test_state_persists_across_restart(tmp_path):
    state = tmp_path / "state.json"
    first = Engine(state)
    first.ingest("new_port", "2222")
    first.ingest("reverse_shell", "bash")
    second = Engine(state)
    assert second.summary()["chains"]
    assert len(second.summary()["events"]) >= 2


def test_multi_stage_attack_produces_multiple_correlations(tmp_path):
    s = feed(
        engine(tmp_path),
        "new_port",
        "reverse_shell",
        "file_write_tmp",
        "cron_change",
        "new_suid",
        "honeypot_access",
        "outbound_c2",
    )
    stages = {c["stage"] for c in s["chains"]}
    assert {"Command & Control", "Persistence", "Privilege Escalation", "Credential Access"} <= stages


def test_slow_low_attack_outside_window_is_not_claimed_detected(tmp_path):
    e = engine(tmp_path, window=10)
    e.ingest("new_port", "day 1")
    for event in e.events:
        event["ts"] = time.time() - 20
    e.ingest("reverse_shell", "day 2")
    assert not any(c["stage"] == "Command & Control" for c in e.summary()["chains"])
