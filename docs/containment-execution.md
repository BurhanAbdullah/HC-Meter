# Containment execution boundary

SYSWATCH now separates containment authorization from platform execution. The
execution broker accepts an already authorized `PLAN_ONLY` plan and delegates
to a narrowly defined adapter interface.

## Security boundary

- The default adapter is unavailable and therefore cannot mutate the host.
- The broker never invokes a shell, firewall command, process operation,
socket operation, filesystem operation, or privilege-escalation mechanism.
- An adapter is supplied explicitly by the caller; it must expose only `apply`
and `rollback` capabilities.
- Authorization must already be `AUTHORIZED_PLAN` and must retain
`actions_taken=false` and `security_verdict=NONE`.
- A successful adapter call must return a non-empty rollback token before the
broker reports `APPLIED`.
- Rollback must return an explicit boolean `True`; anything else is treated as
failure.
- Adapter exceptions are converted to bounded failure results rather than
propagated as successful containment.

## What is intentionally not implemented

This is not a host-containment implementation. There is no Linux firewall,
Windows Filtering Platform, macOS packet-filter, or other privileged adapter in
this change. A production adapter requires a separate platform-specific
security review covering privilege separation, installation ownership,
capability scoping, atomic rule changes, rollback durability, timeout and
crash recovery, and adversarial testing.

Do not interpret `APPLIED` from an injected test adapter as evidence that
SYSWATCH can contain a real endpoint. Production capability remains unavailable
until a reviewed platform adapter is implemented and released.
