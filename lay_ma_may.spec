# -*- mode: python ; coding: utf-8 -*-
r"""
PyInstaller spec — tool nhỏ 'Lấy mã máy' cho nhân viên.
Build:  pyinstaller lay_ma_may.spec  →  dist/TNT_LayMaMay/TNT_LayMaMay.exe
An toàn phát cho nhân viên (không có khoá bí mật).
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ["tnt_license", "cryptography"]
hiddenimports += collect_submodules("cryptography")

a = Analysis(
    ["lay_ma_may.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "scipy", "playwright"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="TNT_LayMaMay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False, upx=False,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="TNT_LayMaMay")
