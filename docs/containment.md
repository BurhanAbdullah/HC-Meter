# Containment safety foundation

SYSWATCH currently provides a **plan-only** containment foundation. It does not claim host containment is implemented.

## Security contract

- The planner is local and deterministic.
- Only IP targets are accepted.
- Invalid or unsupported targets fail closed.
- Input is bounded (`32` targets at the API contract level; reason text is capped at 240 characters).
- A valid plan requests `BLOCK_EGRESS`, but performs no firewall, process, socket, or filesystem mutation.
- Every result reports `actions_taken: false` and `security_verdict: NONE`.
- An explicit authorization boundary is required before any privileged adapter can be introduced.
- The privileged adapter is deliberately marked `NOT_IMPLEMENTED`.

## Why plan-only first

Endpoint containment is a high-impact operation. SYSWATCH must first establish deterministic authorization, audit logging, rollback identity, privilege separation, platform-specific adapters, and failure semantics before a host-mutating implementation is enabled.

Therefore this module is **not** a containment product, firewall controller, EDR response engine, or autonomous blocking mechanism. The roadmap item is not considered complete until an independently reviewable privileged adapter and rollback path exist and pass adversarial and cross-platform testing.
