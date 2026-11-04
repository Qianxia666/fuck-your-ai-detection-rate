# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：产出单文件 FYADR.exe（含 Python 运行时、依赖与前端产物）。"""

import os

# SPECPATH 指向本文件所在目录（packaging/），仓库根在它上一级
ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

a = Analysis(
    [os.path.join(ROOT, "packaging", "launcher.py")],
    pathex=[os.path.join(ROOT, "scripts")],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "app", "dist"), "app/dist"),
        (os.path.join(ROOT, "prompts"), "prompts"),
    ],
    hiddenimports=[
        "web_app",
        "core_config",
        "core_documents",
        "core_llm",
        "core_runs",
        "core_warnings",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "numpy",
        "pandas",
        "matplotlib",
        "PIL",
        "setuptools",
        "pip",
        "pytest",
        "IPython",
    ],
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
    name="FYADR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
