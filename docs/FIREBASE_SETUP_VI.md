# Bật đăng nhập Google cho FlashFree

File `js/firebase-config.js` trong repo đã có cấu hình Web của dự án `flashfree-9971e` (không gồm Analytics). Phần còn lại làm trên máy tính: bật nhà cung cấp Google, thêm tên miền, và dán luật Firestore. Nếu script Firebase không tải được, app vẫn học như khách.

Chỉ dùng gói **Spark** (miễn phí) của Firebase. Không bật dịch vụ trả phí. Không dùng đăng nhập Apple.

## 1. Tạo dự án

1. Mở https://console.firebase.google.com/ và đăng nhập bằng tài khoản Google.
2. Bấm **Thêm dự án** (Add project). Đặt tên, ví dụ `flashfree`.
3. Tắt Google Analytics nếu được hỏi (không cần). Bấm tạo dự án và đợi xong.

## 2. Thêm ứng dụng Web và chép cấu hình

1. Trong dự án, bấm biểu tượng **Web** (`</>`).
2. Đặt biệt danh, ví dụ `FlashFree`. Không cần chọn Hosting.
3. Bấm đăng ký ứng dụng. Firebase hiện một đoạn `firebaseConfig`.
4. Mở file `js/firebase-config.js` trong repo. Điền đúng 6 ô: `apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`. Giữ nguyên dấu ngoặc kép.
5. Lưu file, rồi đưa lên GitHub như các lần sửa khác (commit trên nhánh của bạn, không đẩy thẳng nếu bạn đang dùng pull request).

Đây là cấu hình công khai của ứng dụng Web, không phải mật khẩu máy chủ. Quyền đọc dữ liệu do file luật ở bước 6 quyết định.

## 3. Bật đăng nhập Google

1. Menu **Build** → **Authentication** → **Bắt đầu** (Get started).
2. Thẻ **Sign-in method** → **Google** → bật → chọn email hỗ trợ → **Lưu**.
3. Thẻ **Settings** → **Authorized domains**. Thêm `tuanlmogle.github.io` nếu chưa có. `localhost` thường đã có sẵn, để thử trên máy.

## 4. Tạo Firestore

1. Menu **Build** → **Firestore Database** → **Tạo cơ sở dữ liệu**.
2. Chọn **Production mode** (chế độ sản xuất), không chọn test mode.
3. Chọn vùng gần bạn, ví dụ `asia-southeast1`, rồi bấm bật. Spark cho phép một cơ sở dữ liệu miễn phí.

## 5. Dán luật bảo mật

1. Trong Firestore, mở thẻ **Rules**.
2. Xóa hết chữ sẵn có. Mở file `firestore.rules` trong repo, chép toàn bộ, dán vào ô luật.
3. Bấm **Xuất bản** (Publish).

Luật này nghĩa là: mỗi người chỉ đọc và ghi được `users/{chính họ}`. Khi người mới đăng nhập bằng liên kết `?ref=...`, họ chỉ được **tạo một lần** giấy mời ở `users/{người mời}/referrals/{người mới}`. Người mời đọc được danh sách đó. Không ai đọc được dữ liệu học của người khác.

## 6. Thử

1. Đợi trang https://tuanlmogle.github.io/flashfree/ cập nhật sau khi file cấu hình đã nằm trên nhánh `main`.
2. Mở trang, bấm hình tròn góc trên, rồi **Đăng nhập bằng Google**.
3. Học vài thẻ, tắt mạng, học thêm, bật mạng lại. Firestore của gói Spark xếp hàng khi mất mạng và đẩy lên khi có mạng, trong hạn mức miễn phí.

Nếu ô trong `js/firebase-config.js` để trống, app không gọi Firebase và không báo lỗi. Nút vẫn là **Chưa bật đăng nhập**.

Gói Spark có hạn mức đọc/ghi mỗi ngày. FlashFree chỉ ghi sau khi bạn học (gom khoảng một giây), và chia tiến độ thẻ thành nhiều mảnh nhỏ để không vượt 1 MB mỗi tài liệu. Không cần nâng lên gói trả phí cho việc học cá nhân.

## 7. Bật AI Logic (Gemini, miễn phí)

App nhờ Gemini viết nghĩa và ví dụ cho từ chưa có trong bộ. Chỉ người đã đăng nhập mới gọi được, và mỗi máy được khoảng 30 từ mỗi ngày. Không thêm khóa API mới vào repo: app dùng cấu hình web sẵn có.

1. Mở https://console.firebase.google.com/ và chọn dự án **flashfree-9971e**.
2. Menu bên trái: **Build** → **AI Logic** (có bản giao diện ghi **Firebase AI Logic** hoặc **Gemini**).
3. Bấm **Get started** / **Bắt đầu**.
4. Khi được chọn nền, chọn **Gemini Developer API**. Đừng chọn **Vertex AI Gemini API** (cách đó gắn với Google Cloud và có thể yêu cầu thanh toán). Gemini Developer API là lựa chọn chạy được trên gói **Spark**.
5. Làm theo ô xác nhận để bật API. Nếu trang hỏi đồng ý điều khoản của Gemini Developer API, bấm đồng ý. Không cần tạo khóa mới và dán vào code.
6. Nếu Firestore đã xuất bản luật cũ, mở **Firestore → Rules**, dán lại toàn bộ `firestore.rules` trong repo (đã có `match /ai/{wordId}`), rồi **Publish**.
7. Mở trang web, đăng nhập bằng Google, thêm một từ chưa có trong bộ và bấm **Nhờ AI viết**.

Nếu chưa bấm bước 4, app báo: «Chưa bật AI Logic trên Firebase, hoặc dịch vụ chưa trả lời.» Học các thẻ sẵn vẫn bình thường.
