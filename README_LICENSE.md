# TNT License Kit — Lớp bảo mật license DÙNG CHUNG cho các tool local

Một cặp khoá, một public key, một file `license.key` mỗi máy — dùng cho **mọi** tool.
Chống chạy lậu bằng **chữ ký số Ed25519** + **gắn theo mã máy (machine fingerprint)**.

---

## 0. Có gì trong thư mục này

| File | Vai trò | Bí mật? |
|------|---------|---------|
| `tnt_license.py` | **Module dùng chung** — nhúng vào mọi tool. Chứa public key + toàn bộ logic kiểm. | ✅ An toàn phát đi |
| `make_keys.py` | Sinh cặp khoá (chạy **một lần**). | Script an toàn; **output thì không** |
| `make_license.py` | Tạo `license.key` cho một máy (chạy ở máy bạn). | ✅ Script an toàn |
| `tnt_license_admin.py` | **App GUI** gộp mọi việc cấp phép (sinh khoá + tạo license). Đóng gói thành `.exe`. | ✅ Script an toàn; **exe kèm keys/ thì KHÔNG** |
| `tnt_license_admin.spec` | Spec PyInstaller để build app admin. | ✅ An toàn |
| `lay_ma_may.py` / `.spec` | **App nhỏ** cho nhân viên: double-click → hiện mã máy + nút Copy. | ✅ An toàn phát đi |
| `license_registry.py` | Ghi/đọc **sổ đăng ký** `licenses/registry.csv`. | ✅ Script an toàn; **registry.csv thì giữ ở máy bạn** |
| `whoami_machine.py` | Bản console của "lấy mã máy" (nếu không cần GUI). | ✅ An toàn |
| `keys/private_key.pem` | **KHOÁ BÍ MẬT** để ký license. | 🔴 **TUYỆT MẬT** |
| `keys/public_key.txt` | Public key (đã nhúng sẵn vào `tnt_license.py`). | ✅ An toàn |
| `licenses/*.key` | Các license đã cấp. | Không cần giữ kín, nhưng chỉ chạy đúng 1 máy |

> ⚠️ **Đã có sẵn 1 cặp khoá** trong `keys/` và public key đã được nhúng vào `tnt_license.py`.
> Bạn có thể dùng luôn. Chỉ chạy lại `make_keys.py` nếu muốn tạo cặp khoá **mới**
> (khi đó phải nhúng lại public key và **cấp lại toàn bộ** license cũ).

---

## 1. ⭐ KHI TẠO TOOL MỚI THÌ LÀM GÌ (phần quan trọng nhất)

Chỉ **3 bước**, khoảng 2 phút:

1. **Copy** `tnt_license.py` vào thư mục tool mới (cạnh file chạy chính).
   ```
   copy tnt_license.py  D:\...\tool_moi\
   ```
2. **Thêm 2 dòng** vào đầu hàm khởi động của tool:
   ```python
   from tnt_license import check_license
   check_license("TEN_TOOL_MOI")   # đặt tên riêng, vd "TNT_ImageResize"
   ```
   Đặt **ngay dòng đầu** của `main()` — trước khi mở cửa sổ / làm gì khác.
3. Nếu đóng gói PyInstaller, thêm vào `hiddenimports` trong file `.spec`:
   ```python
   hiddenimports += ["tnt_license", "cryptography"]
   ```

Xong. Tool mới được bảo vệ, **dùng chung** `license.key` với các tool khác trên cùng máy.

> Muốn "máy này được dùng tool mới đó" → khi cấp license thêm tên tool vào `--tools`,
> hoặc cấp license **không kèm** `--tools` (mặc định = mọi tool).

---

## 2. Thiết lập lần đầu (chỉ làm 1 lần, đã làm sẵn cho bạn)

Nếu cần làm lại từ đầu (ví dụ đổi cặp khoá):

```bash
cd tnt_license_kit
pip install cryptography
python make_keys.py           # sinh keys/private_key.pem + in ra PUBLIC KEY (hex)
```
Copy chuỗi hex vừa in → dán vào `tnt_license.py`:
```python
PUBLIC_KEY_HEX = "….64 ký tự hex…."
```
Rồi copy `tnt_license.py` (đã có public key mới) đè lên bản trong **mọi** tool.

