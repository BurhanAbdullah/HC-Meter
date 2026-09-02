import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("syswatch_server", ROOT / "syswatch" / "api" / "server.py")
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


def test_local_hosts_are_allowed():
    assert server.host_is_local("127.0.0.1:8080")
    assert server.host_is_local("localhost:8080")
    assert server.host_is_local("[::1]:8080")


def test_rebinding_style_hosts_are_rejected():
    assert not server.host_is_local("evil.example")
    assert not server.host_is_local("evil.example:8080")
    assert not server.host_is_local("")


def test_local_or_absent_origin_is_allowed():
    assert server.origin_is_local(None)
    assert server.origin_is_local("http://127.0.0.1:8080")
    assert server.origin_is_local("http://localhost:8080")
    assert server.origin_is_local("http://[::1]:8080")


def test_remote_origin_is_rejected():
    assert not server.origin_is_local("https://evil.example")
    assert not server.origin_is_local("null")
