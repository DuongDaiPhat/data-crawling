# Edu Social Crawler CLI

CLI thu thập dữ liệu công khai phục vụ đề tài trong `Aim.md`: nhận diện cảm xúc đa nhãn của người học dựa trên ngữ cảnh hội thoại và đặc trưng ngôn ngữ mạng xã hội.

Ứng dụng hỗ trợ:

- Facebook Pages công khai qua Meta Graph API.
- Threads công khai theo từ khóa qua Threads API.
- Reddit công khai qua OAuth/Data API, chỉ khi đã có quyền phù hợp cho mục đích nghiên cứu.
- Giữ cấu trúc `bài đăng → bình luận cha → bình luận đích` khi API cung cấp được.
- Ghi các đường dẫn ảnh của bài đăng vào cột `image_urls` dưới dạng JSON array.
- Chuẩn hóa Unicode, khoảng trắng và xuống dòng; giữ nguyên emoji, dấu câu, teencode và chữ hoa/thường.
- Thay URL, email, số điện thoại và @mention bằng token; định danh tác giả/ID nội dung bằng HMAC một chiều.
- Lọc nội dung tiếng Việt/liên quan giáo dục, chống trùng bằng SQLite.
- Nhận cả chủ đề đời sống trong môi trường học tập: tình yêu, crush, drama, phốt, xin lỗi, mâu thuẫn, bắt nạt, áp lực…
- Lưu JSONL dự phòng và tự động append vào Google Sheet đích.

