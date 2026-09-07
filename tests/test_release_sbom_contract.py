from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / ".github" / "workflows" / "release.yml"
SECURITY = ROOT / ".github" / "workflows" / "security.yml"
REQUIREMENTS = ROOT / "requirements-release-audit.txt"


def test_release_audit_dependency_is_pinned_and_security_audited():
    assert REQUIREMENTS.read_text(encoding="utf-8").splitlines() == [
        "# Release-time SBOM generator; not shipped by SYSWATCH.",
        "pip-audit==2.10.1",
    ]
    security = SECURITY.read_text(encoding="utf-8")
    for invariant in (
        "requirements-release-audit.txt",
        "release-audit-dependency-sbom.cdx.json",
        "python -m pip_audit -r requirements-release-audit.txt",
    ):
        assert invariant in security


def test_release_publishes_sbom_evidence_with_the_verified_artifacts():
    text = RELEASE.read_text(encoding="utf-8")
    for invariant in (
        "requirements-release-audit.txt",
        "WINDOWS-BUILD-SBOM.cdx.json",
        "RELEASE-AUDIT-SBOM.cdx.json",
        "RELEASE-AUDIT-SBOM-WINDOWS.cdx.json",
        "test -f release/WINDOWS-BUILD-SBOM.cdx.json",
        "test -f release/RELEASE-AUDIT-SBOM.cdx.json",
        "test -f release/RELEASE-AUDIT-SBOM-WINDOWS.cdx.json",
        "release/WINDOWS-BUILD-SBOM.cdx.json",
        "release/RELEASE-AUDIT-SBOM.cdx.json",
        "release/RELEASE-AUDIT-SBOM-WINDOWS.cdx.json",
    ):
        assert invariant in text


def test_release_sbom_generation_is_before_artifact_staging():
    text = RELEASE.read_text(encoding="utf-8")
    for job_marker, sbom_marker, stage_marker in (
        ("  package:\n", "name: Generate release build SBOM evidence", "name: Stage Debian release artifacts"),
        ("  windows-package:\n", "name: Generate Windows release SBOM evidence", "name: Stage Windows release artifacts"),
    ):
        start = text.index(job_marker)
        job = text[start:]
        assert job.index(sbom_marker) < job.index(stage_marker)
