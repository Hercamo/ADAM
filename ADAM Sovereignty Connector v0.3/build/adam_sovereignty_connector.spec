# PyInstaller spec for ADAM Sovereignty Connector.
# Build with:  pyinstaller build\adam_sovereignty_connector.spec
# (or use the top-level build.bat which does env setup + pyinstaller in one step).

# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None

HERE = Path(os.getcwd()).resolve()
SRC = HERE / "src"
DEPLOY = HERE / "deploy"
WEB = SRC / "adam_sovereignty_connector" / "web" / "static"

a = Analysis(
    [str(SRC / "adam_sovereignty_connector" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[
        (str(DEPLOY), "deploy"),
        (str(WEB), "src/adam_sovereignty_connector/web/static"),
    ],
    hiddenimports=[
        "anthropic",
        "openai",
        "yaml",
        # corpus readers are optional; include the shim modules so
        # ImportError fires cleanly inside the frozen build if a user
        # opts not to install them.
        "adam_sovereignty_connector.ai.anthropic_backend",
        "adam_sovereignty_connector.ai.openai_backend",
        "adam_sovereignty_connector.ai.ollama_backend",
        "adam_sovereignty_connector.ai.openai_compat_backend",
        # DNA profile + corpus modules are lazy-imported from catalog
        # handlers — force them in so PyInstaller's static analysis
        # doesn't miss them.
        "adam_sovereignty_connector.core.dna",
        "adam_sovereignty_connector.core.corpus",
        "adam_sovereignty_connector.core.preflight",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pandas", "numpy"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="adam_sovereignty_connector",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    icon=None,          # set to an .ico path when you have branding art
    version="build/version_info.txt" if (HERE / "build" / "version_info.txt").exists() else None,
)
