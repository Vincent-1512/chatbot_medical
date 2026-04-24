# BÁO CÁO TỔNG QUAN DỰ ÁN 
## AI TRIAGE MEDICAL - HỆ THỐNG PHÂN LUỒNG Y TẾ THÔNG MINH

# 1. Tóm tắt dự án
AI Triage Medical là hệ thống chẩn đoán và phân luồng bệnh nhân (Triage) thông minh, được xây dựng dựa trên sự kết hợp giữa mô hình tìm kiếm vector (Vector Search / RAG) và hệ thống máy học luật gia (Rule-based Expert System). 

Mục tiêu cốt lõi của dự án là số hóa quy trình tiếp nhận bệnh nhân: Dựa trên những câu văn mô tả triệu chứng lộn xộn của người bệnh, AI sẽ trích xuất ra các nhóm triệu chứng chuẩn hóa, đánh giá mức độ khẩn cấp, đưa ra chẩn đoán căn bệnh có xác suất cao nhất và điều hướng bệnh nhân đến phòng khám chuyên khoa tương ứng.

# 2. Ngăn xếp công nghệ (Technology Stack)
- **Giao diện người dùng (Frontend):** Python Streamlit (Xây dựng form Chatbot có tính tương tác cao).
- **Hệ cơ sở dữ liệu:** PostgreSQL kết hợp Extention `pgvector` ảo hóa Vector DB. Triển khai thông qua Docker Compose.
- **AI & NLP:** Thư viện `SentenceTransformers` (sử dụng Model Embeddings `BAAI/bge-m3` dung lượng nhẹ, chạy thuần Offline trên RAM).
- **Thuật toán chính:** Thuật toán Lai (Hybrid) gồm Cosine Similarity (Vector Search) và Khai phá luật trọng số (Rule-Based Aggregation).

# 3. Kiến trúc hệ thống
Hệ thống được thiết kế theo một Architecture chia làm 4 Giai đoạn (Phase) xử lý tuần tự và độc lập lẫn nhau nhằm nâng cao tính mở rộng (Scalability) và dễ dàng bảo trì.

## Phase 1: Nguyên lý Vector (RAG & NLP) 
- **Mục tiêu:** Dịch ngôn ngữ tự nhiên của con người thành các mã bệnh chuẩn xác (ID) trong hệ thống CSDL.
- **Quy trình:**
  Tách các câu văn mô tả của bệnh nhân thành các vế (Clause-Splitting) -> Vector hóa từng vế bằng `BAAI/bge-m3` -> Thực thi truy lệnh SQL Vector `(1 - (embedding <=> user_vector))` xuống PostgreSQL -> Áp dụng Bộ lọc nhiễu (Lấy ngưỡng Threshold > 55%) -> Rút trích danh sách ID các triệu chứng khớp nhất.

## Phase 2: Bộ lọc Sinh tồn (Rào chắn an toàn sinh mệnh)
- **Mục tiêu:** Phát hiện nhanh các triệu chứng cực kỳ hiểm nghèo để báo động cấp cứu.
- **Quy trình:** 
  Hệ thống sử dụng các ID Triệu chứng lấy từ Phase 1 quét vào bảng `Symptoms`. Sử dụng cờ (Flag) `is_red_flag = true`. Nếu phát hiện ra bất kỳ tín hiệu sinh tồn nào suy giảm (Ví dụ: Đau thắt ngực, khó thở, hôn mê), hệ thống lập tức ngắt toàn bộ chẩn đoán vòng sau và ra Cảnh báo Báo Động Đỏ đẩy trực tiếp bệnh nhân vào Lối Cấp Cứu.

## Phase 3: Thuật toán Suy diễn (Chẩn đoán Bệnh)
- **Mục tiêu:** Áp dụng nguyên lý Toán học & Thống kê vào chẩn đoán.
- **Quy trình:** 
  Khi bệnh nhân vượt qua được Rào chắn Phase 2 (Kiểm tra an toàn), ID của triệu chứng sẽ được Mapping (Nối bảng) sang `Knowledge_Rules`. Thuật toán sẽ tính tổng các Trọng số (`SUM(kr.weight)`) theo từng căn bệnh khác nhau. Bệnh nào có tổng trọng điểm khớp nhất với các triệu chứng lâm sàng hiện tại sẽ được Xếp hạng Nhất. Phương pháp Suy diễn thuần túy bằng Weight / Rule-based này mang lại sự đáng tin cậy cao và tính năng Giải thích AI (Explainable AI) được đề cao - điều tối quan trọng trong ngành Y.

## Phase 4: Tổng hợp và Điều hướng (UX & Output)
- **Mục tiêu:** Giao tiếp mạch lạc và chuyển đổi mã y tế thành lời khuyên dễ hiểu.
- **Quy trình:** 
  Dựa trên Căn bệnh đã suy diễn ở giai đoạn 3, hệ thống sẽ ánh xạ (JOIN) ra nhóm Chuyên khoa thích hợp (Specialty) và truy xuất dữ liệu mô tả (Description) để đưa ra Lời khuyên chăm sóc tại nhà. Mọi thứ được Streamlit render thông qua UI hai cột hiển thị tường minh luồng suy nghĩ logic của AI cho người dùng cảm thấy tin tưởng.

# 4. Định hướng và Ý nghĩa thực tiễn
Dự án được tạo ra hướng đến khả năng chạy offline 100%, bảo đảm không xảy ra nguy cơ lộ lọt dữ liệu y tế cá nhân ra Internet thông qua các API mở, đồng thời triệt tiêu hoàn toàn chi phí biến đổi cho các token mô hình. Hệ thống rất phù hợp để triển khai làm Kiosk hoặc Chatbot độc lập tại quầy lễ tân của các Bệnh viện và trung tâm Y khoa vừa/lớn. 
