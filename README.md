# FlashFree

Ứng dụng thẻ từ vựng tiếng Anh cho người học tiếng Việt. Chạy hoàn toàn trên trình duyệt: không tài khoản, không máy chủ riêng. Tiến độ (SM-2, chuỗi ngày, bộ thẻ đang chọn) lưu trong `localStorage` của máy bạn.

Mặt trước thẻ là từ tiếng Anh và phiên âm IPA nếu có. Ảnh có thể là sticker Fluent Emoji, emoji phẳng (Twemoji, Noto, OpenMoji) hoặc ảnh Commons. Nút **↻** đổi hình, lựa chọn được nhớ theo từng từ. Nút **i** ghi tác giả và giấy phép. Không có ảnh thì dùng emoji Unicode trong `data/icons.json`. Thẻ không có nghĩa tiếng Việt hiện nhãn **EN** và dòng **Giải nghĩa tiếng Anh**. Mặt sau là nghĩa tiếng Việt, từ loại, và một câu ví dụ Anh–Việt khi Tatoeba có câu phù hợp. Bấm **Biết** / **Chưa biết**, hoặc vuốt phải / trái. Nút loa đọc từ bằng giọng en-US của trình duyệt (Web Speech API).

Ở mục Học có ba cách: **Thẻ** (lật như trên), **Nghe** (đọc từ, nghỉ, đọc nghĩa tiếng Việt nếu máy có giọng vi-VN, rồi đọc câu ví dụ, sau đó sang thẻ sau; có tạm dừng, tốc độ và số lần lặp; không ghi vào lịch ôn), và **Điền** (câu ví dụ bị khoét từ, chọn 1 trong 4 hoặc gõ; đúng tính là Biết, sai tính là Chưa biết). Bộ thẻ còn cho chọn màu giao diện, kể cả chế độ tối. Lựa chọn lưu trên máy.

Khi một thẻ hiện ra hoặc khi bạn chạm để lật, app cũng tự đọc từ tiếng Anh nếu mục **Tự đọc khi lật thẻ** đang bật (mặc định bật, trong Bộ thẻ). Nút loa vẫn dùng được khi tắt tự đọc. Trình duyệt nào chỉ cho đọc sau một lần chạm (như iOS Safari) thì lần hiện thẻ đầu tiên, trước khi bạn chạm, sẽ im; chạm để lật hoặc bấm loa vẫn đọc được.

Nút **+** ở góc trên mở form thêm từ của bạn: tiếng Anh, nghĩa tiếng Việt, từ loại, câu ví dụ, emoji. Các từ nằm trong bộ **Từ của tôi**, chọn như bộ khác, và ôn bằng cùng lịch SM-2. Từ mới bạn thêm được đưa vào phiên hôm nay, không tính vào hạn thẻ mới của bộ sẵn. Sửa hoặc xóa được; xóa có hỏi lại. Nếu từ đã có trong bộ sẵn, form đề nghị điền nghĩa từ đó.

Thống kê giữ chuỗi ngày. Một ngày chỉ tính vào chuỗi khi bạn trả lời ít nhất 20 thẻ (hằng số `STREAK_MIN` trong `js/progress.js`). Nhật ký từng thẻ vẫn được giữ. Cứ 7 ngày đủ 20 thẻ bạn được 1 lần **đóng băng chuỗi**, trữ tối đa 2. Nghỉ đúng số ngày còn đóng băng thì chuỗi không bị xóa; nghỉ nhiều hơn thì chuỗi về 0 và lần đóng băng còn lại được giữ. Huy chương mở ở mốc chuỗi 3, 7, 14, 30, 60, 100, 200, 365 ngày và mốc từ đã học 50, 100, 250, 500, 1000, 2500. Mỗi lượt ôn cộng 1 XP, mỗi lần **Biết** cộng thêm 2 XP. Dải 14 ngày cho biết số lượt ôn và số từ bạn thêm trong ngày.

Lần đầu mở, app chọn sẵn trình độ **B1** và **B2**. Tiến độ cũ trong `localStorage` (khóa `latu-state-v1`) được giữ: id thẻ không đổi, nên lịch SM-2 vẫn khớp. Chủ đề cũ đã bỏ tên được đổi sang chủ đề mới tương ứng. Không có bước xóa dữ liệu.

## Chạy trên máy

Cần một máy chủ tĩnh. Mở file `index.html` trực tiếp thì trình duyệt chặn việc tải `data/meta.json`.

