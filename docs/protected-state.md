# Protected state integrity

SYSWATCH now provides an I/O-free integrity envelope for security-sensitive local state. It is a building block for tamper resistance, not a complete persistence mechanism.

## Security contract

- State is canonically encoded with sorted JSON keys and bounded to 64 KiB.
- The envelope is versioned and rejects unknown schema versions.
- HMAC-SHA256 authenticates both schema version and canonical payload.
- Keys shorter than 32 bytes are rejected.
- Verification uses constant-time MAC comparison and fails closed on mismatch.
- No key material is returned in the envelope.
- The module performs no filesystem, network, subprocess, privilege, or service-management operations.

## Explicit non-claims

This module does not encrypt state, store keys, provide OS-backed secret protection, make files tamper-proof, or establish a durable forensic record. A future persistence layer must supply a protected key source and enforce restrictive filesystem/service permissions independently.

The privileged containment adapter remains separate and disabled until its complete execution, authorization, audit, rollback, and recovery controls are validated.
