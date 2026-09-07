# -*- mode: python ; coding: utf-8 -*-
r"""
PyInstaller spec — dựng APP QUẢN TRỊ LICENSE (tnt_license_admin) thành .exe.

Build:
    pip install cryptography PySide6 pyinstaller
    pyinstaller tnt_license_admin.spec

Kết quả:  dist/TNT_License_Admin/TNT_License_Admin.exe

LƯU Ý BẢO MẬT:
- KHÔNG nhúng thư mục keys/ vào exe. Sau khi build, thư mục keys/ (chứa
  private_key.pem) nằm CẠNH exe và phải giữ KÍN. Chỉ dùng trên máy bạn.
- App này (kèm keys/) KHÔNG phát cho nhân viên.
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ["tnt_license", "cryptography"]
hiddenimports += collect_submodules("cryptography")

a = Analysis(
    ["tnt_license_admin.py"],
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
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TNT_License_Admin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # app cửa sổ
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TNT_License_Admin",
)
