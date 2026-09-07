# PyInstaller one-file build for the supported Windows validation target.
from pathlib import Path

block_cipher = None
ROOT = Path(SPEC).resolve().parents[1]

a = Analysis(
    [str(ROOT / "syswatch" / "windows_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "web"), "web")],
    hiddenimports=[
        "syswatch.platform_windows",
        "syswatch.api.server",
        "syswatch.agent.causal_engine",
        "syswatch.agent.behavioral_baseline",
        "syswatch.agent.network_intelligence",
        "syswatch.agent.filesystem_behavior",
        "syswatch.agent.prediction_engine",
        "syswatch.agent.policy_engine",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="syswatch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
