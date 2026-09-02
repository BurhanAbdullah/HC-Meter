# SYSWATCH PRO

**Local-first host security monitoring and intrusion detection for Linux.**

SYSWATCH PRO turns the existing modular security engine into a usable product: one-command installation, a local web application, continuous background monitoring, live host metrics, network visibility, and on-demand security scans. The core project remains modular and extensible.

## What users get

- **Live dashboard** — CPU, memory, disk, process count, host identity and listening endpoints.
- **Security scan** — runs the existing SYSWATCH security engine from the dashboard.
- **Continuous service** — systemd keeps SYSWATCH running and restarts it after failures.
- **Local-first** — dashboard is bound to `127.0.0.1` by default; no account or cloud service is required.
- **Installable app** — Debian packages can be built from tagged releases, and the repository includes a one-command installer.
- **PWA shell** — the dashboard can be installed from a compatible browser and retains its application shell offline.

The underlying engine covers system monitoring, suspicious-process detection, network analysis, hardening checks, file-integrity monitoring, environment awareness and threat assessment.

## Install from source

```bash
git clone https://github.com/BurhanAbdullah/Syswatch.git
cd Syswatch
sudo ./install.sh
```

Then open **http://127.0.0.1:8080**.

Useful commands:

```text
syswatch start
syswatch stop
syswatch restart
syswatch status
syswatch logs
syswatch open
```

## Install from a Debian release

Download the `.deb` package from the repository's Releases page and install it with:

```bash
sudo apt install ./syswatch_<version>_amd64.deb
```

The package installs the background service and the `syswatch` command. The dashboard is available at `http://127.0.0.1:8080`.

## Product architecture

```text
Linux host
   │
   ├── SYSWATCH engine (existing modular Bash modules)
   │       ├── system / process monitoring
   │       ├── network analysis
   │       ├── hardening inspection
   │       ├── file integrity
   │       └── threat assessment
   │
   └── Local API + Web App (Python stdlib)
           ├── live metrics
           ├── listening endpoints
           └── on-demand security scan
```

The web application is intentionally dependency-light: the server uses Python's standard library, while the dashboard is plain HTML/CSS/JavaScript. This makes the local deployment small and easy to audit.

## Security model

SYSWATCH is a monitoring and auditing product, not a replacement for an endpoint protection platform. The default dashboard binds to localhost. Review service permissions and hardening settings before deploying it to production servers, and do not expose port 8080 publicly without an authenticated reverse proxy and an explicit security policy.

## Development

Run the dashboard directly:

```bash
python3 syswatch/api/server.py
```

Open `http://127.0.0.1:8080` and use **Run security scan** to exercise the existing engine.

## License

See [LICENSE](LICENSE).
