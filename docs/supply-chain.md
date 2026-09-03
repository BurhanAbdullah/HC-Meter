# SYSWATCH supply-chain security

SYSWATCH treats its CI and release path as part of the security boundary.

## Current controls

- Every GitHub Actions dependency is pinned to a full 40-character commit SHA.
- CI checks the workflow directory and fails if a mutable action tag or branch is introduced.
- Development tooling is explicitly version-pinned in `requirements-dev.txt` and is not shipped in the runtime package.
- The application runtime is intentionally stdlib-only; CI verifies that `syswatch/` does not acquire undeclared third-party Python imports.
- `pip-audit` audits the pinned development environment against known Python package advisories and emits a CycloneDX JSON SBOM during the security workflow.
- Release packages are built from the exact tagged Git commit using `git archive`, not from a mutable working tree.
- Debian release artifacts receive SHA-256 checksums and release metadata containing the version and source commit.
- Release packaging verifies the generated Debian package and checksum before publication.
- Release workflow permissions are limited to repository contents and are not granted broad repository administration privileges.

## Security boundary and limitations

The dependency SBOM describes the CI/development Python environment. It is not a claim that the host operating system, kernel, systemd, or native utilities are vulnerability-free. SYSWATCH has no third-party Python runtime dependencies at present.

SHA-256 release checksums provide artifact-integrity verification after download. They are not a substitute for an independently trusted signing key or Sigstore verification. Cryptographic artifact signing/provenance remains a release-hardening item until it is implemented and validated.

The project does not claim that GitHub-hosted CI is an independent security review. An external security assessment remains a separate release gate.