---

## 2b. ⭐ App GUI (.exe) — cách dùng dễ nhất (khuyến nghị)

Thay cho việc gõ lệnh `make_keys.py` / `make_license.py`, có sẵn **1 app cửa sổ**
gộp hết: xem mã máy, sinh khoá, tạo `license.key`.

**Build (1 lần):**
```bash
cd tnt_license_kit
pip install cryptography PySide6 pyinstaller
pyinstaller tnt_license_admin.spec
```
Ra: `dist/TNT_License_Admin/TNT_License_Admin.exe` (kèm `HUONG_DAN_SU_DUNG.txt`).

**Dùng:**
- Đặt thư mục `keys/` (chứa `private_key.pem`) **cạnh** file `.exe`. Nếu chưa có,
  mở app → mục 2 → “Sinh cặp khoá MỚI”.
- Mục 1: xem/copy **mã máy** của máy đang chạy.
- Mục 2: sinh khoá + **copy public key** (dán vào `tnt_license.py`).
- Mục 3: dán mã máy nhân viên → chọn hạn/tool → **“Tạo license.key →”** → lưu file.

> 🔴 `dist/TNT_License_Admin/keys/private_key.pem` là **TỐI MẬT**. App admin (kèm
> `keys/`) chỉ ở máy bạn — **không** phát cho nhân viên. `.gitignore` đã chặn `dist/`.

---

## 2c. Data lưu ở đâu & nhân viên lấy mã máy thế nào

**Data license lưu ở đâu:** cạnh app admin, trong thư mục `licenses/`:
- `licenses/<TenNV>.key` — từng file license đã cấp.
- `licenses/registry.csv` — **sổ đăng ký tổng** (ngày cấp, tên NV, mã máy, hạn, tool),
  tự cập nhật mỗi lần tạo. Mở bằng Excel để tra cứu; app hiện bảng này ở **mục 4**.
  Đây chính là "database" người dùng + license của bạn. Nên sao lưu định kỳ.

**Nhân viên lấy mã máy (nhanh) — 2 cách:**
- **A. Mở thẳng tool chính:** máy chưa có license → tool tự hiện hộp thoại **mã máy
  + nút "📋 Copy mã máy"** và lưu `machine_id.txt` cạnh tool.
- **B. Dùng `TNT_LayMaMay.exe`:** app nhẹ, double-click là ra mã máy + nút Copy
  (build bằng `pyinstaller lay_ma_may.spec`).

---

## 3. Cấp phép cho một nhân viên mới (dòng lệnh — nếu không dùng app GUI)

**Nhân viên:** chạy tool lần đầu (chưa có license) → hiện **MÃ MÁY** trên màn hình và
lưu vào `machine_id.txt` cạnh tool. (Hoặc chạy `whoami_machine.py`.) Gửi mã máy đó cho bạn.

**Bạn** (trên máy có `private_key.pem`):
```bash
# Full quyền, vô thời hạn:
python make_license.py --machine <MÃ_MÁY> --note "Nguyen Van A"

# Giới hạn tool + có hạn dùng:
python make_license.py --machine <MÃ_MÁY> --expires 2026-12-31 \
       --tools TNT_Listing,TNT_VideoSubtitle --note "Nguyen Van A"
```
Ra file `licenses/Nguyen Van A.key`. **Đổi tên thành `license.key`**, gửi cho nhân viên.

**Nhân viên:** đặt `license.key` vào **một trong hai** chỗ:
- cạnh file chạy của tool, **hoặc**
- `C:\TNT\license.key` (đường dẫn chung — 1 file dùng cho mọi tool trên máy).

> Đổi đường dẫn chung: sửa `COMMON_LICENSE_PATH` trong `tnt_license.py`, hoặc đặt biến
> môi trường `TNT_LICENSE_PATH` trỏ thẳng tới file.

---

## 4. Các phép kiểm mỗi lần tool khởi động

Chỉ cần **một** cái sai là từ chối và thoát:
1. **Chữ ký** khớp public key? → chống license giả / bị sửa.
2. **Mã máy** trong license == mã máy tính lại từ máy đang chạy? → chống copy sang máy khác.
3. **Còn hạn** không? (nếu license có đặt hạn).
4. **Tool này có trong danh sách được phép** không? (nếu license có `--tools`).

