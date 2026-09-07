"""
license_registry.py — SỔ ĐĂNG KÝ license đã cấp (chỉ dùng ở máy quản trị).

Mỗi lần tạo license, ghi thêm 1 dòng vào  licenses/registry.csv  để bạn tra cứu
"đã cấp cho ai, máy nào, hết hạn khi nào". File .key vẫn là bản gốc để gửi đi;
registry.csv chỉ là DANH SÁCH TỔNG cho bạn quản lý.

KHÔNG phát file này (và registry.csv) cho nhân viên.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

FIELDS = ["issued", "note", "machine_id", "expires", "tools", "file"]


def registry_path(base_dir: Path) -> Path:
    return base_dir / "licenses" / "registry.csv"


def append_record(base_dir: Path, *, note: str, machine_id: str,
                  expires: str | None, tools: list[str] | None,
                  file_path: str) -> Path:
    """Ghi thêm 1 dòng vào registry.csv (tạo file + header nếu chưa có)."""
    path = registry_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    row = {
        "issued": date.today().isoformat(),
        "note": note or "",
        "machine_id": machine_id,
        "expires": expires or "vĩnh viễn",
        "tools": ",".join(tools) if tools else "MỌI tool",
        "file": file_path,
    }
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)
    return path


def read_records(base_dir: Path) -> list[dict]:
    """Đọc toàn bộ registry.csv → list dict (mới nhất ở cuối)."""
    path = registry_path(base_dir)
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))
