import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("baseline", ROOT / "syswatch" / "agent" / "behavioral_baseline.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def sample():
    return {'cpu': 20, 'memory': 40, 'disk': 50, 'processes': 100, 'load': {'1m': 1.0}}


def test_baseline_starts_in_learning_mode(tmp_path):
    b = mod.Baseline(tmp_path / 'baseline.json')
    out = b.observe(sample())
    assert out['ready'] is False
    assert out['status'] == 'BASELINING'


def test_baseline_detects_large_deviation_without_action(tmp_path):
    b = mod.Baseline(tmp_path / 'baseline.json')
    for _ in range(20):
        b.observe(sample())
    out = b.observe({'cpu': 95, 'memory': 40, 'disk': 50, 'processes': 100, 'load': {'1m': 1.0}})
    assert out['ready'] is True
    assert out['deviation_sigma']['cpu'] is not None
    assert out['status'] == 'ELEVATED'
    assert 'action' not in out


def test_baseline_state_is_private(tmp_path):
    path = tmp_path / 'baseline.json'
    b = mod.Baseline(path)
    b.observe(sample())
    assert path.exists()
    assert oct(path.stat().st_mode & 0o777) == '0o600'
