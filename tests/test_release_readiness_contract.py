from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
RELEASE = WORKFLOWS / "release.yml"
README = ROOT / "README.md"
INSTALLER = ROOT / "install.sh"
BUILDER = ROOT / "packaging" / "build_deb.sh"


def test_all_workflow_actions_are_immutable():
    pattern = re.compile(r"^\s*-?\s*uses:\s*[^@\s]+@([^\s#]+)")
    bad = []
    for path in WORKFLOWS.rglob("*.yml"):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = pattern.match(line)
            if match and not re.fullmatch(r"[0-9a-fA-F]{40}", match.group(1)):
                bad.append(f"{path}:{lineno}: {match.group(1)}")
    assert not bad, "Unpinned GitHub Actions: " + ", ".join(bad)


def test_release_cannot_publish_before_artifact_lifecycle_gate():
    text = RELEASE.read_text(encoding="utf-8")
    lifecycle = text.index("name: Verify packaged install lifecycle")
    attest = text.index("name: Attest Debian package provenance")
    publish = text.index("name: Create release")
    assert lifecycle < attest < publish
    assert "tests/test_debian_lifecycle.sh" in text


def test_release_contract_is_versioned_and_reproducible():
    text = RELEASE.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "release_tag:" in text
    assert 'REF_NAME="${{ inputs.release_tag }}"' in text
    assert 'REF_NAME="${GITHUB_REF_NAME}"' in text
    assert '[[ "$REF_NAME" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+$ ]]' in text
    assert 'git show-ref --verify --quiet "refs/tags/${{ steps.release.outputs.ref_name }}"' in text
    assert 'test "$RELEASE_SHA" = "$(git rev-parse HEAD)"' in text
    assert "sha256sum --check SHA256SUMS" in text
    assert "cmp --silent first-build.deb \"$PACKAGE\"" in text
    assert "RELEASE-METADATA.txt" in text


def test_service_release_boundary_is_non_privileged():
    builder = BUILDER.read_text(encoding="utf-8")
    required = (
        "User=syswatch",
        "Group=syswatch",
        "NoNewPrivileges=true",
        "PrivateDevices=true",
        "ProtectSystem=strict",
        "ProtectHome=read-only",
        "CapabilityBoundingSet=",
        "AmbientCapabilities=",
        "ReadWritePaths=/var/lib/syswatch",
    )
    for invariant in required:
        assert invariant in builder


def test_installer_and_package_share_the_same_service_boundary():
    installer = INSTALLER.read_text(encoding="utf-8")
    builder = BUILDER.read_text(encoding="utf-8")

    # Static systemd hardening directives must remain identical across both
    # installation paths. Service identity and state paths are intentionally
    # emitted from fixed installer variables, so validate that relationship
    # separately instead of requiring already-expanded literals in install.sh.
    shared_directives = (
        "NoNewPrivileges=true",
        "PrivateDevices=true",
        "ProtectSystem=strict",
        "ProtectHome=read-only",
        "CapabilityBoundingSet=",
        "AmbientCapabilities=",
        "StateDirectory=syswatch",
        "StateDirectoryMode=0750",
    )
    for invariant in shared_directives:
        assert invariant in installer
        assert invariant in builder

    assert 'SERVICE_USER="syswatch"' in installer
    assert 'SERVICE_GROUP="syswatch"' in installer
    assert 'User=$SERVICE_USER' in installer
    assert 'Group=$SERVICE_GROUP' in installer
    assert "User=syswatch" in builder
    assert "Group=syswatch" in builder

    assert 'STATE_DIR="/var/lib/syswatch"' in installer
    assert 'Environment=SYSWATCH_STATE_DIR=$STATE_DIR' in installer
    assert 'ReadWritePaths=$STATE_DIR' in installer
    assert "Environment=SYSWATCH_STATE_DIR=/var/lib/syswatch" in builder
    assert "ReadWritePaths=/var/lib/syswatch" in builder

    assert 'export SYSWATCH_STATE_DIR="${SYSWATCH_STATE_DIR:-/var/lib/syswatch}"' in installer
    assert 'url = "http://127.0.0.1:8080/api/health"' in installer


def test_public_documentation_keeps_platform_security_and_release_claims_bounded():
    text = README.read_text(encoding="utf-8")
    required_claims = (
        "local-first Linux endpoint-security project",
        "Ubuntu 24.04 LTS / Linux amd64",
        "No verified public SYSWATCH release is published yet",
        "main` is a development branch",
        "does **not** claim 99.99% detection accuracy",
        "does not execute containment",
        "Cross-platform agents are not currently supported or verified",
        "RHEL-family packaging",
        "not declared release-ready until an actual versioned release artifact",
    )
    for claim in required_claims:
        assert claim in text

    forbidden = (
        "100% malware detection",
        "guaranteed malware detection",
        "detects all malware",
        "Windows is supported",
        "macOS is supported",
        "RHEL is supported",
        "production EDR",
    )
    assert not any(claim in text for claim in forbidden)


def test_public_development_install_is_explicitly_not_a_release_install():
    text = README.read_text(encoding="utf-8")
    assert "sudo SYSWATCH_REF=main ./install.sh" in text
    assert "There is not yet a public versioned release install command" in text
    assert "not a substitute for a versioned release artifact" in text
