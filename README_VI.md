# SizeFolder GUI (PharmApp Theme)

Ứng dụng desktop Tkinter đa nền tảng giúp quét **các thư mục con cấp 1** dưới một thư mục gốc và tính tổng dung lượng cho từng thư mục con, có **đa luồng**, **dừng (Stop)**, **tiến trình realtime**, **lọc**, **sắp xếp cột**, và **xuất CSV**. fileciteturn0file0L1-L9

## Tính năng

- Quét các thư mục con cấp 1 và tính tổng dung lượng (bytes + hiển thị dễ đọc). fileciteturn0file0L1-L9  
- Quét đa luồng, có nút **Stop** để dừng giữa chừng. fileciteturn0file0L1-L9  
- **Exclude patterns** theo glob, nhập dạng danh sách phân tách dấu phẩy: ví dụ `.git,node_modules,__pycache__`. fileciteturn0file0L169-L179  
- Tuỳ chọn **Max depth** để giới hạn độ sâu quét. fileciteturn0file0L62-L80  
- Tuỳ chọn **De-dupe hardlinks** để tránh đếm trùng file hardlink. fileciteturn0file0L62-L80  
- Sắp xếp tất cả cột (bấm tiêu đề để đảo chiều ▲/▼). fileciteturn0file0L9-L9  
- Ô **Filter** để lọc theo tên thư mục hoặc đường dẫn. fileciteturn0file0L190-L195  
- Menu chuột phải: mở thư mục, reveal trong file manager, copy path. fileciteturn0file0L219-L239  
- Xuất CSV (`folder, bytes, human_readable, absolute_path`). fileciteturn0file0L311-L327  
- Hỗ trợ đường dẫn dài trên Windows bằng tiền tố `\\?\\`. fileciteturn0file0L36-L47  

## Yêu cầu

- Python 3.9+ (khuyến nghị)
- Không cần thư viện ngoài (chỉ dùng standard library)

## Chạy chương trình

```bash
python size_folder_gui_gui_v1.py
```

> Ứng dụng sẽ mở GUI. Chọn thư mục gốc, sau đó bấm **Scan**.

## Phím tắt

- **Ctrl/⌘ + O**: Chọn thư mục gốc fileciteturn0file0L141-L149  
- **Ctrl/⌘ + R**: Bắt đầu quét fileciteturn0file0L141-L149  
- **Ctrl/⌘ + S**: Lưu CSV fileciteturn0file0L141-L149  
- **Ctrl/⌘ + F**: Focus ô Filter fileciteturn0file0L141-L149  
- **F1**: Mở tab Help fileciteturn0file0L141-L149  
- **Esc**: Dừng quét fileciteturn0file0L141-L149  

## Cơ chế hoạt động

1. Liệt kê các thư mục con cấp 1 của thư mục gốc. fileciteturn0file0L50-L60  
2. Tính dung lượng từng thư mục bằng `os.scandir()` (không theo symlink). fileciteturn0file0L62-L114  
3. Chạy song song theo thư mục con bằng `ThreadPoolExecutor`. fileciteturn0file0L344-L387  
4. Đưa tiến trình/kết quả về GUI qua queue an toàn luồng. fileciteturn0file0L284-L309  

## CSV Output

Các cột trong CSV theo thứ tự: fileciteturn0file0L311-L327

- `folder`
- `bytes`
- `human_readable`
- `absolute_path`

## Đóng gói (PyInstaller)

### Windows (EXE)

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
python3 -m PyInstaller --noconfirm --clean --windowed --name SizeFolderGUI \
  --icon ./nct_logo.icns \
  --add-data "nct_logo.png:." \
  size_folder_gui_gui_v1.py
```

## Branding

- Icon runtime: `nct_logo.png` fileciteturn0file0L23-L35  
- Màu theme nằm ở phần constants đầu file. fileciteturn0file0L17-L28  

### Website

Website chính thức: **www.pharmapp.dev**.

Nếu muốn footer trong app hiển thị đúng website mới, chỉnh chuỗi footer trong code:

- `self.var_footer = "... | www.pharmapp.dev"` (footer ở Scan tab). fileciteturn0file0L254-L258  

## License

Bạn có thể chọn license (ví dụ MIT) và thêm file `LICENSE` sau.

---

© 2026 | PharmApp | www.pharmapp.dev | www.nghiencuuthuoc.com
