# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path.cwd()
assets_dir = project_root / "assets"
branding_dir = assets_dir / "branding"

datas = [
    (str(branding_dir), "assets/branding"),
    (str(assets_dir / "config"), "assets/config"),
    (str(assets_dir / "shaders"), "assets/shaders"),
    (str(assets_dir / "sprites"), "assets/sprites"),
]


a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SmallOldGames",
    icon=str(branding_dir / "smalloldgames.ico") if (branding_dir / "smalloldgames.ico").exists() else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