Google Sheet mặc định: [Data crawling](https://docs.google.com/spreadsheets/d/1pWQcZkVq_hS0UzITtr5bA9mEb3SPJSYdXBXRpHbzF-k/edit?usp=sharing). Ứng dụng tạo hoặc dùng tab `raw_data`, không sửa các tab khác.

## 1. Yêu cầu và cài đặt

- Python 3.11 trở lên.
- Tài khoản/API app hợp lệ của nền tảng muốn dùng.
- Google Cloud service account có quyền sửa spreadsheet.

Trên PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
edu-crawl init
Copy-Item .env.example .env
```

Sau lệnh `init`, chỉnh `config.yaml`. File `.env` và service-account JSON đã được `.gitignore`, không commit khóa bí mật.

Kiểm tra CLI:

```powershell
edu-crawl --help
edu-crawl validate -c config.yaml
```

## 2. Kết nối Google Sheet

1. Tạo project tại Google Cloud Console.
2. Bật **Google Sheets API** và **Google Drive API**.
3. Tạo một service account, tải khóa JSON.
4. Mở file JSON, sao chép giá trị `client_email`.
5. Mở [Google Sheet đích](https://docs.google.com/spreadsheets/d/1pWQcZkVq_hS0UzITtr5bA9mEb3SPJSYdXBXRpHbzF-k/edit?usp=sharing), bấm **Share**, cấp quyền **Editor** cho `client_email`.
6. Trong `.env`, đặt đường dẫn tuyệt đối:

```dotenv
GOOGLE_SERVICE_ACCOUNT_FILE=D:\secrets\edu-crawler-service-account.json
```

7. Tạo salt ẩn danh ổn định, ít nhất 16 ký tự; nên là chuỗi ngẫu nhiên dài 32 ký tự trở lên:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Đưa kết quả vào `.env`:

```dotenv
ANONYMIZATION_SALT=chuoi-vua-tao
```

Giữ nguyên salt giữa các lần chạy để cùng một tác giả luôn có cùng `author_hash`. Mất hoặc đổi salt sẽ khiến không thể đối chiếu tác giả ẩn danh giữa các đợt.

Kiểm tra quyền Google Sheet:

```powershell
edu-crawl doctor -c config.yaml
```

Nếu thành công, lệnh sẽ tạo tab `raw_data` và hàng header nếu chúng chưa tồn tại. Với tab theo schema cũ, CLI tự thêm cột `image_urls` ở cuối, không dịch chuyển các cột đang có.

## 3. Chọn nguồn dữ liệu

Chỉ thêm nguồn công khai, liên quan trực tiếp đến môi trường học tập và phù hợp với phê duyệt đạo đức nghiên cứu của nhóm. Nên ưu tiên:

- fanpage chính thức của trường/khoa/câu lạc bộ học thuật;
- fanpage confession công khai có chính sách cho phép nghiên cứu;
- tài khoản/chủ đề Threads về học tập, thi cử, học phí, đồ án, thực tập;
- subreddit công khai về học tập/sinh viên khi đã có quyền sử dụng nội dung.

Không thu thập tin nhắn riêng, nhóm kín, hồ sơ cá nhân, danh sách thành viên hoặc nội dung cần vượt qua đăng nhập/anti-bot.

### Facebook Pages

Meta không còn cung cấp Facebook Groups API cho use case thu thập group tổng quát. CLI vì vậy chỉ hỗ trợ Page ID/username qua API chính thức. Để đọc Page của bên thứ ba, Meta có thể yêu cầu App Review và **Page Public Content Access**; Page do bạn quản lý thường cần `pages_read_engagement` và `pages_read_user_content` theo quyền của app/token.

Trong `.env`:

```dotenv
META_ACCESS_TOKEN=EAAB...
```

Trong `config.yaml`:

```yaml
facebook:
  enabled: true
  terms_acknowledged: true
  graph_version: v26.0
  access_token_env: META_ACCESS_TOKEN
  pages:
    - id: PAGE_ID_HOAC_USERNAME
      name: Confession trường ABC
      trusted_education_source: true
  posts_per_page: 25
  comments_per_post: 100
  replies_per_comment: 50
```

`trusted_education_source: true` chỉ nên dùng khi toàn bộ nguồn thuộc môi trường học tập. Khi đó các chủ đề đời sống như tình yêu, drama hay bài phốt vẫn được giữ. Nếu là trang tổng hợp, để `false`; nội dung phải có tín hiệu học thuật, hoặc đồng thời có tín hiệu bối cảnh trường học và chủ đề trong `learning_environment_topics`.

Chạy thử riêng Facebook:

```powershell
edu-crawl crawl -c config.yaml -p facebook --dry-run
```

### Threads

Tạo Meta app/Threads use case, xin token và quyền tìm nội dung công khai (ví dụ quyền keyword search hiện hành trong Meta App Review). Quyền và tên permission có thể thay đổi theo phiên bản API; luôn kiểm tra tài liệu Meta trước khi chạy.

Trong `.env`:

```dotenv
THREADS_ACCESS_TOKEN=THQVJ...
```

Trong `config.yaml`:

```yaml
threads:
  enabled: true
  terms_acknowledged: true
  api_version: v1.0
  access_token_env: THREADS_ACCESS_TOKEN
  queries:
    - text: sinh viên
      search_type: RECENT
      search_mode: KEYWORD
      trusted_education_source: true
    - text: học phí
      search_type: RECENT
      search_mode: KEYWORD
      trusted_education_source: true
  posts_per_query: 50
  fetch_replies: false
```

`fetch_replies: true` chỉ hoạt động khi token có quyền đọc replies cho bài tương ứng. Nếu app chỉ có keyword search, giữ `false`; bài Threads sẽ được lưu với `object_type=post`.

Chạy thử:

```powershell
edu-crawl crawl -c config.yaml -p threads --dry-run
```

### Reddit

Reddit yêu cầu OAuth, User-Agent rõ ràng và tuân thủ Data API Terms. Điều khoản hiện hành hạn chế dùng User Content để huấn luyện AI/ML nếu chưa có sự cho phép phù hợp. Chỉ đặt `terms_acknowledged: true` sau khi nhóm nghiên cứu xác nhận quyền sử dụng dữ liệu cho đúng mục đích.

Trong `.env`:

```dotenv
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=edu-social-crawler/0.1 by u/ten_tai_khoan_cua_ban
```

Trong `config.yaml`:

```yaml
reddit:
  enabled: true
  terms_acknowledged: true
  subreddits:
    - name: TenSubredditDuocPhep
      trusted_education_source: true
      queries: ["sinh viên", "học tập", "thi"]
  posts_per_query: 25
  comments_per_post: 100
  sort: new
  time_filter: month
  include_nsfw: false
```

Chạy thử:

```powershell
edu-crawl crawl -c config.yaml -p reddit --dry-run
```

## 4. Chạy crawl thật

Luôn chạy `--dry-run` trước. Chế độ này chỉ tạo file JSONL trong `data/runs/`, không ghi SQLite và không đẩy Google Sheet:

```powershell
edu-crawl crawl -c config.yaml -p facebook -p threads --dry-run
```

Mở file JSONL mới nhất và kiểm tra một mẫu nhỏ: nguồn, ngôn ngữ, ngữ cảnh, emoji và token ẩn danh. Khi đạt yêu cầu, chạy thật:

```powershell
edu-crawl crawl -c config.yaml -p facebook -p threads
```

Crawl tất cả provider đang bật:

```powershell
edu-crawl crawl -c config.yaml
```

Luồng chạy thật:

1. Dữ liệu hợp lệ được ghi vào SQLite với trạng thái `pending`.
2. Bản JSONL của đợt crawl được lưu trong `data/runs/`.
3. CLI append theo batch vào tab `raw_data`.
4. Chỉ sau khi Google Sheet xác nhận thành công, bản ghi mới chuyển sang `synced`.

Nếu mạng/Google API lỗi, dữ liệu vẫn ở `pending`. Không cần crawl lại; chạy:

```powershell
edu-crawl sync -c config.yaml
```

Muốn crawl trước, đồng bộ sau:

```powershell
edu-crawl crawl -c config.yaml --no-sync
edu-crawl doctor -c config.yaml
edu-crawl sync -c config.yaml
```

## 5. Schema tab `raw_data`

| Cột | Ý nghĩa |
|---|---|
| `collected_at` | Thời điểm hệ thống thu thập (UTC) |
| `platform` | `facebook`, `threads`, `reddit` |
| `source_name` | Tên Page, từ khóa Threads hoặc subreddit |
| `source_type` | Loại nguồn công khai |
| `object_type` | `post`, `comment`, `reply` |
| `source_item_id` | Mã HMAC của ID nội dung, dùng chống trùng |
| `post_id` | Mã HMAC của ID bài đăng gốc |
| `parent_comment_id` | Mã HMAC của ID bình luận cha trực tiếp nếu có |
| `post_text` | Nội dung bài đăng gốc đã làm sạch |
| `parent_comment_text` | Bình luận cha trực tiếp đã làm sạch |
| `target_text` | Nội dung cần gán nhãn |
| `permalink` | Mặc định để trống để giảm khả năng tái định danh |
| `published_at` | Thời điểm đăng do nền tảng trả về |
| `language` | Nhãn ngôn ngữ heuristic |
| `education_relevance` | Điểm liên quan giáo dục 0–1 |
| `author_hash` | Mã tác giả ẩn danh bằng HMAC-SHA256 |
| `content_hash` | Hash nội dung/ngữ cảnh phục vụ kiểm tra |
| `collection_run_id` | ID đợt crawl |
| `image_urls` | JSON array chứa tối đa `max_image_urls` đường dẫn ảnh của bài đăng |

Không có username, tên hiển thị hay author ID gốc trong đầu ra.

## 6. Quy tắc làm sạch

- Chuẩn Unicode NFC; không xóa emoji.
- Gộp khoảng trắng thừa, chuẩn hóa xuống dòng.
- Không lowercase, không bỏ dấu, không sửa teencode/slang vì đây là đặc trưng nghiên cứu.
- URL → `[URL]`, email → `[EMAIL]`, số điện thoại → `[PHONE]`, mention → `[USER]`.
- Mặc định HMAC hóa ID bài/bình luận và không lưu permalink. Chỉ bật `store_permalinks: true` nếu quy trình kiểm chứng đã được phê duyệt và Sheet provenance được tách quyền khỏi người gán nhãn.
- Bỏ nội dung quá ngắn/quá dài, `[deleted]`, `[removed]`.
- Lọc tiếng Việt bằng heuristic nhẹ để vẫn giữ câu trộn Việt–Anh. Có thể giảm `min_vietnamese_score` nếu dữ liệu bị lọc quá mạnh.
- Nguồn không được đánh dấu `trusted_education_source` phải khớp tín hiệu học thuật, hoặc đồng thời khớp bối cảnh trường học và một chủ đề đời sống được cấu hình.
- Bộ lọc có hai nhánh: nội dung học thuật trực tiếp; hoặc chủ đề đời sống (`learning_environment_topics`) đi kèm bối cảnh trường/lớp/sinh viên (`education_context_keywords`). Điều này giữ được confession, tình yêu, drama, phốt, xin lỗi… nhưng hạn chế lấy drama giải trí không liên quan trường học.
- Chỉ URL ảnh dùng `http`/`https` được giữ; URL trùng bị loại. CLI chỉ lưu đường dẫn, không tải ảnh về máy hay Google Drive.

## 7. Lưu ý nghiên cứu và vận hành

- Xin phê duyệt đạo đức nghiên cứu/IRB tương ứng trước khi thu thập quy mô lớn.
- Ghi lại ngày crawl, phiên bản API, danh sách nguồn và căn cứ quyền sử dụng.
- Tôn trọng yêu cầu xóa nội dung; nếu cần quy trình truy vết/xóa, nên giữ bảng ánh xạ provenance riêng, mã hóa và giới hạn quyền, không đưa vào Sheet dùng để gán nhãn.
- Hạn chế người được truy cập Sheet và JSONL; không công bố salt ẩn danh.
- Không dùng `author_hash` để suy luận danh tính hoặc lập hồ sơ cá nhân.
- Kiểm tra lại điều khoản nền tảng trước mỗi đợt crawl; quyền API và giới hạn sử dụng có thể thay đổi.
- Không tăng tốc bằng nhiều app/token để né rate limit.

Tài liệu chính thức tham khảo:

- [Google Sheets API: append values](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/append)
- [Meta Threads API collection](https://www.postman.com/meta/threads/overview)
- [Reddit Data API Terms](https://redditinc.com/policies/data-api-terms)
- [Reddit Developer Terms](https://redditinc.com/policies/developer-terms)

## 8. Kiểm thử cho người phát triển

```powershell
pytest
ruff check .
```

Mã nguồn chính nằm trong `src/edu_social_crawler/`; mỗi nền tảng là một provider độc lập nên có thể bổ sung nguồn mới mà không thay đổi pipeline làm sạch và Google Sheets.
