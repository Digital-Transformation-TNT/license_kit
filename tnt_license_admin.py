"""
tnt_license_admin.py — APP QUẢN TRỊ LICENSE (GUI) cho TNT.

Gộp mọi việc của người cấp phép vào 1 cửa sổ:
  * Xem/copy MÃ MÁY của máy đang chạy.
  * Sinh / xem / copy cặp khoá (public key để nhúng vào tnt_license.py).
  * Tạo file license.key cho một máy (nhập mã máy → xuất file).
  * Xem danh sách license đã cấp (licenses/registry.csv).

CHỈ DÙNG TRÊN MÁY BẠN. App này đọc keys/private_key.pem đặt CẠNH nó → phải giữ
kín thư mục keys/. KHÔNG phát app này (kèm keys/) cho nhân viên.

Đóng gói:  pyinstaller tnt_license_admin.spec
"""
from __future__ import annotations

import os
os.environ.setdefault("CRYPTOGRAPHY_OPENSSL_NO_LEGACY", "1")  # xem chú thích trong tnt_license.py

import sys
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QGuiApplication, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QDateEdit,
    QMessageBox, QFileDialog, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QSizePolicy,
)

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import tnt_license as tl
import license_registry as reg

# --- Thư mục keys/ đặt CẠNH app (không nhúng vào exe) ---
BASE_DIR = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent)
KEYS_DIR = BASE_DIR / "keys"
PRIV_PATH = KEYS_DIR / "private_key.pem"
PUB_PATH = KEYS_DIR / "public_key.txt"

# --- Màu thương hiệu TNT ---
MAROON = "#3B0000"
ORANGE = "#FF791C"
ORANGE_DARK = "#E0660F"
CREAM = "#FBF6F2"
LINE = "#ECD9D1"
MUTED = "#8A6A5E"

STYLE = f"""
QWidget#central {{ background: {CREAM}; }}
QLabel {{ color: {MAROON}; font-size: 12px; }}
QLabel#h1 {{ font-size: 15px; font-weight: 800; }}
QLabel#muted {{ color: {MUTED}; font-size: 11px; }}
QLabel#ok {{ color: #1F7A3D; font-size: 11px; font-weight: 700; }}
QLabel#warn {{ color: #B23B00; font-size: 11px; font-weight: 700; }}

QFrame#card {{
    background: #FFFFFF; border: 1px solid {LINE}; border-radius: 10px;
}}

QLineEdit, QDateEdit {{
    border: 1px solid #E3CFC6; border-radius: 6px; padding: 5px 7px;
    background: #FFF; color: {MAROON}; min-height: 18px;
}}
QLineEdit:focus, QDateEdit:focus {{ border: 1px solid {ORANGE}; }}
QLineEdit:read-only {{ background: #FAF5F2; color: {ORANGE_DARK}; }}
QLineEdit:disabled, QDateEdit:disabled {{ background: #F2ECE9; color: #B9A79F; }}

QPushButton {{
    background: {ORANGE}; color: #FFF; border: none; border-radius: 6px;
    padding: 6px 12px; font-weight: 700; font-size: 12px;
}}
QPushButton:hover {{ background: {ORANGE_DARK}; }}
QPushButton#ghost {{
    background: #FFF; color: {MAROON}; border: 1px solid #E3CFC6;
    font-weight: 600; padding: 5px 10px;
}}
QPushButton#ghost:hover {{ border-color: {ORANGE}; color: {ORANGE_DARK}; }}
QPushButton#cta {{ padding: 9px 12px; font-size: 13px; }}

QTabWidget::pane {{ border: 1px solid {LINE}; border-radius: 8px; background: #FFF; top: -1px; }}
QTabBar::tab {{
    background: transparent; color: {MUTED}; padding: 7px 14px;
    border: 1px solid transparent; border-top-left-radius: 8px; border-top-right-radius: 8px;
    font-weight: 700; font-size: 12px;
}}
QTabBar::tab:selected {{ background: #FFF; color: {MAROON}; border-color: {LINE}; border-bottom-color: #FFF; }}

QTableWidget {{ border: none; gridline-color: #F0E4DE; font-size: 12px; }}
QHeaderView::section {{
    background: #FAF5F2; color: {MUTED}; border: none;
    border-bottom: 1px solid {LINE}; padding: 5px; font-weight: 700; font-size: 11px;
}}
QCheckBox {{ color: {MAROON}; font-size: 12px; }}
"""

MONO = "Consolas, 'Courier New', monospace"


