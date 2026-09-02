#!/usr/bin/env python3
"""Bounded, local-only host trend forecasting.

This module is intentionally descriptive. It forecasts short-horizon resource
trends from the existing local behavioral-baseline history; it does not infer
malware, make security verdicts, or take actions.
"""
import json
import math
import os
from pathlib import Path

FEATURES = ("cpu", "memory", "disk", "processes", "load1")
DEFAULT_STATE = Path(__file__).resolve().parents[2] / "runtime" / "behavior_baseline.json"
MAX_HISTORY = 120
FORECAST_STEPS = 3


def _safe_float(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _clamp(value, low, high):
    return max(low, min(high, value))


def _linear_forecast(values, steps=FORECAST_STEPS):
    """Return a least-squares short-horizon forecast and slope."""
    clean = [_safe_float(v) for v in values]
    clean = [v for v in clean if v is not None]
    if len(clean) < 3:
        return {"available": False, "samples": len(clean), "slope": None, "forecast": []}
    clean = clean[-MAX_HISTORY:]
    n = len(clean)
    x_mean = (n - 1) / 2.0
    y_mean = sum(clean) / n
    denom = sum((i - x_mean) ** 2 for i in range(n))
    slope = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(clean)) / denom if denom else 0.0
    intercept = y_mean - slope * x_mean
    forecast = [intercept + slope * (n - 1 + step) for step in range(1, steps + 1)]
    return {
        "available": True,
        "samples": n,
        "slope_per_sample": round(slope, 4),
        "forecast": [round(v, 3) for v in forecast],
    }


def _load_samples(state):
    try:
        data = json.loads(Path(state).read_text())
    except (OSError, ValueError, TypeError):
        return []
    samples = data.get("samples", []) if isinstance(data, dict) else []
    if not isinstance(samples, list):
        return []
    return [sample for sample in samples[-MAX_HISTORY:] if isinstance(sample, dict)]


def predict(state=None, steps=FORECAST_STEPS):
    """Produce bounded forecasts from local baseline history without mutation."""
    try:
        steps = _clamp(int(steps), 1, FORECAST_STEPS)
    except (TypeError, ValueError):
        steps = FORECAST_STEPS
    state = Path(state or os.environ.get("SYSWATCH_BASELINE_STATE", DEFAULT_STATE))
    samples = _load_samples(state)
    forecasts = {}
    for feature in FEATURES:
        forecasts[feature] = _linear_forecast([sample.get(feature) for sample in samples], steps)

    available = [item for item in forecasts.values() if item["available"]]
    return {
        "status": "READY" if available else "INSUFFICIENT_HISTORY",
        "source": "local_behavior_baseline",
        "samples": len(samples),
        "horizon_steps": steps,
        "forecasts": forecasts,
        "actions_taken": False,
        "security_verdict": "NONE",
    }
