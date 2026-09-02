# SYSWATCH PRO

**Local-first Linux host security agent and Security Operations dashboard.**

SYSWATCH collects host telemetry, normalizes security signals, correlates related activity in time, and presents the resulting attack chains locally. The project is being built as a real installable endpoint-security product, with conservative defaults and an explicit distinction between tested capabilities and future capabilities.

> **Important:** SYSWATCH is security monitoring software, not a guarantee of complete protection. The current release has deterministic signal correlation and a local dashboard. Independent endpoint-security evaluation is still required before making claims about broad malware coverage or detection rates.

## What SYSWATCH does today

- Live local SOC dashboard for host state, processes, network endpoints, threat score, causal chains, and event stream.
- Deterministic temporal correlation of normalized security signals.
- Persistent local agent state across process restarts.
- Security-signal CLI bridge for existing collectors/modules.
- systemd service with automatic restart after failure.
- Localhost-only dashboard by default (`127.0.0.1:8080`).
- Low dependency footprint: Python standard library plus existing shell modules.
- Synthetic adversarial test suite covering multi-stage and noisy attack patterns.

## Architecture

```text
Linux endpoint
   │
   ├── Collectors / sensors
   │     ├── process + resource telemetry
   │     ├── network / listening endpoints
   │     ├── file-integrity events
   │     ├── persistence / hardening events
   │     └── malware / honeypot indicators
   │
   ├── Signal normalization
   │     └── NEW-PORT, REVERSE-SHELL, FILE-INTEG, CRON-PERSIST,
   │         C2-CONNECT, HONEYPOT, PRIVESC, etc.
   │
   ├── Causal correlation engine
   │     ├── temporal window
   │     ├── multi-signal attack chains
   │     ├── confidence scoring
   │     └── persistent state
   │
   └── Local SOC dashboard
         ├── host health
         ├── threat level
         ├── causal chains
         └── event stream
```

## Installation — easiest method

### Requirements

A Linux machine with:

- `git`
- `python3`
- `systemd`
- root/sudo access

Debian/Ubuntu example:

```bash
sudo apt update
sudo apt install -y git python3
```

### Install SYSWATCH

```bash
git clone https://github.com/BurhanAbdullah/Syswatch.git
cd Syswatch
sudo ./install.sh
```

The installer places the application under `/opt/syswatch`, creates the `syswatch` command, installs a systemd service, enables it at boot, and starts it.

Open the dashboard locally:

```text
http://127.0.0.1:8080
```

Or:

```bash
syswatch open
```

### Verify the installation

```bash
syswatch status
syswatch logs
```

You can also verify the HTTP endpoint without opening a browser:

```bash
curl -fsS http://127.0.0.1:8080/api/health
```

## Daily use

```bash
syswatch start
syswatch stop
syswatch restart
syswatch status
syswatch logs
syswatch open
```

The service is intended to run continuously. If it exits unexpectedly, systemd restarts it.

## Feed security events into the agent

Security collectors can send normalized signals through the CLI bridge:

```bash
syswatch-signal NEW-PORT "Port 2222 opened"
syswatch-signal REVERSE-SHELL "unexpected shell process"
syswatch-signal FILE-INTEG "/tmp/.implant written"
syswatch-signal CRON-PERSIST "new scheduled task"
syswatch-signal C2-CONNECT "unexpected outbound endpoint"
syswatch-signal HONEYPOT "credential backup accessed"
syswatch-signal PRIVESC "new SUID executable"
```

The bridge maps the human-readable signal names to the normalized event types used by the correlation engine.

## Try the safe built-in demo

The demo injects synthetic security telemetry only; it does not attack the host.

```bash
cd /opt/syswatch
bash syswatch/agents/feed_signal.sh --demo
```

Then refresh the dashboard. You should see correlated activity rather than isolated alerts.

For development checkouts:

```bash
bash syswatch/agents/feed_signal.sh --demo
python3 -m pytest -q tests/test_causal_engine.py tests/test_adversarial_attack_chains.py
```

## Adversarial validation

SYSWATCH now has synthetic tests for:

- reverse-shell establishment;
- persistence after initial access;
- privilege-escalation indicators;
- credential-access indicators;
- ransomware-like mass-write + C2 correlation;
- cryptominer-like C2 + abnormal CPU correlation;
- SSH brute-force precursor patterns;
- signal-order variation;
- noisy benign telemetry;
- correlation-window expiry;
- state persistence after restart;
- multi-stage attacks producing multiple simultaneous chains.

See [`tests/adversarial_scenarios.md`](tests/adversarial_scenarios.md) for the validation matrix and known hard cases.

These tests are **not** proof of real-world detection accuracy. They validate the correlation engine against controlled telemetry patterns. Real adversarial validation must use isolated, authorized security labs and representative clean workloads.

## Current detection boundary

The current correlation engine is deliberately conservative. It recognizes normalized signal combinations inside a short temporal window. Therefore, a sophisticated slow-and-low intrusion whose relevant signals are separated beyond that window may not currently correlate. That is a known product gap, not something SYSWATCH should pretend to solve.

The next major security-engineering milestones are:

1. behavioral baseline / host DNA;
2. process parent-child lineage;
3. prediction of likely next signals;
4. richer network and DNS telemetry;
5. filesystem behavioral monitoring;
6. policy-driven containment that is reversible and auditable;
7. tamper resistance and sensor-health monitoring;
8. signed updates and supply-chain verification;
9. Debian/Ubuntu/RHEL-family packaging and release validation;
10. broader cross-platform agent support;
11. independent red-team and false-positive evaluation.

## Security model and safe defaults

- Dashboard binds to localhost by default.
- No destructive automated response is enabled by default.
- Future containment must be policy-driven, least-privilege, auditable, and reversible where practical.
- Do not expose the dashboard publicly without authentication and an explicit network-security design.
- Do not run adversarial tests against systems you do not own or have authorization to test.

## Uninstall

If installed using `install.sh`:

```bash
sudo /opt/syswatch/uninstall.sh
```

Or:

```bash
sudo syswatch uninstall
```

## Development

Run the API directly:

```bash
python3 syswatch/api/server.py
```

Run the complete current test set:

```bash
python3 -m pytest -q
```

## Project status

SYSWATCH is under active development toward a production endpoint-security platform. The repository documents implemented behavior separately from planned capabilities so users can evaluate the product honestly.

## License

See [`LICENSE`](LICENSE).
