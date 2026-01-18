# SizeFolder GUI (PharmApp themed)

Một tiện ích desktop nhẹ, đa nền tảng để quét **các thư mục con cấp 1** (immediate subfolders) của một thư mục gốc và tính **tổng dung lượng** của từng thư mục con. Công cụ phù hợp để “triage” nhanh ổ đĩa (xác định thư mục nào đang chiếm dung lượng), với **quét đa luồng**, **dừng/huỷ**, **lọc**, **sắp xếp cột**, và **xuất CSV**.

## Tính năng chính

- Quét **thư mục con cấp 1** dưới thư mục *Root* đã chọn
- Tính dung lượng đệ quy với tuỳ chọn **Max depth**
- Quét I/O **đa luồng** (tuỳ chỉnh số luồng)
- Nút **Stop** (Esc) để dừng tác vụ đang chạy
- **Exclude patterns** (glob, phân tách bằng dấu phẩy): `.git`, `node_modules`, `__pycache__`, ...
- Ô **Filter** để tìm nhanh trong kết quả
- **Sắp xếp theo cột** (bấm tiêu đề cột để đảo ▲/▼)
- Chế độ **Top‑N** (chỉ hiển thị N thư mục lớn nhất)
- **Xuất CSV** (`folder, bytes, human_readable, absolute_path`)
- Đa nền tảng: Windows / macOS / Linux (Tkinter)

## Ảnh minh hoạ

Nên bổ sung ảnh chụp màn hình:
- `./docs/screenshot_scan.png`
- `./docs/screenshot_help.png`

## Yêu cầu

- Python **3.8+**
- Tkinter (thường có sẵn trong bộ cài Python; một số bản Linux cần cài thêm)

Không cần thư viện Python bên thứ ba.

## Chạy nhanh

### 1) Chạy từ mã nguồn

```bash
python size_folder_gui_gui_v1.py
```

Bạn có thể đổi tên file thành `size_folder_gui.py` rồi chạy:

```bash
python size_folder_gui.py
```

### 2) Cách dùng

1. Chọn thư mục **Root**
2. Điều chỉnh tuỳ chọn (nếu cần):
   - **Exclude**: mẫu glob, phân tách bằng dấu phẩy
   - **Max depth**: độ sâu đệ quy (0 = chỉ root; 1 = con; 2 = cháu; ...)
   - **Threads**: số worker chạy song song
   - **Top‑N**: chỉ hiển thị N kết quả lớn nhất (0 = hiển thị tất cả)
   - **De‑dupe hardlinks**: tránh đếm trùng file hardlink
3. Bấm **Scan**
4. (Tuỳ chọn) bấm **Save CSV**

## Phím tắt

- **Ctrl/⌘ + O**: Chọn thư mục root
- **Ctrl/⌘ + R**: Bắt đầu quét
- **Ctrl/⌘ + S**: Lưu CSV
- **Ctrl/⌘ + F**: Focus vào ô Filter
- **F1**: Chuyển sang tab Help
- **Esc**: Dừng quét

## Giải thích kết quả

- **Bytes** là dung lượng logic của file (`st_size`), không nhất thiết bằng dung lượng cấp phát thực tế trên đĩa.
- Trên Windows, công cụ có dùng tiền tố `\\?\` để hỗ trợ đường dẫn rất dài tốt hơn.
- Không follow symlink.

## Định dạng CSV

File CSV xuất ra gồm:

| Cột | Ý nghĩa |
|---|---|
| `folder` | Tên thư mục con (basename) |
| `bytes` | Tổng dung lượng (bytes) |
| `human_readable` | Dung lượng dạng KB/MB/GB/... |
| `absolute_path` | Đường dẫn đầy đủ |

## Build file chạy độc lập (PyInstaller)

> Tuỳ chọn. Chỉ cần nếu bạn muốn đóng gói ứng dụng.

### Windows (EXE một file)

```powershell
py -3 -m pip install pyinstaller
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name SizeFolderGUI `
  --icon .\nct_logo.ico `
  --add-data "nct_logo.png;." `
  size_folder_gui_gui_v1.py
```

### macOS (.app)

```bash
python3 -m pip install pyinstaller
python3 -m PyInstaller --noconfirm --clean --windowed \
  --name SizeFolderGUI \
  --icon ./nct_logo.icns \
  --add-data "nct_logo.png:." \
  size_folder_gui_gui_v1.py
```

Ghi chú:
- Lần chạy đầu trên macOS có thể bị Gatekeeper chặn; dùng right‑click → Open.
- Nếu phát hành rộng rãi, nên codesign và notarize.

## Liên kết dự án

- Sản phẩm / demo: **www.pharmapp.dev**
- Bài viết & tài liệu: **www.nghiencuuthuoc.com**

## License

Bạn có thể chọn:
- MIT (khuyến nghị cho tiện ích mã nguồn mở), hoặc
- Proprietary / chỉ dùng nội bộ

Nếu chọn MIT, hãy thêm file `LICENSE` ở thư mục gốc repo.
