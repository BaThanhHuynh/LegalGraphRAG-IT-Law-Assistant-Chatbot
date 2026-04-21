# IT Law Chatbot - Tư vấn Luật Công nghệ thông tin

IT Law Chatbot là một trợ lý ảo hỗ trợ tư vấn pháp luật chuyên sâu về lĩnh vực Công nghệ thông tin (Việt Nam). Dự án sử dụng kiến trúc **GraphRAG** (Retrieval-Augmented Generation kết hợp Knowledge Graph) để tăng cường độ chính xác cho câu trả lời.

Dự án dùng mô hình LLM từ Google (Gemini) để sinh đáp án phân tích, dựa trên kho văn bản luật trong cơ sở dữ liệu mạng kết nối (MySQL), kết hợp cùng Vector Embeddings (`all-MiniLM-L6-v2` thông qua `sentence-transformers`).


## Yêu cầu hệ thống

- **Python 3.10** hoặc mới hơn.
- **XAMPP** (hoặc MySQL Server tương đương).
- Git (tuỳ chọn để clone dự án).

---

## Hướng dẫn cài đặt và chạy chi tiết

### Bước 1: Khởi động cơ sở dữ liệu MySQL

1. Mở **XAMPP Control Panel**.
2. Nhấn **Start** ở module **MySQL** (chắc chắn cổng đang chạy là `3306`).
   - *Lưu ý:* Bạn chưa cần làm gì thêm bên trong phpMyAdmin vì script của dự án sẽ tự tạo Database có tên `it_law_chatbot`.

### Bước 2: Thiết lập môi trường Python

Mở Terminal / PowerShell tại thư mục thư mục gốc của dự án (`IT-Law-Chatbot`) và chạy các lệnh dưới đây:

```bash
# 1. Tạo môi trường ảo (nếu chưa có)
python -m venv .venv

# 2. Kích hoạt môi trường (trên Windows)
.\.venv\Scripts\activate

# 3. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

### Bước 3: Cấu hình biến môi trường `.env`

1. Tại thư mục gốc `IT-Law-Chatbot`, tìm file có tên `.env.example`.
2. Tạo một bản sao chép của file đó và đổi tên thành `.env` (hoặc đổi tên trực tiếp file cũ).
3. Mở file `.env` lên và cấu hình `GEMINI_API_KEY`:

```env
# Google Gemini API Key (Bắt buộc phải có)
GEMINI_API_KEY=điền_api_key_cua_ban_vao_day

# Cấu hình XAMPP MySQL (Mặc định XAMPP Windows là User root, Password rỗng)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=it_law_chatbot

# Server
FLASK_PORT=5000
FLASK_DEBUG=true
```

> **Làm thế nào để có GEMINI_API_KEY?** Truy cập [Google AI Studio](https://aistudio.google.com/app/apikey) để tạo khóa miễn phí.

### Bước 4: Khởi tạo Database và nạp dữ liệu (Seeding)

Dự án đi kèm một script tự động:
- Đọc file `database/schema.sql` để tạo Database và các Bảng.
- Lấy thông tin đã cào được từ file `law_chunks.jsonl`.
- Tạo **Embeddings** cho từng đoạn văn bản.
- Kết nối và xây dựng các đỉnh / cạnh của **Knowledge Graph** (Đồ thị tri thức).

Tại Terminal đang chạy môi trường ảo, bạn gõ lệnh:
```bash
python database/seed_data.py
```

> **Lưu ý:** Quá trình nạp và phân tích sinh ra số lượng lớn Embeddings (hơn 9.000 records) nên sẽ tiêu tốn từ vài phút đến vài chục phút tùy hiệu năng máy của bạn (CPU/GPU). Vui lòng kiên nhẫn.

### Bước 5: Chạy máy chủ Chatbot

Sau khi thấy thông báo việc Seed Data hoàn tất ( *Seed data completed!*), tiến hành khởi động server Flask:

```bash
python app.py
```

Khi server hoạt động thành công, Terminal sẽ hiển thị: `Server running at http://localhost:5000`.

### Bước 6: Trải nghiệm giao diện

Mở trình duyệt bất kỳ (Google Chrome, Edge, v.v...) và truy cập đường dẫn: 
**[http://localhost:5000](http://localhost:5000)**

Chỉ cần gõ câu hỏi vào vùng trò chuyện (Ví dụ: *"Các hành vi bị nghiêm cấm trong luật CNTT là gì?"*), Chatbot sẽ truy xuất tài liệu và trả về câu trả lời có trích xuất chi tiết theo Đồ thị tri thức/Vector!
