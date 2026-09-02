from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "network_intelligence", ROOT / "syswatch" / "agent" / "network_intelligence.py"
)
network = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(network)


def test_classification_is_conservative():
    assert network.classify_ip("127.0.0.1")["classification"] == "LOOPBACK"
    assert network.classify_ip("10.10.0.4")["classification"] == "PRIVATE"
    public = network.classify_ip("1.1.1.1")
    assert public["classification"] == "PUBLIC_UNASSESSED"
    assert public["assessed"] is False


def test_endpoint_parser_handles_ipv4_and_ipv6():
    assert network.parse_endpoint("192.0.2.10:443") == ("192.0.2.10", 443)
    assert network.parse_endpoint("[2001:db8::10]:53") == ("2001:db8::10", 53)
    assert network.parse_endpoint("not-an-endpoint") is None


def test_resolv_conf_parser_is_local_and_bounded():
    text = """
# comment
nameserver 10.0.0.1
nameserver 2001:4860:4860::8888
nameserver invalid
nameserver 10.0.0.1
"""
    assert network.parse_resolv_conf(text) == ["10.0.0.1", "2001:4860:4860::8888"]


def test_ss_parser_exposes_no_process_command_line():
    text = """
tcp ESTAB 0 0 10.0.0.5:41820 1.1.1.1:443
udp UNCONN 0 0 127.0.0.1:5353 224.0.0.251:5353
"""
    rows = network.parse_ss_output(text)
    assert len(rows) == 2
    assert rows[0]["peer"]["address"] == "1.1.1.1"
    assert rows[0]["peer_classification"] == "PUBLIC_UNASSESSED"
    assert rows[1]["peer_classification"] == "MULTICAST"
    assert all("command" not in row for row in rows)


def test_collect_uses_supplied_inputs_without_network_access(tmp_path):
    resolv = tmp_path / "resolv.conf"
    resolv.write_text("nameserver 192.168.1.1\n")
    result = network.collect(
        resolv_path=resolv,
        ss_text="tcp ESTAB 0 0 192.168.1.20:40000 93.184.216.34:443\n",
    )
    assert result["reputation_provider"] == "none"
    assert result["dns"]["nameservers"] == ["192.168.1.1"]
    assert result["summary"] == {"connections": 1, "public_unassessed": 1, "local_or_special": 0}
