# LUỒNG XỬ LÝ CỐT LÕI CỦA AI CHATBOT (A-Z)

Dưới đây là lời giải thích chi tiết toàn bộ luồng hoạt động của "Não bộ" AI (từ A-Z) và cách các file, bảng DB, trọng số móc xích với nhau để đưa ra kết luận. Hệ thống hoạt động qua **3 Giai đoạn (Phases)** cốt lõi:

## GIAI ĐOẠN 1: Bóc tách ngôn ngữ (NLP Extractor - Vector Search)
**Mục tiêu:** Biến đoạn chat thô của bệnh nhân thành các ID triệu chứng chuẩn y khoa.

1. **Nhập liệu:** Bệnh nhân gõ: *"Tôi bị đau đầu kèm theo sốt cao và buồn nôn"*. (Dữ liệu vào API `POST /api/patient/chat` tại `server.py`).
2. **Tiền xử lý (`symptom_extractor.py`):**
   - Hàm `_split_clauses()` chặt câu ra làm nhiều vế dựa vào dấu phẩy, chữ "và", "kèm theo" 
   *(Thành 3 vế: "tôi bị đau đầu", "sốt cao", "buồn nôn").*
3. **Chạy Mô hình Vector (`triage_engine.py`):**
   - Hệ thống dùng Embedding Model (như `BAAI/bge-m3`) để biến từng vế thành một vector (mảng 1024 con số thực).
4. **Đối chiếu Database (Bảng `Symptoms` & `Knowledge_Chunks`):**
   - Dùng toán tử Cosine Similarity (thuật toán đo khoảng cách vector của thư viện **pgvector**) tìm trong database xem từ vựng nào giống nhất.
   - Nếu độ tương đồng (Similarity) cao hơn một ngưỡng nhất định (VD: > 55%), nó sẽ Map (chốt) về ID chuẩn.
   - *Kết quả:* Chữ "sốt cao" -> `symptom_id = 5`; "buồn nôn" -> `symptom_id = 12`.
5. **Lưu trữ:** Lưu danh sách các ID này vào bảng **`SESSION_SYMPTOMS`** (Kèm theo độ tin cậy `confidence` là bao nhiêu %).

## GIAI ĐOẠN 2: Động cơ suy diễn (Inference Engine) & Tính Trọng Số
**Mục tiêu:** Chấm điểm xem bệnh nhân đang mắc bệnh gì dựa vào bộ quy tắc của Chuyên gia.
**File xử lý:** `triage_engine.py` (Hàm `diagnose()`)

Hệ thống sẽ mang danh sách Triệu chứng mà bệnh nhân đang có để quét qua bảng **`KNOWLEDGE_RULES`**. Bảng này chứa "Luật" do Chuyên gia cấu hình. 
**Ví dụ Bệnh Sốt xuất huyết (Disease A) được chuyên gia cấu hình 3 luật:**
- Triệu chứng: Sốt cao | Trọng số (`weight`) = 1.0 | `is_mandatory` = TRUE (Bắt buộc phải có)
- Triệu chứng: Phát ban | Trọng số (`weight`) = 0.5 
- Triệu chứng: Ho có đờm | `is_exclusion` = TRUE (Triệu chứng loại trừ)

**Thuật toán đối chiếu (Logic Scoring):**
Máy sẽ duyệt qua toàn bộ danh sách bệnh lý trong DB và xét 3 lớp bảo vệ:
1. **Lớp 1 (Check Loại Trừ):** Nếu trong danh sách bệnh nhân khai có "Ho đờm", thì dù trùng khớp 99% các triệu chứng khác, điểm của Bệnh Sốt xuất huyết lập tức về `0` (bị loại bỏ).
2. **Lớp 2 (Check Bắt buộc):** Bệnh nhân khai "Phát ban" nhưng KHÔNG khai "Sốt cao" (mà Sốt cao là Mandatory). Điểm của bệnh này sẽ bị phạt (Penalty) rớt xuống cực thấp.
3. **Lớp 3 (Toán học tính Điểm - `hybrid_score`):**
   - Công thức: `Điểm = [Tổng weight của các triệu chứng BN đang có] / [Tổng max weight của bệnh đó]`
   - Ví dụ: Bệnh nhân có Sốt cao (1.0), không có Phát ban (0.5).
   - => `hybrid_score = 1.0 / (1.0 + 0.5) = 0.66 (66%)`.

Kết thúc hàm, AI sẽ chọn ra Top 3 bệnh có điểm cao nhất (Rank 1, 2, 3) và ném vào bảng **`SESSION_DISEASE_SCORES`**.

## GIAI ĐOẠN 3: Đưa ra Lời khuyên (Output Generation)
**Mục tiêu:** Giao tiếp lại với người dùng.
**File xử lý:** `chatbot_logic.py` (Hoặc logic chat ở `triage_engine.py`)

Sau khi có điểm rank, hệ thống sẽ đưa ra quyết định:
- **Trường hợp 1 (Thiếu thông tin):** Top 1 bệnh có điểm 66%, AI thấy vẫn còn 1 triệu chứng "Phát ban" chưa rõ. AI sẽ chọc vào bảng `Symptoms`, lấy cột `question_text` của chữ "Phát ban" (Ví dụ: *"Bạn có bị nổi nốt mẩn đỏ trên da không?"*) và phản hồi ra màn hình để BN trả lời (Có/Không).
- **Trường hợp 2 (Đã đủ thông tin - Đạt ngưỡng Threshold):**
  1. Lấy `disease_id` Top 1.
  2. Map ngược qua bảng **`DISEASES`**, `JOIN` vào bảng **`SPECIALTIES`** để lấy thông tin `Tên Chuyên Khoa`.
  3. Cập nhật `suggested_specialty_id` vào bảng **`CHAT_SESSIONS`**.
  4. Lắp ráp các câu chữ thành "Phiếu kết quả sàng lọc" lưu vào bảng **`SESSION_RECOMMENDATIONS`**.

- Cuối cùng, API trả JSON chứa Phiếu kết quả này về Frontend (Giao diện Streamlit), hiển thị lời khuyên: *"Bạn nên đi khám Nội Tổng hợp vì nghi ngờ Sốt xuất huyết..."*

Đó là một vòng lặp kín từ lúc Bệnh nhân gõ phím cho đến khi dữ liệu nằm an toàn trong cơ sở dữ liệu để Bác sĩ có thể đọc được!
