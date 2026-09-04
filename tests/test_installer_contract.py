from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"


def test_installer_validates_before_host_mutation():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'git check-ref-format --allow-onelevel "$REF"' in text
    assert text.index('git check-ref-format --allow-onelevel "$REF"') < text.index('groupadd --system "$SERVICE_GROUP"')
    assert text.index('git clone --depth 1 --branch "$REF"') < text.index('mv "$STAGED" "$PREFIX"')


def test_installer_stages_before_swapping_active_tree():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'cp -a "$CLONE/." "$STAGED/"' in text
    assert 'mv "$PREFIX" "$BACKUP"' in text
    assert 'mv "$STAGED" "$PREFIX"' in text
    assert text.index('cp -a "$CLONE/." "$STAGED/"') < text.index('mv "$STAGED" "$PREFIX"')


def test_installer_has_transactional_state_rollback():
    text = INSTALLER.read_text(encoding="utf-8")
    required = (
        'STATE_PREEXISTED=0',
        'STATE_PREEXISTED=1',
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

    # A first install must create state only in the no-preexisting-state branch;
    # rollback restores a backup only when that state existed beforehand.
    assert 'if [[ -d "$STATE_DIR" ]]; then\n  STATE_PREEXISTED=1' in text
    assert 'if [[ "$STATE_PREEXISTED" -eq 1 && -n "$STATE_BACKUP" && -d "$STATE_BACKUP" ]]; then' in text


def test_installer_restores_service_wrappers_and_service_state_on_failure():
    text = INSTALLER.read_text(encoding="utf-8")
    required = (
        'SERVICE_BACKUP="$TMP/service-backup"',
        'BIN_BACKUP="$TMP/bin-backup"',
        'SIGNAL_BIN_BACKUP="$TMP/signal-bin-backup"',
        'SERVICE_PREEXISTED=1',
        'BIN_PREEXISTED=1',
        'SIGNAL_BIN_PREEXISTED=1',
        'SERVICE_WAS_ENABLED=1',
        'SERVICE_WAS_ACTIVE=1',
        'rm -f "$SERVICE" "$BIN" "$SIGNAL_BIN"',
        'cp -a "$SERVICE_BACKUP" "$SERVICE"',
        'cp -a "$BIN_BACKUP" "$BIN"',
        'cp -a "$SIGNAL_BIN_BACKUP" "$SIGNAL_BIN"',
        'systemctl enable "$APP_NAME.service"',
        'systemctl start "$APP_NAME.service"',
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


def test_installer_health_check_requires_expected_application_contract():
    text = INSTALLER.read_text(encoding="utf-8")
    required = (
        'if response.status != 200:',
        'payload = json.load(response)',
        'payload.get("ok") is True',
        'payload.get("service") == "syswatch"',
        'payload.get("agent") == "online"',
        'raise RuntimeError(f"unexpected health payload: {payload!r}")',
    )
    for invariant in required:
        assert invariant in text

    # Do not regress to treating arbitrary 2xx/3xx/4xx responses as healthy.
    assert 'if 200 <= response.status < 500:' not in text
