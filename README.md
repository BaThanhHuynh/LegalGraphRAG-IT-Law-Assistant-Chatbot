# ⚖️ IT Law Chatbot - Trợ lý pháp lý thông minh

## 1. 📖 Tên và mô tả
**IT Law Chatbot** là một hệ thống trợ lý ảo chuyên tư vấn pháp lý về lĩnh vực Công nghệ thông tin tại Việt Nam. Bằng cách ứng dụng kiến trúc tiên tiến **GraphRAG** (kết hợp Đồ thị tri thức - Knowledge Graph và Tìm kiếm Vector), chatbot có khả năng cung cấp các câu trả lời chính xác, bám sát văn bản pháp luật, đồng thời luôn đi kèm trích dẫn rõ ràng, minh bạch.

## 2. ✨ Tính năng chính
- 🔍 **Tra cứu thông minh**: Hiểu ngôn ngữ tự nhiên và truy xuất cực nhanh các điều khoản luật liên quan.
- 🧠 **Suy luận chuyên sâu (GraphRAG)**: Phân tích được các mối liên hệ phức tạp giữa văn bản luật, chương, điều khoản, hành vi và chủ thể.
- 💬 **Trả lời tự nhiên, logic**: Tích hợp mô hình AI mạnh mẽ (Gemini 2.5 Flash) giúp phản hồi trôi chảy, dễ hiểu.
- 📑 **Trích dẫn nguồn uy tín**: Không tự bịa thông tin, luôn cung cấp căn cứ pháp lý để người dùng đối chiếu.

## 3. 📸 Ảnh demo
*(Hãy cập nhật hình ảnh thực tế của ứng dụng)*

![Giao diện IT Law Chatbot](https://via.placeholder.com/800x450.png?text=IT+Law+Chatbot+Demo)

## 4. ⚙️ Hướng dẫn cài đặt

**Yêu cầu hệ thống:**
- Python 3.9 trở lên
- Neo4j Database

**Các bước cài đặt:**

1. **Clone mã nguồn:**
   ```bash
   git clone https://github.com/BaThanhHuynh/IT-Law-Chatbot.git
   cd IT-Law-Chatbot
   ```

2. **Thiết lập môi trường ảo và cài đặt thư viện:**
   ```bash
   python -m venv venv
   # Kích hoạt trên Windows:
   venv\Scripts\activate
   # Kích hoạt trên Linux/Mac:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Cấu hình môi trường:**
   Tạo file `.env` ở thư mục gốc và cung cấp các thông tin cần thiết:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   API_PORT=8000
   ```

## 5. 🚀 Cách sử dụng

1. **Khởi chạy máy chủ FastAPI:**
   ```bash
   python -m app.main
   ```
   *(Hoặc chạy qua uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`)*

2. **Truy cập ứng dụng:**
   Mở trình duyệt web và đi tới địa chỉ: `http://localhost:8000`

3. **Trải nghiệm:**
   Gõ các câu hỏi pháp lý vào khung chat (ví dụ: *"Hành vi nào bị nghiêm cấm trên không gian mạng?"*) và nhận kết quả tư vấn!

## 6. 🛠 Công nghệ dùng

| Thành phần | Công nghệ / Thư viện |
|------------|-----------------------|
| **Backend API** | FastAPI, Uvicorn ⚡ |
| **Mô hình Ngôn ngữ (LLM)** | Google Gemini API (Gemini 2.5) 🤖 |
| **Framework AI** | LangChain, Sentence-transformers |
| **Cơ sở dữ liệu Đồ thị** | Neo4j 🕸️ |
| **Cơ sở dữ liệu Vector** | FAISS / Qdrant 🗄️ |

## 7. 👨‍💻 Thông tin tác giả
- **Tác giả**: BaThanhHuynh (Huỳnh Bá Thành)
- **GitHub**: [@BaThanhHuynh](https://github.com/BaThanhHuynh)
- **Link dự án**: [IT-Law-Chatbot](https://github.com/BaThanhHuynh/IT-Law-Chatbot)
