# Chính Sách Quyền Riêng Tư (Privacy Policy)
*Cập nhật lần cuối: 28/09/2026*

Ứng dụng **Edu Social Crawler** là công cụ kỹ thuật phục vụ đề tài Nghiên cứu Khoa học (NCKH) cấp trường/viện: *"Nhận diện cảm xúc đa nhãn của người học trên mạng xã hội dựa trên ngữ cảnh hội thoại và đặc trưng ngôn ngữ mạng xã hội"*. Chúng tôi cam kết bảo vệ quyền riêng tư và xử lý dữ liệu người dùng một cách minh bạch, an toàn và tuân thủ các quy định đạo đức nghiên cứu cũng như chính sách của nền tảng (Meta Platform Terms, Threads API Terms).

---

## 1. Dữ liệu chúng tôi thu thập (Data We Collect)

Ứng dụng chỉ thu thập các dữ liệu công khai trên mạng xã hội (Threads, Facebook Pages) liên quan đến chủ đề giáo dục và đời sống học tập:
* Nội dung văn bản của bài đăng công khai (public posts) và các câu trả lời công khai (public replies).
* Thời gian đăng bài (timestamp) và số lượng tương tác tổng quát (nếu có).
* Đường dẫn ảnh công khai đính kèm bài đăng (chỉ phục vụ phân tích đa phương thức theo ngữ cảnh).

> **Lưu ý:** Chúng tôi **KHÔNG** thu thập tin nhắn riêng tư (DM), danh sách bạn bè, thông tin tài khoản cá nhân nhạy cảm, mật khẩu hoặc bất kỳ dữ liệu riêng tư nào.

---

## 2. Mục đích sử dụng dữ liệu (Purpose of Data Use)

Mọi dữ liệu thu thập được **chỉ phục vụ duy nhất cho mục đích nghiên cứu học thuật phi thương mại**:
* Xây dựng bộ ngữ liệu tiếng Việt phục vụ huấn luyện và đánh giá các mô hình học máy / xử lý ngôn ngữ tự nhiên (NLP) nhận diện cảm xúc người học.
* Dữ liệu tuyệt đối **không được sử dụng cho bất kỳ mục đích thương mại, quảng cáo hay bán lại cho bên thứ ba**.

---

## 3. Biện pháp ẩn danh hóa và bảo mật dữ liệu (Anonymization & Security)

Để bảo đảm tính riêng tư tuyệt đối cho người dùng trên mạng xã hội, toàn bộ dữ liệu thô sau khi thu thập đều được tự động xử lý qua pipeline ẩn danh:
1. **Băm một chiều danh tính (One-way Hashing):** Tên tài khoản (username) và ID người dùng được băm bằng thuật toán mật mã `HMAC-SHA256` kết hợp cùng khóa salt bí mật (`ANONYMIZATION_SALT`). Không ai có thể giải mã ngược lại để tìm danh tính thật của tác giả.
2. **Che thông tin cá nhân (Redaction):** Toàn bộ địa chỉ email, số điện thoại, liên kết URL cá nhân và các lượt nhắc đến tài khoản khác (`@mention`) xuất hiện trong văn bản đều được thay thế bằng các token ẩn danh (`[EMAIL]`, `[PHONE]`, `[URL]`, `[MENTION]`).
3. **Lưu trữ an toàn:** Dữ liệu sau khi làm sạch được lưu trữ an toàn trong cơ sở dữ liệu nội bộ và Google Spreadsheet được phân quyền giới hạn chỉ nhóm tác giả đề tài có quyền truy cập.

---

## 4. Hướng dẫn yêu cầu xóa dữ liệu (User Data Deletion Instructions)

Người dùng có toàn quyền yêu cầu xóa nội dung công khai của mình khỏi tập dữ liệu nghiên cứu bất kỳ lúc nào:
* **Cách thức yêu cầu:** Gửi email đến đại diện nhóm nghiên cứu theo địa chỉ bên dưới, đính kèm liên kết (URL) của bài đăng/bình luận mà bạn muốn gỡ bỏ.
* **Thời gian xử lý:** Trong vòng 48 giờ kể từ khi nhận được yêu cầu hợp lệ, nhóm nghiên cứu sẽ rà soát và xóa vĩnh viễn bản ghi chứa nội dung đó khỏi toàn bộ cơ sở dữ liệu và bảng tính nghiên cứu.
* **Email tiếp nhận:** `research.contact.edunlp@gmail.com` *(hoặc email liên hệ của nhóm nghiên cứu)*.

---

## 5. Thay đổi chính sách

Chính sách này có thể được cập nhật để phù hợp với tiến độ nghiên cứu hoặc các thay đổi về chính sách từ phía Meta/Threads. Mọi cập nhật sẽ được công bố công khai trên kho lưu trữ mã nguồn này.

---

# Privacy Policy (English Version)

*Last updated: September 28, 2026*

The **Edu Social Crawler** application is a research tool developed for an academic research project: *"Multi-label emotion recognition of learners on social networks based on conversational context and linguistic features"*. We are committed to protecting user privacy and processing data ethically, transparently, and in compliance with Meta Platform Terms and Threads API Terms.

### 1. Data Collection
We only collect publicly available data related to education and learning environments:
- Text content of public posts and public replies.
- Public timestamps and aggregated interaction indicators.
- Publicly accessible image URLs attached to posts.
We **DO NOT** access private messages, personal profile credentials, friend lists, or non-public information.

### 2. Purpose of Use
All collected data is strictly used for **non-commercial academic research** to train and evaluate Natural Language Processing (NLP) models for educational emotion recognition. Data will never be sold, rented, or used for advertising.

### 3. Anonymization & Data Protection
- **One-way Pseudonymization:** User identifiers and usernames are cryptographically hashed using `HMAC-SHA256` with a private secret salt. Personal identities cannot be reverse-engineered.
- **PII Redaction:** Personal Information (emails, phone numbers, external URLs, and `@mentions`) within the text are automatically detected and replaced with placeholder tokens.
- **Secure Storage:** Data is stored within restricted local databases and password-protected research repositories accessible only to authorized researchers.

### 4. Data Deletion Instructions
Users have the right to request the deletion of their public posts/replies from our research dataset:
- **How to request:** Send an email to `research.contact.edunlp@gmail.com` with the permalink/URL of the post or comment you wish to remove.
- **Processing Time:** Within 48 hours of verification, all associated records will be permanently purged from our datasets.

### 5. Contact Information
For any inquiries regarding data protection and research ethics, please contact the research team at: `research.contact.edunlp@gmail.com`.
