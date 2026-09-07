"""
make_keys.py — SINH CẶP KHOÁ Ed25519 (CHẠY MỘT LẦN DUY NHẤT, CHỈ TRÊN MÁY BẠN).

  * Tạo private key  → keys/private_key.pem   ← TUYỆT MẬT, KHÔNG BAO GIỜ phát đi.
  * Tạo public key   → in ra màn hình (hex)   ← dán vào tnt_license.py (PUBLIC_KEY_HEX).

Dùng CHUNG một cặp khoá cho TẤT CẢ các tool. Nếu private key lộ ra ngoài,
bất kỳ ai cũng chế được license giả → phải sinh lại cặp mới và cập nhật public key
trong mọi tool.

Chạy:  python make_keys.py
"""
from __future__ import annotations

import binascii
import sys
from pathlib import Path

try:  # cho phép in tiếng Việt trên console Windows (cp1252).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

KEYS_DIR = Path(__file__).resolve().parent / "keys"
PRIV_PATH = KEYS_DIR / "private_key.pem"
PUB_PATH = KEYS_DIR / "public_key.txt"


def main() -> None:
    KEYS_DIR.mkdir(exist_ok=True)

    if PRIV_PATH.exists():
        print(f"!! ĐÃ TỒN TẠI private key: {PRIV_PATH}")
        print("   Nếu tạo mới sẽ làm HỎNG mọi license đã cấp trước đó.")
        ans = input("   Gõ 'YES' để ghi đè, Enter để huỷ: ").strip()
        if ans != "YES":
            print("Đã huỷ.")
            return

    priv = Ed25519PrivateKey.generate()

    # Lưu private key (PEM, KHÔNG mã hoá — hãy giữ file này an toàn tuyệt đối,
    # hoặc đổi sang BestAvailableEncryption(b"mat-khau") nếu muốn có passphrase).
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    PRIV_PATH.write_bytes(priv_pem)

    # Public key dạng raw 32 byte → hex 64 ký tự (để nhúng vào tnt_license.py).
    pub_raw = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    pub_hex = binascii.hexlify(pub_raw).decode()
    PUB_PATH.write_text(pub_hex + "\n", encoding="utf-8")

    print("\n==================== ĐÃ TẠO CẶP KHOÁ ====================")
    print(f"Private key (BÍ MẬT) : {PRIV_PATH}")
    print(f"Public  key (an toàn): {PUB_PATH}")
    print("\n>>> DÁN CHUỖI HEX DƯỚI ĐÂY vào PUBLIC_KEY_HEX trong tnt_license.py:\n")
    print(pub_hex)
    print("\n=========================================================")
    print("NHẮC: KHÔNG commit / KHÔNG gửi file keys/private_key.pem cho bất kỳ ai.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
