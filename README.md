# FlashFree

Ứng dụng thẻ từ vựng tiếng Anh cho người học tiếng Việt. Chạy hoàn toàn trên trình duyệt: không tài khoản, không máy chủ riêng. Tiến độ (SM-2, chuỗi ngày, bộ thẻ đang chọn) lưu trong `localStorage` của máy bạn.

Mặt trước thẻ là từ tiếng Anh và phiên âm IPA nếu có. Với từ cụ thể, mặt trước còn một emoji gợi nhớ (Unicode, trong `data/icons.json`). Mặt sau là nghĩa tiếng Việt, từ loại, và một câu ví dụ Anh–Việt khi Tatoeba có câu phù hợp. Bấm **Biết** / **Chưa biết**, hoặc vuốt phải / trái. Nút loa đọc từ bằng giọng en-US của trình duyệt (Web Speech API).

Khi một thẻ hiện ra hoặc khi bạn chạm để lật, app cũng tự đọc từ tiếng Anh nếu mục **Tự đọc khi lật thẻ** đang bật (mặc định bật, trong Bộ thẻ). Nút loa vẫn dùng được khi tắt tự đọc. Trình duyệt nào chỉ cho đọc sau một lần chạm (như iOS Safari) thì lần hiện thẻ đầu tiên, trước khi bạn chạm, sẽ im; chạm để lật hoặc bấm loa vẫn đọc được.

Nút **+** ở góc trên mở form thêm từ của bạn: tiếng Anh, nghĩa tiếng Việt, từ loại, câu ví dụ, emoji. Các từ nằm trong bộ **Từ của tôi**, chọn như bộ khác, và ôn bằng cùng lịch SM-2. Từ mới bạn thêm được đưa vào phiên hôm nay, không tính vào hạn thẻ mới của bộ sẵn. Sửa hoặc xóa được; xóa có hỏi lại. Nếu từ đã có trong bộ sẵn, form đề nghị điền nghĩa từ đó.

Thống kê giữ chuỗi ngày. Cứ 7 ngày học liên tiếp bạn được 1 lần **đóng băng chuỗi**, trữ tối đa 2. Nghỉ đúng số ngày còn đóng băng thì chuỗi không bị xóa; nghỉ nhiều hơn thì chuỗi về 0 và lần đóng băng còn lại được giữ. Huy chương mở ở mốc chuỗi 3, 7, 14, 30, 60, 100, 200, 365 ngày và mốc từ đã học 50, 100, 250, 500, 1000, 2500. Mỗi lượt ôn cộng 1 XP, mỗi lần **Biết** cộng thêm 2 XP. Dải 14 ngày cho biết số lượt ôn và số từ bạn thêm trong ngày.

Lần đầu mở, app chọn sẵn trình độ **B1** và **B2**. Tiến độ cũ trong `localStorage` được giữ khi cập nhật; không có bước xóa dữ liệu.

## Chạy trên máy

Cần một máy chủ tĩnh. Mở file `index.html` trực tiếp thì trình duyệt chặn việc tải `data/vocab.json`.

```bash
python3 -m http.server 47321
```

Rồi mở http://127.0.0.1:47321

## Đưa lên GitHub Pages

Không có bước build. Thư mục gốc của repo là trang web. Repo xuất bản tại https://tuanlmogle.github.io/flashfree/.

File `.github/workflows/pages.yml` đẩy trang lên GitHub Pages mỗi lần có commit trên nhánh `main` (`actions/upload-pages-artifact` rồi `actions/deploy-pages`). Trong Settings → Pages, chọn nguồn **GitHub Actions** một lần.

CSS, JavaScript, font, `data/vocab.json` và `data/icons.json` dùng đường dẫn tương đối, nên cùng một bản chạy ở gốc máy chủ local, dưới `/flashfree/`, và trên một tên miền riêng sau này. Trang không gắn `<base>` theo tên thư mục. Nếu địa chỉ là một thư mục mà thiếu dấu `/` cuối, trang tự thêm dấu đó trước khi tải file. Emoji trong `icons.json` là ký tự Unicode do app chọn, không lấy từ bộ tranh của ứng dụng khác.

Netlify hoặc Vercel cũng chạy được: publish directory là `.`, không cần build command. Không cần biến môi trường.

## Tạo lại dữ liệu từ vựng

```bash
python3 scripts/build_vocab.py
```

Script tải các nguồn trong `DATA_SOURCES.md` vào `data/raw/` (thư mục này không được commit), rồi ghi `data/vocab.json`. Lần chạy sau dùng bản đã tải nếu file còn đó. Xóa `data/raw/` nếu bạn muốn tải lại từ đầu.

Chi tiết giấy phép và cách trích dẫn nằm ở `DATA_SOURCES.md` và trang **Nguồn** trong app.