def _copy(text: str) -> None:
    QGuiApplication.clipboard().setText(text)


def _mono_field(text: str = "") -> QLineEdit:
    """Ô chữ mono, chỉ đọc, chọn/copy được — dùng cho mã máy & public key."""
    ed = QLineEdit(text)
    ed.setReadOnly(True)
    ed.setFont(QFont("Consolas", 9))
    ed.setCursorPosition(0)
    return ed


class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TNT — Quản trị License")
        self.resize(720, 560)
        central = QWidget(objectName="central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(10)

        root.addWidget(self._build_header())

        tabs = QTabWidget()
        tabs.addTab(self._build_issue_tab(), "Cấp license")
        self.tab_list_index = 1
        tabs.addTab(self._build_registry_tab(), "Đã cấp")
        self.tabs = tabs
        root.addWidget(tabs, 1)

        self._refresh_keys_state()
        self._reload_registry()

    # ---------------- Header: mã máy + trạng thái khoá ---------------- #
    def _build_header(self) -> QFrame:
        card = QFrame(objectName="card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # Hàng 1: tiêu đề
        lay.addWidget(QLabel("TNT — Công cụ cấp phép License", objectName="h1"))

        # Hàng 2: mã máy của máy này
        r1 = QHBoxLayout()
        r1.setSpacing(6)
        lbl = QLabel("Máy này:")
        lbl.setFixedWidth(58)
        r1.addWidget(lbl)
        try:
            mid = tl.machine_id_pretty()
        except Exception as e:
            mid = f"(lỗi đọc phần cứng: {e})"
        self.ed_machine_self = _mono_field(mid)
        r1.addWidget(self.ed_machine_self, 1)
        b_copy = QPushButton("Copy", objectName="ghost")
        b_copy.clicked.connect(lambda: (_copy(self.ed_machine_self.text()),
                                        self._toast("Đã copy mã máy.")))
        b_use = QPushButton("Điền vào form", objectName="ghost")
        b_use.clicked.connect(lambda: (self.ed_machine.setText(self.ed_machine_self.text()),
                                       self.tabs.setCurrentIndex(0)))
        r1.addWidget(b_copy)
        r1.addWidget(b_use)
        lay.addLayout(r1)

        # Hàng 3: trạng thái khoá + public key (gọn 1 dòng)
        r2 = QHBoxLayout()
        r2.setSpacing(6)
        lbl2 = QLabel("Khoá ký:")
        lbl2.setFixedWidth(58)
        r2.addWidget(lbl2)
        self.lbl_keys_state = QLabel("…", objectName="ok")
        r2.addWidget(self.lbl_keys_state)
        r2.addWidget(QLabel("public:", objectName="muted"))
        self.ed_pub = _mono_field()
        self.ed_pub.setMaximumWidth(210)
        r2.addWidget(self.ed_pub)
        b_pub = QPushButton("Copy public key", objectName="ghost")
        b_pub.clicked.connect(self._copy_pub)
        r2.addWidget(b_pub)
        b_gen = QPushButton("Sinh khoá mới…", objectName="ghost")
        b_gen.clicked.connect(self._gen_keys)
        r2.addWidget(b_gen)
        r2.addStretch(1)
        lay.addLayout(r2)
        return card

    def _copy_pub(self) -> None:
        if not self.ed_pub.text():
            QMessageBox.warning(self, "Chưa có khoá", "Chưa có cặp khoá. Bấm 'Sinh khoá mới…'.")
            return
        _copy(self.ed_pub.text())
        self._toast("Đã copy public key → dán vào PUBLIC_KEY_HEX trong tnt_license.py")

    def _refresh_keys_state(self) -> None:
        if PRIV_PATH.exists():
            self.lbl_keys_state.setObjectName("ok")
            self.lbl_keys_state.setText("✅ đã có (giữ kín keys/)")
            self.lbl_keys_state.setToolTip(f"private_key.pem tại: {KEYS_DIR}")
            try:
                self.ed_pub.setText(PUB_PATH.read_text(encoding="utf-8").strip())
            except Exception:
                try:
                    priv = serialization.load_pem_private_key(
                        PRIV_PATH.read_bytes(), password=None)
                    raw = priv.public_key().public_bytes(
                        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
                    self.ed_pub.setText(raw.hex())
                except Exception:
                    self.ed_pub.setText("")
        else:
            self.lbl_keys_state.setObjectName("warn")
            self.lbl_keys_state.setText("⚠️ chưa có — bấm 'Sinh khoá mới…'")
            self.ed_pub.setText("")
        # ép áp lại style theo objectName mới
        self.lbl_keys_state.setStyleSheet("")
        self.lbl_keys_state.style().unpolish(self.lbl_keys_state)
        self.lbl_keys_state.style().polish(self.lbl_keys_state)
        self.ed_pub.setToolTip(self.ed_pub.text())

    def _gen_keys(self) -> None:
        if PRIV_PATH.exists():
            r = QMessageBox.warning(
                self, "Xác nhận",
                "ĐÃ CÓ khoá. Sinh khoá mới sẽ làm HỎNG toàn bộ license đã cấp trước đó "
                "và bạn phải cập nhật public key trong mọi tool.\n\nVẫn tiếp tục?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r != QMessageBox.Yes:
                return
        try:
            KEYS_DIR.mkdir(exist_ok=True)
            priv = Ed25519PrivateKey.generate()
            PRIV_PATH.write_bytes(priv.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()))
            pub_hex = priv.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
            PUB_PATH.write_text(pub_hex + "\n", encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không tạo được khoá:\n{e}")
            return
        self._refresh_keys_state()
        QMessageBox.information(
            self, "Đã tạo khoá",
            "Đã tạo cặp khoá mới.\n\nBƯỚC TIẾP: bấm 'Copy public key' và dán vào "
            "PUBLIC_KEY_HEX trong tnt_license.py, rồi copy tnt_license.py đè vào mọi tool.")

    # ---------------- Tab 1: Cấp license ---------------- #
    def _build_issue_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(14, 14, 14, 12)
        outer.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(9)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.ed_machine = QLineEdit()
        self.ed_machine.setPlaceholderText("Dán mã máy nhân viên gửi (có gạch cũng được)…")
        self.ed_machine.setFont(QFont("Consolas", 9))
        form.addRow("Mã máy:", self.ed_machine)

        self.ed_note = QLineEdit()
        self.ed_note.setPlaceholderText("VD: Nguyen Van A — Marketing")
        form.addRow("Nhân viên:", self.ed_note)

        # KHÔNG giới hạn theo tool: license cấp cho MÁY, dùng cho mọi tool TNT.
        # Tool mới sau này chỉ cần nhúng module license là chạy — không phải cấp lại.

        # Hết hạn
        row_exp = QHBoxLayout()
        row_exp.setSpacing(8)
        self.chk_no_expiry = QCheckBox("Không hết hạn")
        self.chk_no_expiry.setChecked(True)
        self.date_expiry = QDateEdit()
        self.date_expiry.setCalendarPopup(True)
        self.date_expiry.setDate(QDate.currentDate().addYears(1))
        self.date_expiry.setDisplayFormat("yyyy-MM-dd")
        self.date_expiry.setEnabled(False)
        self.date_expiry.setFixedWidth(130)
        self.chk_no_expiry.toggled.connect(lambda on: self.date_expiry.setEnabled(not on))
        row_exp.addWidget(self.chk_no_expiry)
        row_exp.addWidget(self.date_expiry)
        row_exp.addStretch(1)
        form.addRow("Hết hạn:", row_exp)

        outer.addLayout(form)

        btn = QPushButton("Tạo license.key →", objectName="cta")
        btn.clicked.connect(self._make_license)
        outer.addWidget(btn)

        self.lbl_result = QLabel("")
        self.lbl_result.setObjectName("ok")
        self.lbl_result.setWordWrap(True)
        self.lbl_result.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        outer.addWidget(self.lbl_result)

        hint = QLabel("License cấp cho MÁY — dùng được cho mọi tool TNT trên máy đó. "
                      "Sau này ra tool mới, nhân viên KHÔNG cần xin license lại: chỉ cần "
                      "license.key sẵn có là tool mới chạy luôn.\n"
                      "Gửi file .key cho nhân viên → đặt cạnh tool hoặc C:\\TNT\\license.key",
                      objectName="muted")
        hint.setWordWrap(True)
        outer.addWidget(hint)
        outer.addStretch(1)
        return w

    def _make_license(self) -> None:
        if not PRIV_PATH.exists():
            QMessageBox.critical(self, "Thiếu khoá",
                                 "Chưa có private key. Bấm 'Sinh khoá mới…' ở trên trước.")
            return
        machine = "".join(c for c in self.ed_machine.text() if c.isalnum()).lower()
        if len(machine) != 64:
            QMessageBox.critical(
                self, "Sai mã máy",
                f"Mã máy sau chuẩn hoá dài {len(machine)} ký tự, cần 64 (hex SHA-256).")
            return

        expires = None
        if not self.chk_no_expiry.isChecked():
            expires = self.date_expiry.date().toString("yyyy-MM-dd")
            if datetime.strptime(expires, "%Y-%m-%d").date() < date.today():
                r = QMessageBox.question(
                    self, "Hạn ở quá khứ",
                    f"Hạn {expires} đã qua → license hết hạn ngay. Vẫn tạo?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if r != QMessageBox.Yes:
                    return

        # tools = None  →  license dùng được cho MỌI tool (không giới hạn theo tool).
        tools = None

        payload = {
            "machine_id": machine,
            "expires": expires,
            "tools": tools,
            "issued": date.today().isoformat(),
            "note": self.ed_note.text().strip(),
        }
        try:
            priv = serialization.load_pem_private_key(PRIV_PATH.read_bytes(), password=None)
            sig = priv.sign(tl._canonical_payload_bytes(payload))
            license_text = tl.encode_license(payload, sig)
            tl.verify_license_text(license_text, (tools or ["*"])[0],
                                   this_machine_id=machine)   # tự kiểm lại cho chắc
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không tạo được license:\n{e}")
            return

        safe = "".join(c for c in (self.ed_note.text().strip() or machine[:12])
                       if c.isalnum() or c in "-_ ").strip() or machine[:12]
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu license.key", str(BASE_DIR / "licenses" / f"{safe}.key"),
            "License (*.key);;All files (*)")
        if not path:
            return
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(license_text, encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi ghi file", str(e))
            return

        try:
            reg.append_record(BASE_DIR, note=self.ed_note.text().strip(),
                              machine_id=machine, expires=expires, tools=tools,
                              file_path=path)
            self._reload_registry()
        except Exception:
            pass

        self.lbl_result.setText(
            f"✅ Đã tạo: {Path(path).name}  ·  "
            f"{self.ed_note.text().strip() or '(không ghi chú)'}  ·  "
            f"hạn: {expires or 'vĩnh viễn'}")
        self._toast(f"Đã lưu: {path}")

    # ---------------- Tab 2: Danh sách đã cấp ---------------- #
    def _build_registry_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 10)
        lay.setSpacing(8)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Ngày cấp", "Nhân viên", "Mã máy", "Hết hạn", "Tool"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        lay.addWidget(self.table, 1)

        row = QHBoxLayout()
        self.lbl_count = QLabel("", objectName="muted")
        row.addWidget(self.lbl_count, 1)
        b1 = QPushButton("Làm mới", objectName="ghost")
        b1.clicked.connect(self._reload_registry)
        b2 = QPushButton("Mở thư mục licenses", objectName="ghost")
        b2.clicked.connect(self._open_licenses_dir)
        row.addWidget(b1)
        row.addWidget(b2)
        lay.addLayout(row)
        return w

    def _reload_registry(self) -> None:
        try:
            records = reg.read_records(BASE_DIR)
        except Exception:
            records = []
        self.table.setRowCount(0)
        for rec in reversed(records):   # mới nhất lên đầu
            r = self.table.rowCount()
            self.table.insertRow(r)
            mid = rec.get("machine_id", "")
            vals = [rec.get("issued", ""), rec.get("note", ""),
                    (mid[:10] + "…") if len(mid) > 11 else mid,
                    rec.get("expires", ""), rec.get("tools", "")]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 2:
                    item.setFont(QFont("Consolas", 9))
                    item.setToolTip(mid)   # hover xem đủ mã máy
                self.table.setItem(r, c, item)
        self.lbl_count.setText(f"Tổng: {len(records)} license đã cấp")
        if hasattr(self, "tabs"):
            self.tabs.setTabText(self.tab_list_index, f"Đã cấp ({len(records)})")

    def _open_licenses_dir(self) -> None:
        d = BASE_DIR / "licenses"
        d.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(d))   # Windows
        except Exception:
            QMessageBox.information(self, "Thư mục", str(d))

    def _toast(self, msg: str) -> None:
        self.statusBar().showMessage(msg, 4000)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TNT License Admin")
    app.setStyleSheet(STYLE)
    win = AdminWindow()
    win.show()
    try:
        scr = app.primaryScreen().availableGeometry()
        fg = win.frameGeometry(); fg.moveCenter(scr.center()); win.move(fg.topLeft())
    except Exception:
        pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
