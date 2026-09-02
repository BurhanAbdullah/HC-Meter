#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
HOST = os.environ.get("SYSWATCH_HOST", "127.0.0.1")
PORT = int(os.environ.get("SYSWATCH_PORT", "8080"))


def cpu_percent():
    def read():
        with open("/proc/stat", "r", encoding="utf-8") as f:
            vals = list(map(int, f.readline().split()[1:8]))
        return vals[0] + vals[1] + vals[2] + vals[3], vals[3]
    a = read(); time.sleep(0.08); b = read()
    total = b[0] - a[0]
    idle = b[1] - a[1]
    return round((1 - idle / total) * 100, 1) if total else 0.0


def memory_percent():
    total = available = 0
    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            key, value, *_ = line.split()
            if key == "MemTotal:": total = int(value)
            elif key == "MemAvailable:": available = int(value)
    return round((1 - available / total) * 100, 1) if total else 0.0


def process_count():
    return sum(1 for p in Path("/proc").iterdir() if p.name.isdigit())


def ports():
    try:
        out = subprocess.check_output(["ss", "-H", "-lntup"], text=True, stderr=subprocess.DEVNULL, timeout=2)
        return out.splitlines()[:100]
    except (FileNotFoundError, subprocess.SubprocessError):
        return []


def metrics():
    disk = shutil.disk_usage("/")
    return {
        "cpu": cpu_percent(),
        "memory": memory_percent(),
        "disk": round(disk.used / disk.total * 100, 1),
        "disk_free_gb": round(disk.free / 1024**3, 2),
        "processes": process_count(),
        "ports": ports(),
        "hostname": os.uname().nodename,
        "platform": os.uname().sysname + " " + os.uname().release,
        "timestamp": int(time.time()),
    }


def run_scan():
    engine = ROOT / "core" / "engine.sh"
    if not engine.exists():
        return {"ok": False, "error": "Security engine not found"}
    try:
        p = subprocess.run(["bash", str(engine)], cwd=str(ROOT), text=True, capture_output=True, timeout=60)
        return {"ok": p.returncode == 0, "exit_code": p.returncode, "output": (p.stdout + p.stderr)[-12000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Scan timed out after 60 seconds"}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self.send_json({"ok": True, "service": "syswatch"})
        if path == "/api/metrics":
            return self.send_json(metrics())
        if path == "/api/scan":
            return self.send_json(run_scan())
        if path == "/metrics":
            return self.send_json(metrics())
        if path == "/" or path == "/index.html":
            return self.serve_file(WEB / "index.html", "text/html; charset=utf-8")
        if path == "/manifest.webmanifest":
            return self.serve_file(WEB / "manifest.webmanifest", "application/manifest+json")
        if path == "/sw.js":
            return self.serve_file(WEB / "sw.js", "application/javascript")
        if path == "/icon.svg":
            return self.serve_file(WEB / "icon.svg", "image/svg+xml")
        self.send_error(404)

    def serve_file(self, path, content_type):
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            return self.send_error(404)
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print("[SYSWATCH] " + fmt % args)


if __name__ == "__main__":
    print(f"SYSWATCH PRO dashboard: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
