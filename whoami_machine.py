"""
whoami_machine.py — Nhân viên chạy file này để lấy MÃ MÁY gửi cho quản trị.

Chạy:  python whoami_machine.py
(hoặc bấm đúp nếu đã cài Python; hoặc đóng gói kèm tool.)
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tnt_license as tl  # noqa: E402


def main() -> None:
    try:
        mid = tl.get_machine_id()
    except tl.LicenseError as e:
        print("Lỗi khi đọc phần cứng:", e)
        input("\nNhấn Enter để thoát...")
        return

    pretty = tl.machine_id_pretty(mid)
    print("\n==================== MÃ MÁY CỦA BẠN ====================\n")
    print(pretty)
    print("\n=======================================================")
    print("Hãy COPY dòng trên gửi cho người quản trị để xin license.")

    # Ghi ra file cho dễ copy.
    try:
        out = Path(__file__).resolve().parent / "machine_id.txt"
        out.write_text(pretty + "\n", encoding="utf-8")
        print(f"(Đã lưu vào: {out})")
    except Exception:
        pass

    input("\nNhấn Enter để thoát...")


if __name__ == "__main__":
    main()
