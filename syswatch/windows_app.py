"""Windows desktop entrypoint for the SYSWATCH local operator console.

The Windows build reuses the same localhost API and UI while selecting the
read-only Windows telemetry backend. No firewall, process, service, registry,
or filesystem mutation is performed by this entrypoint.
"""

from __future__ import annotations

import sys
from pathlib import Path

from syswatch import platform_windows
from syswatch.api import server

server.cpu_percent = platform_windows.cpu_percent
server.memory_percent = platform_windows.memory_percent
server.ports = platform_windows.ports
server.network_interfaces = platform_windows.network_interfaces
server.wifi_security = platform_windows.wifi_security
server.firewall_health = platform_windows.firewall_health
server.ssh_health = platform_windows.ssh_health
server.load_metrics = platform_windows.load_metrics
server.process_lineage = platform_windows.process_lineage
server.metrics = platform_windows.metrics

# Linux-only collectors are not allowed to fail the Windows console. Keep the
# feature visible as unavailable until a native, independently validated
# implementation exists rather than fabricating telemetry.
def _unavailable(*args, **kwargs):
    return {
        "status": "UNAVAILABLE_ON_WINDOWS",
        "source": "windows_safe_boundary",
        "actions_taken": False,
        "security_verdict": "NONE",
    }

server.filesystem_behavior = _unavailable
server.run_scan = _unavailable

# In a PyInstaller one-file build, bundled static assets are extracted under
# _MEIPASS. The source-tree path remains the fallback for development runs.
bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
server.WEB = bundle_root / "web"

if __name__ == "__main__":
    print(f"SYSWATCH Windows dashboard: http://{server.HOST}:{server.PORT}")
    server.ThreadingHTTPServer((server.HOST, server.PORT), server.Handler).serve_forever()
