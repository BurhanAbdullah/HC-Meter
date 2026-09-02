# SYSWATCH Platform Roadmap

SYSWATCH is being developed as a security platform, not only a Linux monitoring script.

## Product layers

```text
Public website
    │
    ├── Documentation
    ├── Verified releases
    ├── Installation
    └── Product / security disclosures
            │
            ▼
Endpoint agent
    │
    ├── Host telemetry
    ├── Process / network / filesystem sensors
    ├── Behavioral baseline
    ├── Local causal engine
    └── Policy-controlled response
            │
            ▼
Future fleet control plane
    │
    ├── Device identity
    ├── Signed enrollment
    ├── Fleet health
    ├── Cross-device correlation
    └── Security event search
            │
            ▼
Future IoT / edge agents
    ├── Lightweight sensor profile
    ├── Device identity + secure enrollment
    ├── Resource-bounded telemetry
    ├── Local buffering when offline
    └── No destructive action by default
```

## IoT direction

IoT support is a **future product layer**, not a claim that the current Linux agent supports arbitrary embedded devices.

The design target is a small, auditable edge sensor that can run on constrained Linux-class devices and expose a normalized telemetry contract. Device-specific collectors should be isolated from the core correlation model.

### Security requirements before IoT release

- unique device identity;
- authenticated enrollment;
- signed agent updates;
- least-privilege execution;
- bounded memory, CPU and storage use;
- offline buffering with explicit retention limits;
- encrypted transport when a remote control plane exists;
- replay protection for security events;
- fleet-level revocation;
- no unauthenticated remote command execution;
- deterministic tests on every supported hardware profile.

## Release ladder

1. Harden Linux endpoint agent.
2. Complete DNS, filesystem, prediction and policy layers.
3. Add safe reversible containment.
4. Add tamper resistance and signed supply chain.
5. Produce verified Debian/RHEL-family releases.
6. Establish cross-platform agent contracts.
7. Perform independent security evaluation.
8. Add constrained edge/IoT sensor profiles.
9. Add authenticated fleet correlation only after the device-security model is validated.
