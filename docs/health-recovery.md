# Health and corrupted-state recovery

SYSWATCH treats protected local state as a security boundary. A health check must be read-only: it must not create a key, repair files silently, or mutate host state merely because health was queried.

`ProtectedStateStore.check()` reports one of these bounded states:

- `ABSENT`: no protected-state directory exists; a first-run initialization may create it through the normal write path.
- `PRESENT` + `PASS`: state and its integrity key exist and verification succeeds.
- `INCOMPLETE`: the state directory exists but either the key or state file is missing. SYSWATCH fails closed rather than inventing or replacing state during health inspection.
- `CORRUPT`, `INVALID`, or another `FAIL` result: the protected state cannot be trusted. Callers must not use it as authoritative security state.

The current recovery boundary is deliberately conservative. There is no automatic state reconstruction, key replacement, or destructive cleanup in the health check. Recovery should be performed by the explicit lifecycle/upgrade path after preserving evidence and validating the installation. The local protected-state mechanism is not a TPM, kernel keyring, remote append-only ledger, or independent trust anchor.

## Operational contract

1. Health inspection is read-only.
2. Integrity failure is fail-closed.
3. Missing state is distinguishable from corrupt state.
4. A corrupt state must never be silently reset during a status/health request.
5. Any future automated recovery must be separately authorized, bounded, auditable, and regression-tested.
