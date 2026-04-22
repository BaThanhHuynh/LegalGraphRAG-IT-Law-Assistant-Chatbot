# IT Law Chatbot – GraphRAG IT Law Advisory

## Giới thiệu

IT Law Chatbot là một hệ thống trợ lý pháp lý được xây dựng nhằm hỗ trợ tra cứu và tư vấn **Luật Công nghệ Thông tin tại Việt Nam**. Hệ thống được thiết kế với mục tiêu cung cấp câu trả lời có căn cứ rõ ràng, bám sát điều luật và hạn chế tối đa việc suy đoán ngoài dữ liệu.

Điểm cốt lõi của dự án là việc áp dụng kiến trúc **GraphRAG** – kết hợp giữa truy xuất ngữ nghĩa (Vector Search) và đồ thị tri thức (Knowledge Graph). Cách tiếp cận này giúp hệ thống không chỉ “tìm đúng đoạn luật”, mà còn “hiểu mối quan hệ giữa các điều luật”, từ đó cải thiện đáng kể độ chính xác và tính nhất quán của câu trả lời.

---

## Kiến trúc tổng thể

Hệ thống gồm ba thành phần chính, phối hợp với nhau trong quá trình xử lý truy vấn:

### Knowledge Graph (Neo4j)

Đây là lớp biểu diễn tri thức có cấu trúc, mô hình hóa luật dưới dạng đồ thị.

**Các thực thể chính:**
- `VAN_BAN`: Văn bản pháp luật (Luật, Nghị định, Thông tư)
- `CHUONG`: Các chương trong văn bản
- `DIEU_LUAT`: Đơn vị tra cứu chính
- `KHAI_NIEM`: Định nghĩa pháp lý
- `HANH_VI`: Hành vi bị điều chỉnh hoặc cấm
- `CHU_THE`: Đối tượng áp dụng

**Các quan hệ:**
- `THUOC`: Quan hệ phân cấp (Điều → Chương → Văn bản)
- `THAM_CHIEU`: Dẫn chiếu giữa các điều luật
- `NGHIEM_CAM`: Hành vi bị cấm
- `DINH_NGHIA`: Liên kết định nghĩa
- `AP_DUNG`: Đối tượng áp dụng

Vai trò của Knowledge Graph là giúp hệ thống:
- Truy vết logic pháp lý
- Mở rộng ngữ cảnh truy vấn
- Hỗ trợ suy luận đa bước giữa các điều luật

---

### Vector Retrieval (MySQL + Embedding)

Thành phần này đảm nhiệm việc tìm kiếm ngữ nghĩa.

- Dữ liệu văn bản luật được chia nhỏ theo **Điều/Khoản**
- Sử dụng embedding model: `all-MiniLM-L6-v2`
- Lưu trữ trong MySQL (XAMPP)

Vai trò:
- Tìm các đoạn văn bản có nội dung liên quan
- Cung cấp context ban đầu cho mô hình ngôn ngữ
- Xử lý các truy vấn không khớp chính xác từ khóa

---

### Mô hình ngôn ngữ (LLM)

Hệ thống sử dụng **Gemini 2.5 Flash** để tổng hợp thông tin và sinh câu trả lời.

**Đầu vào:**
- Context từ Vector Search
- Thông tin quan hệ từ Knowledge Graph

**Đầu ra:**
- Câu trả lời có cấu trúc
- Trích dẫn điều luật cụ thể
- Lập luận dựa trên dữ liệu truy xuất

---

## Cách hệ thống hoạt động (GraphRAG)

Quy trình xử lý một câu hỏi diễn ra theo các bước:

1. **Phân tích truy vấn**
   - Xác định hành vi, chủ thể, loại văn bản liên quan

2. **Truy xuất vector**
   - Tìm các đoạn luật có độ tương đồng cao

3. **Truy vấn đồ thị**
   - Mở rộng thông tin qua các quan hệ như:
     - Điều luật liên quan
     - Hành vi bị cấm
     - Văn bản nguồn

4. **Hợp nhất ngữ cảnh**
   - Loại bỏ trùng lặp
   - Giữ lại thông tin có giá trị cao

5. **Sinh câu trả lời**
   - Dựa hoàn toàn vào dữ liệu truy xuất
   - Kèm theo trích dẫn pháp lý

---

## Pipeline dữ liệu

Hệ thống có pipeline xử lý dữ liệu gồm hai phần chính:

### 1. Xử lý và lưu trữ văn bản

- Thu thập văn bản luật
- Làm sạch và chuẩn hóa dữ liệu
- Chia đoạn theo cấu trúc (Điều/Khoản)
- Sinh embedding
- Lưu vào MySQL

### 2. Xây dựng Knowledge Graph

- Trích xuất thực thể (NER)
- Trích xuất quan hệ (Relation Extraction)
- Chuyển dữ liệu sang Neo4j
- Tạo nodes và relationships theo schema pháp lý

---

## Thiết kế lưu trữ

### MySQL
Dùng để lưu:
- Nội dung văn bản luật
- Embedding vector
- Metadata (điều, khoản, văn bản…)

### Neo4j
Dùng để lưu:
- Quan hệ giữa các thành phần pháp luật
- Cấu trúc phân cấp và dẫn chiếu

---

## Điểm nổi bật

- Kết hợp **Vector Search và Knowledge Graph**
- Tôn trọng cấu trúc pháp lý (Điều/Khoản)
- Câu trả lời có **trích dẫn rõ ràng**
- Giảm thiểu hallucination
- Dễ mở rộng thêm dữ liệu và luật mới

---

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|----------|----------|
| Backend | Python (Flask) |
| LLM | Gemini 2.5 Flash |
| Embedding | sentence-transformers |
| Database | MySQL (XAMPP) |
| Graph DB | Neo4j |
| Pipeline | Python scripts |

---

## Phạm vi

Hệ thống hiện tập trung vào:
- Luật Công nghệ thông tin
- Luật An ninh mạng
- Các nghị định, thông tư liên quan

---

## Hạn chế

- Phụ thuộc vào dữ liệu đầu vào
- Cần cập nhật khi có thay đổi pháp luật
- Độ chính xác phụ thuộc vào mức độ đầy đủ của Knowledge Graph

---

## Định hướng phát triển

- Mở rộng sang các lĩnh vực luật khác
- Tích hợp mô hình ngôn ngữ chuyên ngành pháp lý
- Tối ưu truy vấn đồ thị (multi-hop reasoning)
- Xây dựng hệ thống đánh giá tự động

---
