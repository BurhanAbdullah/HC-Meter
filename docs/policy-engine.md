# SYSWATCH Policy Evidence Layer

The policy engine is a deterministic, local-only decision-support layer over already collected SYSWATCH evidence. It evaluates declarative rules and returns auditable recommendations.

## Safety boundary

The engine:

- does not execute commands;
- does not modify host state;
- does not kill processes, delete files, block traffic, or quarantine anything;
- does not contact external reputation or cloud services;
- bounds evidence and policy inputs;
- rejects malformed signals safely;
- always reports `actions_taken: false` and `security_verdict: NONE`.

`ESCALATE` and `REVIEW` are recommendations for a future response/policy layer, not actions performed by this module.

## Evidence contract

Evidence records use a small normalized schema: `type`, `severity`, `confidence`, and `source`. Unknown severity values are reduced to `INFO`; confidence is constrained to `[0, 1]`; malformed records are ignored.

The evaluator is order-independent and produces deterministic, confidence-sorted decisions. This makes the policy layer suitable for reproducible tests and later audit logging.

## Current policies

- `correlated_high_risk`: requires `reverse_shell` and `outbound_c2` at high-or-greater severity with confidence at least 0.60, producing an `ESCALATE` recommendation.
- `persistence_change`: requires `cron_change` and `file_write_tmp` at medium-or-greater severity with confidence at least 0.50, producing a `REVIEW` recommendation.

These are intentionally conservative demonstration policies. They do not constitute malware classification or production incident response.

## Next integration

The next step is to feed existing causal/network/filesystem evidence into this policy layer through a read-only API endpoint and expose the resulting recommendations in the dashboard. Safe reversible containment remains downstream and disabled until its own authorization, rollback, audit, and adversarial-test gates are satisfied.
