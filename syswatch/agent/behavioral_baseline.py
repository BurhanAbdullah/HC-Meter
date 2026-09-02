#!/usr/bin/env python3
"""Small, local-only behavioral baseline for host telemetry.

The baseline is descriptive, not an automated verdict: it reports deviation from
recent host behavior and never takes action on its own.
"""
import json
import math
import os
import time
from pathlib import Path

DEFAULT_STATE = Path(__file__).resolve().parents[2] / 'runtime' / 'behavior_baseline.json'
FEATURES = ('cpu', 'memory', 'disk', 'processes', 'load1')
MAX_SAMPLES = 600


def _stats(values):
    if not values:
        return {'mean': 0.0, 'stddev': 0.0, 'samples': 0}
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return {'mean': round(mean, 3), 'stddev': round(math.sqrt(variance), 3), 'samples': len(values)}


class Baseline:
    def __init__(self, state=None):
        self.state = Path(state or DEFAULT_STATE)
        self.state.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.state, 0o600)
        except OSError:
            pass
        self.samples = []
        self.load()

    def load(self):
        try:
            data = json.loads(self.state.read_text())
            self.samples = data.get('samples', [])[-MAX_SAMPLES:]
        except (OSError, ValueError, TypeError):
            self.samples = []

    def _save(self):
        payload = json.dumps({'version': 1, 'samples': self.samples[-MAX_SAMPLES:]}, indent=2)
        tmp = self.state.with_suffix('.tmp')
        tmp.write_text(payload)
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(self.state)

    def observe(self, metrics):
        sample = {
            'ts': int(time.time()),
            'cpu': float(metrics.get('cpu', 0)),
            'memory': float(metrics.get('memory', 0)),
            'disk': float(metrics.get('disk', 0)),
            'processes': float(metrics.get('processes', 0)),
            'load1': float(metrics.get('load', {}).get('1m', 0)),
        }
        history = self.samples[-MAX_SAMPLES:]
        stats = {k: _stats([float(x.get(k, 0)) for x in history]) for k in FEATURES}
        deviations = {}
        for k in FEATURES:
            s = stats[k]
            if s['samples'] < 10 or s['stddev'] < 1e-9:
                deviations[k] = None
            else:
                deviations[k] = round(abs(sample[k] - s['mean']) / s['stddev'], 2)
        self.samples.append(sample)
        self._save()
        valid = [v for v in deviations.values() if v is not None]
        return {
            'ready': len(self.samples) >= 10,
            'samples': len(self.samples),
            'deviation_sigma': deviations,
            'max_deviation_sigma': round(max(valid), 2) if valid else None,
            'status': 'BASELINING' if len(self.samples) < 10 else ('ELEVATED' if max(valid, default=0) >= 3 else 'NORMAL'),
            'updated_at': sample['ts'],
        }


baseline = Baseline()


def observe(metrics):
    return baseline.observe(metrics)
