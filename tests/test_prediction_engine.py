import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prediction", ROOT / "syswatch" / "agent" / "prediction_engine.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def write_state(path, samples):
    path.write_text(__import__('json').dumps({'version': 1, 'samples': samples}))


def sample(cpu):
    return {'cpu': cpu, 'memory': 40, 'disk': 50, 'processes': 100, 'load1': 1.0}


def test_prediction_requires_sufficient_history(tmp_path):
    path = tmp_path / 'baseline.json'
    write_state(path, [sample(20), sample(21)])
    out = mod.predict(path)
    assert out['status'] == 'INSUFFICIENT_HISTORY'
    assert out['actions_taken'] is False
    assert out['security_verdict'] == 'NONE'


def test_prediction_is_deterministic_and_forecasts_trend(tmp_path):
    path = tmp_path / 'baseline.json'
    write_state(path, [sample(v) for v in range(20, 30)])
    out = mod.predict(path, steps=3)
    cpu = out['forecasts']['cpu']
    assert out['status'] == 'READY'
    assert cpu['available'] is True
    assert cpu['slope_per_sample'] == 1.0
    assert cpu['forecast'] == [30.0, 31.0, 32.0]


def test_prediction_does_not_mutate_baseline_state(tmp_path):
    path = tmp_path / 'baseline.json'
    samples = [sample(v) for v in range(20)]
    write_state(path, samples)
    before = path.read_text()
    mod.predict(path)
    assert path.read_text() == before


def test_prediction_bounds_horizon_and_rejects_nonfinite_values(tmp_path):
    path = tmp_path / 'baseline.json'
    write_state(path, [sample(v) for v in range(20)] + [sample(float('nan'))])
    out = mod.predict(path, steps=999)
    assert out['horizon_steps'] == 3
    assert out['forecasts']['cpu']['available'] is True
    assert all(abs(v) < 1000 for v in out['forecasts']['cpu']['forecast'])
