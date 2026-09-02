# SYSWATCH adversarial validation plan

These scenarios are **synthetic telemetry tests**. They do not execute malware, exploit code, credential theft, persistence, or destructive payloads on a real host.

## Attack families covered

| Scenario | Synthetic signal sequence | Expected result |
|---|---|---|
| Reverse shell | `NEW-PORT` → `REVERSE-SHELL` | Command & Control correlation |
| Dropper + persistence | `REVERSE-SHELL` → `FILE-INTEG` → `CRON-PERSIST` | Persistence correlation |
| Privilege escalation | `REVERSE-SHELL` → `PRIVESC` | Privilege Escalation correlation |
| Credential access | `HONEYPOT` → `C2-CONNECT` | Credential Access correlation |
| Ransomware-like behavior | `FILE-INTEG`/mass-write telemetry → `C2-CONNECT` | Impact correlation when normalized to `mass_file_write` |
| Cryptominer | `C2-CONNECT` → abnormal CPU telemetry | Execution correlation when normalized to `high_cpu_alien` |
| SSH brute-force precursor | repeated SSH failures + new listener | Initial Access correlation |
| Multi-stage intrusion | port → shell → file write → persistence → SUID → honeypot → C2 | Multiple simultaneous chains |
| Noisy benign host | unrelated isolated signals | No chain should be raised |
| Out-of-window slow attack | signals separated beyond correlation window | No claim of detection; identifies a current coverage boundary |
| Restart/recovery | detect chain → restart agent → reload state | Chain/event state remains available |

## How to run

From a checkout of SYSWATCH:

```bash
python3 -m pytest -q tests/test_causal_engine.py tests/test_adversarial_attack_chains.py
```

Run the built-in demonstration:

```bash
bash syswatch/agents/feed_signal.sh --demo
```

## What a passing result means

A passing test proves that the deterministic correlation logic recognizes the synthetic signal pattern. It does **not** prove real-world malware detection accuracy, kernel-level visibility, zero false positives, or coverage of every attacker technique.

## Hard cases that require the next agent generation

The current engine is intentionally conservative and correlates normalized signals inside a short temporal window. The highest-value next tests are:

1. slow-and-low campaigns spanning hours or days;
2. parent/child process lineage and LOLBin-style execution;
3. encrypted or rapidly changing C2 destinations;
4. living-off-the-land activity with minimal filesystem changes;
5. signed-but-abused binaries and legitimate administrative tools;
6. namespace/container boundary abuse;
7. kernel/module/rootkit telemetry;
8. tamper attempts against the agent itself;
9. sensor loss and degraded telemetry;
10. false-positive testing on representative clean workloads.

These should be validated in isolated disposable VMs or dedicated security labs, never against systems without authorization.
