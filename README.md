# SYSWATCH PRO

**Local-first host security agent and security operations dashboard for Linux.**

SYSWATCH combines continuous host telemetry, deterministic security checks, behavioral correlation and a persistent causal-analysis layer. It is designed to become an installable endpoint-security product without requiring a cloud account.

## Current product

- **Security Operations dashboard** — live CPU, memory, disk, processes, listening endpoints, threat level, causal chains and event stream.
- **Causal detection agent** — correlates security signals inside a temporal window instead of treating alerts independently.
- **Persistent telemetry state** — behavioral events survive process restarts through a local JSON state store.
- **Continuous service** — systemd restarts the local API after failures.
- **Local-first** — dashboard binds to `127.0.0.1` by default.
- **Low dependency footprint** — Python standard library + existing Bash modules.
- **CLI signal bridge** — security modules can feed normalized signals into the agent.

## Architecture

```text
Linux host
  │
  ├── Collectors / existing security modules
  │      ├── process + resource telemetry
  │      ├── network / connection telemetry
  │      ├── file integrity
  │      ├── persistence / hardening
  │      └── malware indicators
  │
  ├── Agent correlation layer
  │      ├── temporal signal window
  │      ├── causal attack-chain detection
  │      ├── confidence scoring
  │      └── persistent event state
  │
  └── Local SOC dashboard
         ├── live host state
         ├── threat score / level
         ├── causal chains
         └── event stream
```

## Install

```bash
git clone https://github.com/BurhanAbdullah/Syswatch.git
cd Syswatch
sudo ./install.sh
```

Then open `http://127.0.0.1:8080`.

Commands:

```text
syswatch start
syswatch stop
syswatch restart
syswatch status
syswatch logs
syswatch open
```

## Feed the agent

```bash
syswatch-signal NEW-PORT "Port 2222 opened"
syswatch-signal REVERSE-SHELL "bash spawned by unexpected parent"
syswatch-signal CRON-PERSIST "new scheduled task"
```

Run a complete local correlation demonstration:

```bash
bash syswatch/agents/feed_signal.sh --demo
```

## Important security boundary

SYSWATCH does **not** claim 99.99% detection accuracy. Real endpoint-security effectiveness depends on operating system coverage, telemetry quality, adversarial testing, false-positive controls, kernel visibility, update cadence and independent evaluation. Automated destructive response is deliberately not enabled by default. Any future containment engine should be policy-driven, auditable, least-privilege and reversible where possible.

Do not expose the dashboard publicly without authentication and an explicit network-security policy.

## Security maturity roadmap

Systematic feature roadmap. Each capability must be implemented with least privilege, explicit data boundaries, deterministic tests, adversarial/regression tests where applicable, and CI verification before being marked complete.

- [x] Live historical graphs (session-local resource history)
- [x] Firewall intelligence (UFW/firewalld/nftables detection)
- [x] Wi-Fi security intelligence (interface/SSID/security/signal where OS exposes it)
- [x] Process lineage (bounded PID/PPID/executable/user/start-time telemetry; command lines excluded by default)
- [x] Behavioral baseline / host DNA (local descriptive baseline; no autonomous response)
- [ ] DNS/network reputation intelligence
- [ ] Filesystem behavioral monitoring
- [ ] Prediction engine
- [ ] Policy engine
- [ ] Safe reversible containment
- [ ] Tamper resistance
- [ ] Signed updates / supply chain
- [ ] Debian/RHEL packages + releases
- [ ] Cross-platform agents
- [ ] Independent security evaluation

Security gates for every feature: no fabricated telemetry, no unsafe default actions, local-first data handling, bounded resource use, input validation, regression tests, and CI green. Do not claim production EDR status until the remaining controls and independent evaluation are complete.

## Development

```bash
python3 syswatch/api/server.py
python3 -m pytest tests/test_causal_engine.py
```

The project is being developed incrementally; refer to the security maturity roadmap above for current and upcoming capabilities.

## License

See [LICENSE](LICENSE).
