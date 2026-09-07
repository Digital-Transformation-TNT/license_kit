"""
make_license.py — TẠO FILE license.key CHO MỘT MÁY (CHỈ CHẠY TRÊN MÁY BẠN).

Quy trình cấp phép cho một nhân viên:
  1) Nhân viên chạy tool (hoặc whoami_machine.py) → lấy MÃ MÁY, gửi cho bạn.
  2) Bạn chạy script này, nhập mã máy + (tuỳ chọn) hạn dùng + danh sách tool.
  3) Ký bằng private key → xuất ra license.key.
  4) Gửi license.key cho nhân viên; họ đặt cạnh tool hoặc tại C:\\TNT\\license.key.

Một license.key dùng được cho MỌI tool trên đúng máy đó (vì mọi tool nhúng cùng
public key). Muốn giới hạn "máy này chỉ dùng tool A, B" thì điền --tools.

Ví dụ:
  # Cấp full quyền, không hạn:
  python make_license.py --machine 1A2B... --note "Nguyen Van A"

  # Chỉ cho 2 tool, hết hạn cuối năm:
  python make_license.py --machine 1A2B... --expires 2026-12-31 \
        --tools TNT_Listing,TNT_VideoSubtitle --note "Nguyen Van A"

  # Xuất thẳng ra thư mục giao cho nhân viên:
  python make_license.py --machine 1A2B... --out D:\\giao\\NguyenVanA\\license.key
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from cryptography.hazmat.primitives import serialization

# Dùng lại hàm đóng gói/ký từ chính module (đảm bảo định dạng KHỚP lúc kiểm).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tnt_license as tl  # noqa: E402

KEYS_DIR = Path(__file__).resolve().parent / "keys"
PRIV_PATH = KEYS_DIR / "private_key.pem"


def _load_private_key():
    if not PRIV_PATH.exists():
        print(f"!! Không thấy private key: {PRIV_PATH}")
        print("   Hãy chạy make_keys.py trước.")
        sys.exit(1)
    data = PRIV_PATH.read_bytes()
    return serialization.load_pem_private_key(data, password=None)


def _normalize_machine_id(raw: str) -> str:
    """Cho phép dán mã máy dạng đẹp (có gạch/khoảng trắng) → chuẩn hoá về hex thường."""
    cleaned = "".join(c for c in raw if c.isalnum()).lower()
    return cleaned


def main() -> None:
    ap = argparse.ArgumentParser(description="Tạo license.key cho một máy.")
    ap.add_argument("--machine", required=True,
                    help="MÃ MÁY nhân viên gửi (dán cả bản có gạch cũng được).")
    ap.add_argument("--expires", default=None,
                    help="Ngày hết hạn YYYY-MM-DD. Bỏ trống = KHÔNG hết hạn.")
    ap.add_argument("--tools", default=None,
                    help="Danh sách tool được phép, phẩy. Bỏ trống = MỌI tool.")
    ap.add_argument("--note", default="",
                    help="Ghi chú (tên nhân viên...). Được KÝ kèm.")
    ap.add_argument("--out", default=None,
                    help="Đường dẫn file xuất ra. Mặc định: ./licenses/<note-hoặc-machine>.key")
    args = ap.parse_args()

    machine_id = _normalize_machine_id(args.machine)
    if len(machine_id) != 64:
        print(f"!! MÃ MÁY sau khi chuẩn hoá dài {len(machine_id)} ký tự, cần 64 (hex SHA-256).")
        print(f"   Nhận được: {machine_id!r}")
        sys.exit(1)

    if args.expires:
        try:
            exp = datetime.strptime(args.expires, "%Y-%m-%d").date()
        except ValueError:
            print("!! --expires sai định dạng, cần YYYY-MM-DD.")
            sys.exit(1)
        if exp < date.today():
            print(f"!! Cảnh báo: hạn {args.expires} đã ở QUÁ KHỨ — license sẽ hết hạn ngay.")

    tools = None
    if args.tools:
        tools = [t.strip() for t in args.tools.split(",") if t.strip()]

    payload = {
        "machine_id": machine_id,
        "expires": args.expires,        # None = vô thời hạn
        "tools": tools,                 # None = mọi tool
        "issued": date.today().isoformat(),
        "note": args.note,
    }

    priv = _load_private_key()
    signature = priv.sign(tl._canonical_payload_bytes(payload))
    license_text = tl.encode_license(payload, signature)

    # Nơi lưu.
    if args.out:
        out = Path(args.out)
    else:
        safe = "".join(c for c in (args.note or machine_id[:12]) if c.isalnum() or c in "-_") \
               or machine_id[:12]
        out = Path(__file__).resolve().parent / "licenses" / f"{safe}.key"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(license_text, encoding="utf-8")

    # Ghi vào SỔ ĐĂNG KÝ để tra cứu sau này.
    import license_registry as reg
    reg_path = reg.append_record(
        Path(__file__).resolve().parent,
        note=args.note, machine_id=machine_id, expires=args.expires,
        tools=tools, file_path=str(out),
    )

    # Tự kiểm lại NGAY để chắc file ký đúng (kiểm chữ ký, bỏ qua so mã máy vì
    # đang tạo cho máy KHÁC → truyền this_machine_id = chính machine_id trong license).
    tl.verify_license_text(license_text, (tools or ["*"])[0], this_machine_id=machine_id)

    print("==================== ĐÃ TẠO LICENSE ====================")
    print(f"Máy      : {machine_id}")
    print(f"Hết hạn  : {args.expires or 'KHÔNG (vô thời hạn)'}")
    print(f"Tool     : {', '.join(tools) if tools else 'MỌI tool'}")
    print(f"Ghi chú  : {args.note or '(trống)'}")
    print(f"File     : {out}")
    print(f"Sổ đăng ký: {reg_path}")
    print("=======================================================")
    print("→ Gửi file này cho nhân viên, đặt cạnh tool hoặc tại C:\\TNT\\license.key")


if __name__ == "__main__":
    main()
