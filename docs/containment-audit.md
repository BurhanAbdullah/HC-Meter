# Containment audit ledger

SYSWATCH now has a bounded, local, in-memory audit ledger for containment state transitions. It is an integrity primitive, not a claim of durable forensic storage.

## Security contract

- Entries are immutable dataclass values once appended.
- Each entry contains the previous entry hash and a SHA-256 hash of its canonical fields.
- Verification is deterministic and fails on sequence, linkage, or content tampering.
- Input fields and timestamps are bounded and strictly typed.
- Capacity is bounded to 256 entries by default.
- When capacity is reached, append fails closed rather than silently discarding history or rewriting the chain.
- Export returns value records only; this module does not write files, databases, logs, sockets, or remote services.
- The ledger grants no privilege and performs no host mutation.

## Not yet claimed

This is not a durable audit trail, tamper-proof storage, remote SIEM integration, or evidence of successful host containment. Durable storage and privileged execution remain separate security-reviewed dependencies.
