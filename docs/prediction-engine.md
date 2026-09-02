# SYSWATCH Prediction Engine

## Scope

The prediction engine provides a bounded, deterministic, local-only forecast of short-horizon host-resource trends from the existing behavioral-baseline history.

It is **not** a malware classifier, threat-intelligence feed, security verdict engine, or autonomous response mechanism.

## Data boundary

The engine reads only the local behavioral-baseline state:

- CPU utilization
- memory utilization
- disk utilization
- process count
- one-minute load

The implementation keeps at most 120 historical samples and a maximum three-step forecast horizon. Non-finite input values are discarded before fitting.

Prediction is read-only: the baseline file is not modified by forecasting.

## Model

For each metric with at least three usable samples, SYSWATCH fits a least-squares linear trend:

\[
y_i \approx a + b i
\]

and evaluates the fitted line over the next bounded sample positions. The reported slope is descriptive and is not converted into a security decision.

## API contract

`GET /api/prediction` returns a JSON object containing:

- `status`: `READY` or `INSUFFICIENT_HISTORY`
- `source`: `local_behavior_baseline`
- `samples`: number of retained baseline samples
- `horizon_steps`: bounded forecast horizon
- `forecasts`: per-metric forecast and slope information
- `actions_taken`: always `false`
- `security_verdict`: always `NONE`

If the prediction module cannot be imported, the API returns an explicit `UNAVAILABLE` payload rather than inventing a result.

## Security properties

- local-only; no external service calls
- no file-content inspection
- no process execution
- no state mutation during prediction
- bounded memory and compute
- non-finite input rejection
- explicit no-verdict/no-action boundary
- deterministic tests for insufficient history, trend forecasting, bounds, and immutability

## Operational interpretation

Forecasts are contextual evidence for the operator. A rising forecast can indicate that a resource trend deserves attention, but it does not establish malicious activity. Security conclusions must continue to come from correlated evidence and explicit policy layers.

The next integration stage is to surface these forecasts in the dashboard alongside the existing resource telemetry without changing their descriptive security boundary.
