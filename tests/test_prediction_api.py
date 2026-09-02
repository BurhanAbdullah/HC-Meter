import importlib.util

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("syswatch_server", ROOT / "syswatch" / "api" / "server.py")
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


def test_prediction_api_returns_prediction_payload(monkeypatch):
    expected = {
        "status": "READY",
        "source": "local_behavior_baseline",
        "samples": 10,
        "horizon_steps": 3,
        "forecasts": {"cpu": {"available": True}},
        "actions_taken": False,
        "security_verdict": "NONE",
    }
    monkeypatch.setattr(server, "prediction_predict", lambda: expected)
    assert server.prediction_predict() == expected
    assert expected["actions_taken"] is False
    assert expected["security_verdict"] == "NONE"


def test_prediction_module_is_imported_on_server():
    assert callable(server.prediction_predict)
