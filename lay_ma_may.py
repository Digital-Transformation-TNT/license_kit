"""
lay_ma_may.py — Tool NHỎ cho nhân viên: double-click để lấy MÃ MÁY.

Hiện 1 cửa sổ có mã máy + nút "Copy mã máy", đồng thời lưu machine_id.txt.
Nhân viên copy mã gửi cho quản trị để xin license.

Đóng gói:  pyinstaller lay_ma_may.spec  →  dist/TNT_LayMaMay/TNT_LayMaMay.exe
(An toàn để phát cho nhân viên — KHÔNG chứa khoá bí mật.)
"""
from __future__ import annotations

import os
os.environ.setdefault("CRYPTOGRAPHY_OPENSSL_NO_LEGACY", "1")

import sys

import tnt_license as tl


def main() -> None:
    # show_machine_id tự dựng QApplication + hộp thoại có nút Copy, và ghi machine_id.txt.
    tl.show_machine_id(
        reason="Đây là MÃ MÁY của bạn. Bấm 'Copy mã máy' rồi gửi cho người quản trị.",
        tool_name="",
    )


if __name__ == "__main__":
    main()
