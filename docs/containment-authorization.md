# Containment authorization boundary

SYSWATCH now has a deterministic authorization/audit primitive for its plan-only containment foundation. This is still **not** host containment.

## Security contract

- A containment plan receives a stable SHA-256 identity from canonical JSON.
- An authorization grant must explicitly name the exact plan identity, the required `containment:block-egress` scope, an operator identity, a grant identity, and an expiry.
- Time is supplied by the caller so expiry decisions are deterministic and testable.
- Missing, malformed, expired, mismatched, or incorrectly scoped grants fail closed.
- An authorized result remains `AUTHORIZED_PLAN`; it does not execute a firewall, process, socket, or filesystem operation.
- Audit records are constructed in memory and are deterministic; this module does not persist them or transmit them.
- `actions_taken` remains `false` and `security_verdict` remains `NONE`.
- The privileged platform adapter remains `NOT_IMPLEMENTED`.

## What this enables next

Before any host-mutating adapter is introduced, the project still needs a least-privilege execution boundary, durable tamper-evident audit storage, rollback identity/state, platform-specific adapters, failure/timeout semantics, and independent adversarial testing. This module establishes only the authorization and identity primitives required for those later controls.

Do not interpret `AUTHORIZED_PLAN` as evidence that the endpoint was contained. It means only that a caller supplied a structurally valid, explicitly scoped authorization for a deterministic plan.
