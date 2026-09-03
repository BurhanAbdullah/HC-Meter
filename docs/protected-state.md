# Protected state integrity and persistence

SYSWATCH provides an I/O-free integrity envelope plus a separate bounded local persistence layer for security-sensitive state. The two layers remain intentionally distinct: cryptographic verification does not imply that the host filesystem is trusted.

## Integrity contract

- State is canonically encoded with sorted JSON keys and bounded to 64 KiB.
- The envelope is versioned and rejects unknown schema versions.
- HMAC-SHA256 authenticates both schema version and canonical payload.
- Keys shorter than 32 bytes are rejected.
- Verification uses constant-time MAC comparison and fails closed on mismatch.
- No key material is returned in the envelope.
- The envelope module performs no filesystem, network, subprocess, privilege, or service-management operations.

## Persistence contract

`ProtectedStateStore` provides the local persistence boundary:

- state and integrity key are stored separately;
- state directories are restricted to mode `0700` and files to `0600`;
- new key files use exclusive creation and `O_NOFOLLOW` where the platform exposes it;
- existing key and state symlinks are rejected;
- state writes use a same-directory temporary file, `fsync`, and atomic replacement;
- persisted state is size-bounded before decoding and cryptographically verified before being returned;
- malformed, oversized, symlinked, or integrity-failed state is rejected rather than repaired implicitly.

## Trust boundary and non-claims

The local store is suitable for unprivileged host state but does **not** make the local host a trusted root of evidence. A user or root process that can replace both the key and state can forge a new valid pair. Stronger tamper resistance requires an external trust anchor such as a kernel-backed key store, TPM-backed secret, protected service identity, or remote append-only evidence system; those integrations are intentionally not enabled here.

This layer does not encrypt state, establish an independent forensic record, or grant privilege. The privileged containment adapter remains separate and disabled until its complete execution, authorization, audit, rollback, and recovery controls are validated.
