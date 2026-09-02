#!/usr/bin/env python3
"""Read-only, local-first network and DNS intelligence.

This module deliberately performs no outbound reputation lookup. It classifies
observed endpoints using local IP address semantics and reports configured DNS
servers from /etc/resolv.conf. Public endpoints remain UNASSESSED unless a
future, explicitly configured reputation provider is added.
"""

import ipaddress
import re
import subprocess
from pathlib import Path


_ENDPOINT_RE = re.compile(r"^(?P<host>\[[^\]]+\]|[^:]+):(?P<port>\d+)$")


def _strip_brackets(host):
    return host[1:-1] if host.startswith("[") and host.endswith("]") else host


def parse_endpoint(value):
    """Parse an ss -n endpoint into host and integer port, or return None."""
    match = _ENDPOINT_RE.match(value.strip())
    if not match:
        return None
    host = _strip_brackets(match.group("host"))
    try:
        return host, int(match.group("port"))
    except ValueError:
        return None


def classify_ip(value):
    """Return a conservative local classification for an IP address."""
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return {"classification": "INVALID", "scope": "unknown", "assessed": False}
    if ip.is_loopback:
        return {"classification": "LOOPBACK", "scope": "local", "assessed": True}
    if ip.is_link_local:
        return {"classification": "LINK_LOCAL", "scope": "local", "assessed": True}
    if ip.is_private:
        return {"classification": "PRIVATE", "scope": "local", "assessed": True}
    if ip.is_multicast:
        return {"classification": "MULTICAST", "scope": "local", "assessed": True}
    if ip.is_reserved or ip.is_unspecified:
        return {"classification": "RESERVED", "scope": "special", "assessed": True}
    return {"classification": "PUBLIC_UNASSESSED", "scope": "public", "assessed": False}


def parse_resolv_conf(text):
    """Extract nameserver addresses without resolving or contacting them."""
    servers = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or not line.startswith("nameserver"):
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            ipaddress.ip_address(parts[1])
        except ValueError:
            continue
        if parts[1] not in servers:
            servers.append(parts[1])
    return servers[:8]


def parse_ss_output(text, limit=200):
    """Parse numeric ss output into bounded endpoint observations."""
    observations = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        local = parse_endpoint(fields[4])
        peer = parse_endpoint(fields[5])
        if not local or not peer:
            continue
        peer_host, peer_port = peer
        local_host, local_port = local
        peer_class = classify_ip(peer_host)
        observations.append({
            "transport": fields[0].lower(),
            "state": fields[1],
            "local": {"address": local_host, "port": local_port},
            "peer": {"address": peer_host, "port": peer_port},
            "peer_classification": peer_class["classification"],
            "peer_scope": peer_class["scope"],
            "reputation_assessed": peer_class["assessed"],
        })
        if len(observations) >= limit:
            break
    return observations


def _run_ss():
    try:
        return subprocess.check_output(
            ["ss", "-H", "-n", "-t", "-u"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return ""


def collect(resolv_path="/etc/resolv.conf", ss_text=None):
    """Collect local network intelligence with bounded, read-only inputs."""
    try:
        resolv_text = Path(resolv_path).read_text(errors="ignore")
    except OSError:
        resolv_text = ""
    raw = _run_ss() if ss_text is None else ss_text
    endpoints = parse_ss_output(raw)
    public = sum(1 for e in endpoints if e["peer_scope"] == "public")
    return {
        "source": "local-os",
        "reputation_provider": "none",
        "reputation_boundary": "Public endpoints are classified but not remotely reputation-scored.",
        "dns": {"nameservers": parse_resolv_conf(resolv_text)},
        "connections": endpoints,
        "summary": {
            "connections": len(endpoints),
            "public_unassessed": public,
            "local_or_special": len(endpoints) - public,
        },
    }
