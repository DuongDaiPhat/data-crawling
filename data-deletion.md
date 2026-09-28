# Hướng Dẫn Yêu Cầu Xóa Dữ Liệu Người Dùng (User Data Deletion Instructions)
*Cập nhật lần cuối: 28/09/2026*

Ứng dụng **Edu Social Crawler** là công cụ kỹ thuật phục vụ nghiên cứu khoa học học thuật (NCKH). Theo Chính sách nền tảng của Meta (Meta Platform Policy) và các tiêu chuẩn bảo vệ quyền riêng tư, người dùng có toàn quyền yêu cầu xóa bỏ mọi dữ liệu liên quan đến nội dung công khai của mình khỏi hệ thống nghiên cứu của chúng tôi.

Dưới đây là các phương thức và quy trình từng bước để yêu cầu xóa dữ liệu:

---

## Cách 1: Gửi yêu cầu xóa dữ liệu trực tiếp đến Nhóm Nghiên cứu (Khuyên dùng)

Nếu bạn muốn xóa các bài đăng hoặc bình luận công khai của mình khỏi tập dữ liệu nghiên cứu và bảng tính Google Sheet của chúng tôi:

### Bước 1: Soạn email yêu cầu
Gửi email đến hòm thư tiếp nhận của nhóm nghiên cứu với thông tin:
* **Địa chỉ nhận:** `research.contact.edunlp@gmail.com`
* **Tiêu đề email:** `[Yêu cầu xóa dữ liệu] - Edu Social Crawler`
* **Nội dung email bao gồm:**
  1. Tên người dùng (username/handle) trên Threads hoặc Facebook.
  2. Đường dẫn (URL/Permalink) đến bài viết hoặc bình luận mà bạn muốn gỡ bỏ khỏi tập dữ liệu.

### Bước 2: Tiếp nhận và xác minh
* Nhóm nghiên cứu sẽ phản hồi xác nhận tiếp nhận email trong vòng **24 giờ**.
* Nhóm sẽ tiến hành tra cứu bản ghi trong cơ sở dữ liệu nội bộ (`SQLite`) và trên bảng tính lưu trữ (`Google Sheets`).

### Bước 3: Thực hiện xóa vĩnh viễn
* Trong vòng **48 giờ** kể từ khi xác nhận, toàn bộ bản ghi văn bản, ID và siêu dữ liệu liên quan đến bài viết/bình luận của bạn sẽ bị **xóa hoàn toàn và vĩnh viễn** khỏi:
  - Bảng tính Google Sheets (`raw_data`).
  - Cơ sở dữ liệu SQLite cục bộ (`data/state.sqlite3`).
  - Các bản sao lưu tệp thô (`data/runs/*.jsonl`).
* Sau khi xóa xong, nhóm nghiên cứu sẽ gửi một email xác nhận hoàn tất kèm mã xác thực yêu cầu xóa dữ liệu.

---

## Cách 2: Hủy quyền truy cập ứng dụng trên Meta / Threads

Nếu bạn đã từng đăng nhập hoặc cấp quyền cho ứng dụng **Edu Social Crawler** qua tài khoản Meta/Threads của mình, bạn có thể tự thu hồi quyền bất kỳ lúc nào:

1. **Trên Facebook:**
   * Mở Facebook > vào **Cài đặt & quyền riêng tư (Settings & Privacy)** > **Cài đặt (Settings)**.
   * Chọn **Ứng dụng và trang web (Apps and Websites)**.
   * Tìm ứng dụng **Edu Social Crawler** và bấm nút **Gỡ (Remove)**.
2. **Trên Threads:**
   * Mở ứng dụng Threads > vào **Trang cá nhân** > bấm icon Menu cài đặt.
   * Chọn **Tài khoản (Account)** > **Quyền trang web (Website permissions)**.
   * Chọn tab **Đang hoạt động (Active)** > Tìm ứng dụng và chọn **Xóa/Thu hồi quyền (Revoke access)**.

---

# User Data Deletion Instructions (English Version)

*Last updated: September 28, 2026*

**Edu Social Crawler** is an academic research application. In compliance with the Meta Platform Terms and global data protection standards, users have the absolute right to request the deletion of their data and publicly crawled content from our research database.

### Method 1: Submit a Deletion Request via Email (Recommended)

If you wish to purge your public posts or replies from our research dataset and storage sheets:

1. **Send an Email Request:**
   - **To:** `research.contact.edunlp@gmail.com`
   - **Subject:** `[Data Deletion Request] - Edu Social Crawler`
   - **Body:** Include your Threads/Facebook username and the specific URLs/permalinks of the posts or comments to be deleted.
2. **Verification & Processing:**
   - The research team will acknowledge your request within **24 hours**.
   - Associated records will be permanently and irreversibly purged from our Google Sheets, SQLite state databases, and backup JSONL files within **48 hours**.
3. **Confirmation:**
   - A confirmation email with a completion reference code will be dispatched to you once all records have been erased.

### Method 2: Revoke App Permissions via Meta Accounts

If you have granted testing or login permissions to **Edu Social Crawler**, you can revoke them directly:
- **Facebook:** Go to **Settings & Privacy > Settings > Apps and Websites** > Locate **Edu Social Crawler** > Click **Remove**.
- **Threads:** Open Threads > Go to **Settings > Account > Website permissions** > Under the **Active** tab, select **Edu Social Crawler** and choose **Revoke Access**.

---

### Liên hệ / Contact Information
Mọi thắc mắc liên quan đến quyền riêng tư và quy trình xử lý dữ liệu, vui lòng liên hệ đại diện nhóm nghiên cứu:
* **Email:** `research.contact.edunlp@gmail.com`
* **Dự án:** Nhận diện cảm xúc đa nhãn của người học trên mạng xã hội (NCKH 2026-2027).