Mã máy = SHA-256 của các định danh phần cứng **ổn định**:
- Windows: `MachineGuid` (registry) + `UUID` mainboard + serial ổ hệ thống.
- macOS: `IOPlatformUUID` + serial máy.
Tránh IP/tên máy (dễ đổi). Ổn định qua reboot, không đổi nếu phần cứng không đổi.

---

## 5. File nào BÍ MẬT, file nào AN TOÀN phát đi

🔴 **KHÔNG BAO GIỜ** đưa ra ngoài (giữ trên máy bạn / backup nơi an toàn):
- `keys/private_key.pem` ← lộ file này là **toi**: ai cũng chế được license giả.

✅ **An toàn** để đóng gói vào exe và phát cho nhân viên:
- `tnt_license.py` (chỉ có public key)
- `license.key` của **đúng** máy đó (máy khác dùng cũng vô dụng)

> `.gitignore` đã chặn sẵn `keys/`, `*.pem`, `licenses/`, `*.key`. **Đừng** đóng gói
> `license.key` của bạn vào bản build phát hành — mỗi nhân viên nhận file riêng.

---

## 6. Đóng gói & làm khó dịch ngược (Python)

Python dễ đọc ngược, nên nên:
1. **PyInstaller** (đã có `.spec` sẵn cho cả 2 tool) → ra 1 thư mục exe.
2. **Obfuscate** thêm bằng **PyArmor** (khuyến nghị) để mã hoá bytecode:
   ```bash
   pip install pyarmor
   pyarmor gen --pack onefile app.py tnt_license.py
   ```
3. `console=False` trong `.spec` (đã đặt) để app không hiện cửa sổ đen.

**Giới hạn thật lòng:** không có giải pháp offline nào chống được kẻ tấn công đủ giỏi.
Startup check kiểu `check_license()` **có thể bị patch** (sửa bytecode để bỏ qua).
Muốn khó hơn hẳn → xem mục 7 (mã hoá phần lõi) + PyArmor.

---

## 7. (Nâng cao) Ràng buộc MẠNH: mã hoá phần lõi bằng khoá phái sinh từ license

Thay vì chỉ chặn bằng một câu `if`, có thể khiến **thiếu license hợp lệ thì phần
lõi không giải mã được** (không chỉ là cờ boolean):

```python
info = check_license("TEN_TOOL")               # ném/thoát nếu sai
data = tnt_license.unlock_secret(info, blob)   # blob mã hoá kèm trong app
```
`derive_fernet_key(info)` sinh khoá gắn chặt với **license + máy này**. Bạn mã hoá sẵn
một thứ tool **bắt buộc phải có** (endpoint API, prompt lõi, tham số thuật toán…) bằng
khoá đó; không có license đúng máy thì không dựng lại được khoá → không giải mã được →
patch câu `if` cũng vô dụng. (Đây là tuỳ chọn; 2 tool hiện tại đang dùng startup check.)

---

## 8. Điểm yếu của phương án offline & hướng nâng cấp

**Điểm yếu:**
- Không **thu hồi từ xa** được: nhân viên nghỉ việc vẫn dùng tới khi license hết hạn.
  → Giảm nhẹ bằng cách cấp license **có hạn ngắn** (`--expires`), gia hạn định kỳ.
- Startup check có thể bị patch (xem mục 6–7).
- Đổi phần cứng lớn (thay mainboard/ổ hệ thống) → mã máy đổi → phải cấp lại license.

**Nâng cấp thu hồi từ xa (khi cần):**
- Dựng 1 **server nhỏ**: tool định kỳ "gọi về" gửi mã máy → server trả *còn hiệu lực?*
  + hạn mới. Nghỉ việc = tắt trên server là mất quyền ngay lần kiểm sau.
- Hoặc chuyển hẳn sang **xác thực bằng tài khoản công ty** (Google Workspace / Microsoft
  365 qua OAuth) thay vì license gắn máy — sạch hơn về lâu dài, thu hồi tức thì bằng
  cách khoá tài khoản. Đánh đổi: tool cần mạng lúc đăng nhập.
