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
- Debian release artifacts are also submitted to GitHub's Sigstore-backed build-provenance service, providing verifiable provenance for the package artifact when the release workflow runs with the required GitHub identity/attestation permissions.
- Release workflow permissions are limited to repository contents plus the narrowly required OIDC and attestation permissions for provenance publication.

## Verification contract

For a published release, consumers should verify both:

1. the SHA-256 checksum in `SHA256SUMS`; and
2. the GitHub artifact attestation for the Debian package using GitHub's supported attestation verification tooling.

The release metadata identifies the source commit used for the package build. The provenance attestation binds the published package digest to the GitHub Actions build identity and workflow invocation.

## Security boundary and limitations

The dependency SBOM describes the CI/development Python environment. It is not a claim that the host operating system, kernel, systemd, or native utilities are vulnerability-free. SYSWATCH has no third-party Python runtime dependencies at present.

SHA-256 release checksums provide artifact-integrity verification after download. Sigstore-backed provenance provides an additional build-origin/integrity signal, but it is not a substitute for an independent security review, a distribution trust chain, or operator verification of the expected repository and release policy.

The project does not claim that GitHub-hosted CI is an independent security review. An external security assessment remains a separate release gate.
