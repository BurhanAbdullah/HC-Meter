from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"


def test_installer_validates_before_host_mutation():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'git check-ref-format --allow-onelevel "$REF"' in text
    assert text.index('git check-ref-format --allow-onelevel "$REF"') < text.index('groupadd --system "$SERVICE_GROUP"')
    assert text.index('git clone --depth 1 --branch "$REF"') < text.index('systemctl disable --now "$APP_NAME.service"')


def test_installer_stages_before_swapping_active_tree():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'cp -a "$CLONE/." "$STAGED/"' in text
    assert 'mv "$PREFIX" "$BACKUP"' in text
    assert 'mv "$STAGED" "$PREFIX"' in text
    assert text.index('cp -a "$CLONE/." "$STAGED/"') < text.index('mv "$STAGED" "$PREFIX"')


def test_installer_has_transactional_state_rollback():
    text = INSTALLER.read_text(encoding="utf-8")
    required = (
        'STATE_BACKUP="$TMP/state-backup"',
        'cp -a "$STATE_DIR" "$STATE_BACKUP"',
        'rm -rf "$STATE_DIR"',
        'mv "$STATE_BACKUP" "$STATE_DIR"',
        'CREATED_USER=0',
        'CREATED_GROUP=0',
        'STATE_CREATED=0',
        'trap on_error ERR',
    )
    for invariant in required:
        assert invariant in text


def test_installer_service_is_non_privileged_and_local_only():
    text = INSTALLER.read_text(encoding="utf-8")
    required = (
        'User=$SERVICE_USER',
        'Group=$SERVICE_GROUP',
        'NoNewPrivileges=true',
        'PrivateDevices=true',
        'ProtectSystem=strict',
        'ProtectHome=read-only',
        'CapabilityBoundingSet=',
        'AmbientCapabilities=',
        'ReadWritePaths=$STATE_DIR',
        'url = "http://127.0.0.1:8080/api/health"',
    )
    for invariant in required:
        assert invariant in text


def test_installer_health_check_is_release_blocking():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'raise SystemExit(f"SYSWATCH health check failed: {last}")' in text
    assert 'systemctl enable --now "$APP_NAME.service"' in text
    assert text.index('systemctl enable --now "$APP_NAME.service"') < text.index('raise SystemExit(f"SYSWATCH health check failed: {last}")')
