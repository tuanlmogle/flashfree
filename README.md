# FlashFree

Ứng dụng thẻ từ vựng tiếng Anh cho người học tiếng Việt. Chạy hoàn toàn trên trình duyệt: không tài khoản, không máy chủ riêng. Tiến độ (SM-2, chuỗi ngày, bộ thẻ đang chọn) lưu trong `localStorage` của máy bạn.

Mặt trước thẻ là từ tiếng Anh và phiên âm IPA nếu có. Mặt sau là nghĩa tiếng Việt, từ loại, và một câu ví dụ Anh–Việt khi Tatoeba có câu phù hợp. Bấm **Biết** / **Chưa biết**, hoặc vuốt phải / trái. Nút loa đọc từ bằng giọng en-US của trình duyệt (Web Speech API).

Lần đầu mở, app chọn sẵn trình độ **B1** và **B2**.

## Chạy trên máy

Cần một máy chủ tĩnh. Mở file `index.html` trực tiếp thì trình duyệt chặn việc tải `data/vocab.json`.

```bash
python3 -m http.server 47321
```

Rồi mở http://127.0.0.1:47321

## Đưa lên GitHub Pages

Không có bước build. Thư mục gốc của repo là trang web. Repo xuất bản tại https://tuanlmogle.github.io/flashfree/.

File `.github/workflows/pages.yml` đẩy trang lên GitHub Pages mỗi lần có commit trên nhánh `main` (`actions/upload-pages-artifact` rồi `actions/deploy-pages`). Trong Settings → Pages, chọn nguồn **GitHub Actions** một lần.

CSS, JavaScript, font và `data/vocab.json` dùng đường dẫn tương đối, nên cùng một bản chạy ở gốc máy chủ local, dưới `/flashfree/`, và trên một tên miền riêng sau này. Trang không gắn `<base>` theo tên thư mục. Nếu địa chỉ là một thư mục mà thiếu dấu `/` cuối, trang tự thêm dấu đó trước khi tải file.

Netlify hoặc Vercel cũng chạy được: publish directory là `.`, không cần build command. Không cần biến môi trường.

## Tạo lại dữ liệu từ vựng

```bash
python3 scripts/build_vocab.py
```

Script tải các nguồn trong `DATA_SOURCES.md` vào `data/raw/` (thư mục này không được commit), rồi ghi `data/vocab.json`. Lần chạy sau dùng bản đã tải nếu file còn đó. Xóa `data/raw/` nếu bạn muốn tải lại từ đầu.

Chi tiết giấy phép và cách trích dẫn nằm ở `DATA_SOURCES.md` và trang **Nguồn** trong app.