```bash
python3 -m http.server 47321
```

Rồi mở http://127.0.0.1:47321

## Đưa lên GitHub Pages

Không có bước build. Thư mục gốc của repo là trang web. Repo xuất bản tại https://tuanlmogle.github.io/flashfree/.

File `.github/workflows/pages.yml` đẩy trang lên GitHub Pages mỗi lần có commit trên nhánh `main` (`actions/upload-pages-artifact` rồi `actions/deploy-pages`). Trong Settings → Pages, chọn nguồn **GitHub Actions** một lần.

CSS, JavaScript, font, `data/meta.json`, `data/level-a1.json` … `data/level-c2.json` và `data/icons.json` dùng đường dẫn tương đối, nên cùng một bản chạy ở gốc máy chủ local, dưới `/flashfree/`, và trên một tên miền riêng sau này. Trang không gắn `<base>` theo tên thư mục. Nếu địa chỉ là một thư mục mà thiếu dấu `/` cuối, trang tự thêm dấu đó trước khi tải file. App chỉ tải file trình độ đang chọn, rồi tải các mức còn lại ở nền. Từ chuyên ngành nằm trong `data/fields/` và chỉ tải khi mở chủ đề đó (hoặc tải nền sau). Ảnh không nằm trong repo: trình duyệt xin bản nhỏ (Commons rộng khoảng 320px, hoặc SVG OpenMoji) khi thẻ hiện ra. Emoji trong `icons.json` là ký tự Unicode do app chọn, dùng khi không có ảnh.

Netlify hoặc Vercel cũng chạy được: publish directory là `.`, không cần build command. Không cần biến môi trường.

## Tạo lại dữ liệu từ vựng

```bash
pip install wordfreq wn
python3 scripts/build_all.py
```

`build_vocab.py` tải các nguồn trong `DATA_SOURCES.md` vào `data/raw/` (thư mục này không được commit), rồi ghi `data/meta.json` và một file cho mỗi mức. `build_images.py` gắn ảnh OpenMoji và Wikimedia Commons vào các file đó. Lần chạy sau dùng bản đã tải nếu file còn đó. Xóa `data/raw/` nếu bạn muốn tải lại từ đầu.

Chi tiết giấy phép và cách trích dẫn nằm ở `DATA_SOURCES.md` và trang **Nguồn** trong app.

Nút tròn góc trên mở hồ sơ: chuỗi, lịch tháng, huy chương, chia sẻ. Đăng nhập Google là tùy chọn và chỉ dùng gói Firebase miễn phí. Khi `js/firebase-config.js` còn để trống, app học như khách và nút ghi **Chưa bật đăng nhập**. Các bước bật nằm ở `docs/FIREBASE_SETUP_VI.md`.

## Cách thêm từ mới

Không cần biết lập trình. Bạn thêm từ bằng một file chữ trên GitHub, rồi bấm một nút để máy tạo lại bộ thẻ.

1. Mở https://github.com/tuanlmogle/flashfree/blob/main/data/extra-words.txt
2. Bấm biểu tượng cây bút (Edit this file).
3. Kéo xuống cuối. Mỗi dòng là một từ. Dòng có dấu `#` ở đầu chỉ là ghi chú, máy bỏ qua.
   - Chỉ từ, máy tự tìm nghĩa: `waffle`
   - Từ và nghĩa: `kindness | lòng tốt`
   - Từ, nghĩa, và câu ví dụ tiếng Anh: `kindness | lòng tốt | She showed kindness.`
   - Nếu không có nghĩa tiếng Việt, viết một câu tiếng Anh ngắn: `serendipity | A pleasant surprise.`
4. Bấm **Commit changes**. Có thể ghi thẳng vào nhánh `main`.
5. Vào tab **Actions**, chọn workflow **Rebuild vocabulary**. Nếu bạn vừa commit file trên, workflow thường tự chạy. Nếu không, bấm **Run workflow**, chọn nhánh `main`, rồi **Run workflow**.
6. Vài phút sau sẽ có một pull request tên **Update vocabulary data**. Mở PR, xem cho chắc, rồi bấm **Merge**. Workflow không tự merge và không sửa thẳng `main` ngoài file bạn đã commit.
7. Sau khi merge, trang web cập nhật theo lần đẩy GitHub Pages.

Từ đã có trong bộ thì dòng mới không đè nghĩa cũ. Id thẻ không đổi, nên tiến độ ôn trên máy học viên vẫn còn.
