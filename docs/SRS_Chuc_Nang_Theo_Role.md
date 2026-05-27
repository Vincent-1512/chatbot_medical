# 📋 ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)
## HỆ THỐNG CHATBOT SÀNG LỌC TRIỆU CHỨNG Y TẾ — AI TRIAGE MEDICAL

---

| Thông tin | Nội dung |
|:---|:---|
| **Tên dự án** | AI Triage Medical — Hệ thống Phân luồng Y tế Thông minh |
| **Phiên bản tài liệu** | 1.0 |
| **Ngày tạo** | 23/05/2026 |
| **Công nghệ** | Python (Flask + Streamlit), PostgreSQL + pgvector, SentenceTransformers (BAAI/bge-m3) |
| **Kiến trúc** | Monolithic — Offline 100% — Docker Compose |

---

## MỤC LỤC

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Phân loại vai trò (Roles)](#2-phân-loại-vai-trò-roles)
3. [Role 1: Bệnh nhân (Patient)](#3-role-1-bệnh-nhân-patient)
4. [Role 2: Bác sĩ Lâm sàng (Doctor)](#4-role-2-bác-sĩ-lâm-sàng-doctor)
5. [Role 3: Chuyên viên Tri thức Y khoa (Knowledge Admin)](#5-role-3-chuyên-viên-tri-thức-y-khoa-knowledge-admin)
6. [Role 4: Quản trị viên Hệ thống (System Admin / IT)](#6-role-4-quản-trị-viên-hệ-thống-system-admin--it)
7. [Ma trận phân quyền tổng hợp](#7-ma-trận-phân-quyền-tổng-hợp)
8. [Yêu cầu phi chức năng](#8-yêu-cầu-phi-chức-năng)

---

## 1. TỔNG QUAN HỆ THỐNG

### 1.1. Mục đích
Hệ thống AI Triage Medical là chatbot sàng lọc triệu chứng y tế thông minh, tích hợp vào website phòng khám để:
- **Thu thập** triệu chứng từ ngôn ngữ tự nhiên của bệnh nhân bằng NLP (Vector Search + RAG).
- **Suy diễn** bệnh lý tiềm năng bằng Rule-based Expert System (Hệ chuyên gia luật trọng số).
- **Phân luồng** bệnh nhân đến chuyên khoa phù hợp, đánh giá mức độ khẩn cấp.
- **Hỗ trợ** bác sĩ tiếp nhận bệnh nhân nhanh chóng thông qua phiếu tóm tắt sàng lọc.

### 1.2. Phạm vi
| Phạm vi trong (In-scope) | Phạm vi ngoài (Out-of-scope) |
|:---|:---|
| Chatbot sàng lọc triệu chứng NLP | Tích hợp hệ thống HIS bệnh viện |
| Hệ chuyên gia suy diễn luật trọng số | Thanh toán, đặt lịch hẹn khám |
| Quản trị cây tri thức y khoa | Thiết kế UI/UX chi tiết |
| Feedback loop bác sĩ xác minh AI | Kiểm thử bảo mật chuyên sâu |
| Quản trị tài khoản nhân sự | Triển khai production server |

### 1.3. Kiến trúc xử lý 4 Phase

```
Phase 1: Vector Search (NLP)     → Bóc tách triệu chứng từ văn bản tự nhiên
Phase 2: Red Flag Filter         → Quét cờ đỏ, cảnh báo khẩn cấp
Phase 3: Inference Engine        → Suy diễn bệnh lý bằng luật trọng số
Phase 4: Output & Routing        → Gợi ý chuyên khoa + lời khuyên
```

---

## 2. PHÂN LOẠI VAI TRÒ (ROLES)

Hệ thống phân chia thành **4 vai trò** (Role) với phạm vi trách nhiệm tách biệt:

| # | Vai trò | Mã Role trong DB | Mô tả ngắn |
|:---:|:---|:---:|:---|
| 1 | **Bệnh nhân** (Patient) | `patient` | Người dùng cuối, tương tác chatbot để khai báo triệu chứng |
| 2 | **Bác sĩ Lâm sàng** (Doctor) | `doctor` | Nhân viên y tế, xem hàng đợi sàng lọc và xác minh kết quả AI |
| 3 | **Chuyên viên Tri thức** (Knowledge Admin) | `knowledge_admin` | Chuyên gia y khoa, quản trị cây tri thức và luật suy diễn |
| 4 | **Quản trị viên IT** (System Admin) | `admin` | Kỹ thuật viên, quản lý nhân sự, hệ thống, cấu hình AI |

> **Lưu ý:** Bệnh nhân được lưu trong bảng `Patients`, còn 3 role còn lại được lưu trong bảng `Staff_Accounts` với trường `role` phân biệt.

---

## 3. ROLE 1: BỆNH NHÂN (PATIENT)

### 3.1. Tổng quan
Bệnh nhân là đối tượng sử dụng dịch vụ chính. Họ tương tác trực tiếp với Chatbot AI bằng ngôn ngữ tự nhiên để khai báo triệu chứng và nhận gợi ý chuyên khoa khám.

### 3.2. Bảng yêu cầu chức năng chi tiết

#### 🔐 MODULE: XÁC THỰC & ĐĂNG NHẬP

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **BN-AUTH-01** | **Đăng ký tài khoản mới** | Bệnh nhân nhập: Họ tên, Số điện thoại, Mật khẩu, Giới tính. Hệ thống kiểm tra trùng SĐT. Nếu hợp lệ → tạo tài khoản + tạo hồ sơ y tế trống (Medical_Profiles). Mật khẩu được mã hóa Bcrypt. | `Patients`, `Medical_Profiles` |
| **BN-AUTH-02** | **Đăng nhập bằng SĐT/Mật khẩu** | Bệnh nhân nhập SĐT + Mật khẩu. Hệ thống truy vấn bảng `Patients`, giải mã Bcrypt để xác thực. Nếu đúng → thiết lập Session với `user_type = 'patient'`, `patient_id`, `user_name`. | `Patients` |
| **BN-AUTH-03** | **Đăng nhập qua SSO (Giả lập)** | Trên giao diện Streamlit, bệnh nhân chọn tài khoản có sẵn từ dropdown hoặc đăng ký mới trực tiếp. Hệ thống gọi `get_or_create_patient()` để đồng bộ. | `Patients`, `Medical_Profiles` |
| **BN-AUTH-04** | **Đăng xuất** | Bệnh nhân nhấn "Đăng xuất". Hệ thống xóa toàn bộ session data (Flask `session.clear()`). | — |
| **BN-AUTH-05** | **Kiểm tra trạng thái đăng nhập** | API `/api/auth/me` trả về thông tin user hiện tại: `logged_in`, `user_type`, `user_name`, `patient_id`. Frontend dùng để render giao diện phù hợp. | — |

#### 💬 MODULE: CHATBOT SÀNG LỌC TRIỆU CHỨNG

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **BN-CHAT-01** | **Khởi tạo phiên tư vấn mới** | Bệnh nhân nhấn "Bắt đầu tư vấn". Hệ thống: (1) Tạo record `Chat_Sessions` với `status = 'in_progress'`. (2) Khởi tạo `ChatbotSession` in-memory. (3) Gửi tin nhắn chào mừng tự động. (4) Hỗ trợ **Guest Mode** cho khách chưa đăng nhập (tạo patient tạm). | `Chat_Sessions`, `Message_Logs` |
| **BN-CHAT-02** | **Gửi tin nhắn mô tả triệu chứng** | Bệnh nhân gõ văn bản tự do (VD: "tôi bị đau đầu, buồn nôn và chóng mặt"). Hệ thống: (1) Log tin nhắn vào `Message_Logs`. (2) Gọi `SymptomExtractor.extract()` để bóc tách triệu chứng bằng Vector Search. (3) Lưu triệu chứng nhận diện được vào `Session_Symptoms`. (4) Trả về danh sách triệu chứng đã ghi nhận. | `Message_Logs`, `Session_Symptoms`, `Symptoms` |
| **BN-CHAT-03** | **Trả lời câu hỏi xác nhận AI** | Chatbot hỏi câu hỏi đóng (VD: "Bạn có bị sốt không?"). Bệnh nhân nhấn **[Có]**, **[Không]**, hoặc **[Không rõ]**. Hệ thống: (1) Phân loại câu trả lời qua `detect_response_type()`. (2) Cập nhật `Session_Symptoms` với `is_present = true/false`. (3) Kích hoạt Inference Engine tính lại điểm. | `Session_Symptoms`, `Knowledge_Rules` |
| **BN-CHAT-04** | **Nhận kết quả sàng lọc** | Khi đủ thông tin (hoặc đạt tối đa 6 câu hỏi follow-up), hệ thống: (1) Chạy `diagnose()` để tính tổng điểm trọng số. (2) Hiển thị: Chuyên khoa gợi ý, Bệnh lý nghi ngờ (top 3), Mức độ ưu tiên, Lời khuyên chăm sóc. (3) Lưu kết quả vào `Session_Disease_Scores` và `Session_Recommendations`. (4) Cập nhật `Chat_Sessions` → `status = 'completed'`. | `Session_Disease_Scores`, `Session_Recommendations`, `Chat_Sessions` |
| **BN-CHAT-05** | **Cảnh báo khẩn cấp (Red Flag)** | Nếu phát hiện triệu chứng cờ đỏ (`is_red_flag = true`), hệ thống ngay lập tức: (1) Ngắt toàn bộ luồng suy diễn. (2) Hiển thị cảnh báo đỏ "🚨 CẢNH BÁO KHẨN CẤP". (3) Khuyến nghị bệnh nhân đến cơ sở y tế gần nhất. (4) Đánh dấu `triage_urgency = 'emergency'`. | `Symptoms`, `Chat_Sessions` |
| **BN-CHAT-06** | **Hủy phiên tư vấn** | Bệnh nhân nhấn "Hủy phiên" hoặc đóng chatbot. Hệ thống cập nhật `status = 'abandoned'`, ghi `end_time = NOW()`. Xóa state in-memory. | `Chat_Sessions` |

#### 📋 MODULE: HỒ SƠ SỨC KHỎE

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **BN-PROF-01** | **Xem hồ sơ y tế cá nhân** | Bệnh nhân truy cập tab "Hồ sơ Sức khỏe". Hệ thống JOIN bảng `Patients` + `Medical_Profiles` hiển thị: Họ tên, SĐT, Giới tính, Ngày sinh, Chiều cao, Cân nặng, Nhóm máu, Dị ứng, Bệnh nền. | `Patients`, `Medical_Profiles` |
| **BN-PROF-02** | **Cập nhật hồ sơ y tế** | Bệnh nhân chỉnh sửa: Chiều cao, Cân nặng, Nhóm máu, Tiền sử dị ứng, Bệnh lý nền. Nhấn "Lưu". Hệ thống thực hiện UPSERT vào `Medical_Profiles` (ON CONFLICT DO UPDATE). | `Medical_Profiles` |

#### 📜 MODULE: LỊCH SỬ TƯ VẤN

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **BN-HIST-01** | **Xem danh sách phiên tư vấn** | Bệnh nhân truy cập tab "Lịch sử Sàng lọc". Hiển thị danh sách các phiên chat đã thực hiện: Thời gian, Chuyên khoa gợi ý, Mức độ khẩn cấp, Trạng thái. Sắp xếp theo `start_time DESC`. | `Chat_Sessions`, `Specialties`, `Session_Recommendations` |
| **BN-HIST-02** | **Xem chi tiết phiên chat cũ** | Bệnh nhân click vào 1 phiên. Hiển thị toàn bộ lịch sử bong bóng chat và phiếu kết quả. **Chế độ Read-only** — không cho phép gửi tin nhắn mới. | `Message_Logs`, `Session_Recommendations` |

### 3.3. Luồng xử lý chính (Chatbot Flow)

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Bệnh nhân   │────▶│  Nhập triệu chứng│────▶│  NLP Extraction │
│  (Greeting)  │     │  (Free text)     │     │  (Vector Search)│
└──────────────┘     └──────────────────┘     └────────┬────────┘
                                                        │
                               ┌────────────────────────▼────────────────────────┐
                               │        Tìm thấy triệu chứng?                   │
                               │     CÓ                          KHÔNG           │
                               └──────┬──────────────────────────┬───────────────┘
                                      │                          │
                               ┌──────▼──────┐           ┌──────▼──────────────┐
                               │ Kiểm tra    │           │ Yêu cầu mô tả lại  │
                               │ Red Flag    │           │ chi tiết hơn        │
                               └──────┬──────┘           └─────────────────────┘
                                      │
                        ┌─────────────▼─────────────┐
                        │    Có Red Flag?            │
                        │   CÓ              KHÔNG   │
                        └──┬─────────────────┬──────┘
                           │                 │
                    ┌──────▼──────┐   ┌──────▼──────────┐
                    │ 🚨 CẢNH BÁO │   │ Inference Engine│
                    │ KHẨN CẤP   │   │ (Rule-based)    │
                    │ → KẾT THÚC │   └──────┬──────────┘
                    └─────────────┘          │
                                      ┌─────▼───────────┐
                                      │ Cần hỏi thêm?   │
                                      │ (≤ 6 câu hỏi)   │
                                      └──┬──────────┬────┘
                                    CÓ   │          │ KHÔNG
                                  ┌──────▼────┐ ┌───▼──────────┐
                                  │ Hỏi xác   │ │ 📋 KẾT QUẢ  │
                                  │ nhận thêm │ │ SÀNG LỌC     │
                                  │ Có/Không  │ │ → KẾT THÚC   │
                                  └───────────┘ └──────────────┘
```

---

## 4. ROLE 2: BÁC SĨ LÂM SÀNG (DOCTOR)

### 4.1. Tổng quan
Bác sĩ truy cập cổng thông tin nội bộ (Portal) để xem danh sách bệnh nhân đã được AI phân luồng về khoa mình, xem chi tiết báo cáo sàng lọc, và phản hồi đánh giá chất lượng AI (Feedback Loop).

### 4.2. Bảng yêu cầu chức năng chi tiết

#### 🔐 MODULE: XÁC THỰC

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **BS-AUTH-01** | **Đăng nhập Portal Bác sĩ** | Bác sĩ nhập Username/Email + Mật khẩu tại trang đăng nhập nội bộ. Hệ thống: (1) Truy vấn `Staff_Accounts` với điều kiện `is_active = true`. (2) So khớp Bcrypt. (3) Kiểm tra `role = 'doctor'`. (4) Thiết lập session: `user_type`, `staff_id`, `user_name`, `specialty_id`. | `Staff_Accounts`, `Specialties` |
| **BS-AUTH-02** | **Đăng xuất** | Bác sĩ nhấn "Đăng xuất". Hệ thống xóa session state, trở về màn hình đăng nhập. | — |

#### 📋 MODULE: HÀNG ĐỢI SÀNG LỌC (TRIAGE QUEUE)

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **BS-QUEUE-01** | **Xem hàng đợi bệnh nhân** | Hiển thị danh sách bệnh nhân đã được AI điều hướng về khoa của bác sĩ đang đăng nhập. **Bộ lọc tự động:** `suggested_specialty_id = [specialty_id của bác sĩ]` AND `status = 'completed'`. **Sắp xếp:** Ca `emergency` lên đầu, sau đó theo `end_time DESC`. Hiển thị: Tên BN, Giới tính, Ngày sinh, Mức độ khẩn cấp, Thời gian sàng lọc. | `Chat_Sessions`, `Patients`, `Specialties` |
| **BS-QUEUE-02** | **Đánh dấu ca cấp cứu** | Các ca có `triage_urgency = 'emergency'` tự động được **bôi nền đỏ**, kèm icon cảnh báo 🚨, và **ghim lên đầu danh sách**. | `Chat_Sessions` |

#### 🔍 MODULE: CHI TIẾT BÁO CÁO SÀNG LỌC

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **BS-DETAIL-01** | **Xem thông tin bệnh nhân** | Click vào 1 ca bệnh → Màn hình chia 2 cột: **Cột trái** hiển thị: Họ tên, Giới tính, Ngày sinh, SĐT, Dị ứng (bôi đỏ), Bệnh nền, Chiều cao/Cân nặng, Nhóm máu. | `Patients`, `Medical_Profiles` |
| **BS-DETAIL-02** | **Xem kết luận AI** | **Cột phải** hiển thị: Phiếu tóm tắt gợi ý AI (`Session_Recommendations`), Bảng điểm AI (tên bệnh, điểm hybrid, ranking). | `Session_Recommendations`, `Session_Disease_Scores`, `Diseases` |
| **BS-DETAIL-03** | **Xem lịch sử chat nguyên văn** | Hiển thị toàn bộ bong bóng chat (👤 Bệnh nhân / 🤖 AI) theo thứ tự thời gian. **Chế độ Read-only.** | `Message_Logs` |
| **BS-DETAIL-04** | **Xem triệu chứng đã thu thập** | Liệt kê các triệu chứng AI đã bóc tách: Tên triệu chứng, Mã code, Có/Không có mặt, Độ tin cậy, Nguồn thu thập (free text / xác nhận). | `Session_Symptoms`, `Symptoms` |

#### 🔄 MODULE: FEEDBACK LOOP — XÁC MINH AI

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **BS-FB-01** | **Đánh giá kết quả AI** | Bác sĩ đối chiếu kết quả AI với khám thực tế. Chọn: **[AI chẩn đoán Đúng]** hoặc **[AI chẩn đoán Sai]**. Nếu "Sai" → chọn bệnh lý thực tế từ dropdown danh sách `Diseases`. Nhấn "Lưu đánh giá". Hệ thống UPDATE bảng `Session_Disease_Scores`: `is_doctor_verified = true/false`, `actual_disease_id` (nếu AI sai). | `Session_Disease_Scores`, `Diseases` |
| **BS-FB-02** | **Xuất báo cáo sàng lọc** | Bác sĩ nhấn "Xuất báo cáo" để tải file `.txt` chứa: Mã phiên, Thông tin bệnh nhân, Kết quả AI, Đánh giá bác sĩ, Ngày đánh giá. Dùng để kẹp vào hồ sơ bệnh án hoặc gửi qua HIS. | — |

### 4.3. Luồng xử lý chính (Doctor Flow)

```
┌────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│  Đăng nhập     │────▶│  Xem hàng đợi       │────▶│  Click vào 1 ca  │
│  Portal Bác sĩ │     │  (Lọc theo khoa)    │     │  bệnh cụ thể     │
└────────────────┘     └─────────────────────┘     └────────┬─────────┘
                                                            │
                                                   ┌───────▼────────────┐
                                                   │  Xem chi tiết:     │
                                                   │  • Thông tin BN    │
                                                   │  • Kết luận AI     │
                                                   │  • Lịch sử chat   │
                                                   └───────┬────────────┘
                                                            │
                                                   ┌───────▼────────────┐
                                                   │  Feedback Loop:    │
                                                   │  AI Đúng / Sai?   │
                                                   │  → Lưu đánh giá   │
                                                   └───────┬────────────┘
                                                            │
                                                   ┌───────▼────────────┐
                                                   │  Xuất báo cáo      │
                                                   │  (Tùy chọn)       │
                                                   └────────────────────┘
```

---

## 5. ROLE 3: CHUYÊN VIÊN TRI THỨC Y KHOA (KNOWLEDGE ADMIN)

### 5.1. Tổng quan
Chuyên viên Tri thức (Knowledge Admin) là chuyên gia y tế có trách nhiệm quản trị, bảo trì và mở rộng cơ sở tri thức (Knowledge Base) — bao gồm chuyên khoa, triệu chứng, bệnh lý, và các luật suy diễn. Vai trò này đảm bảo AI hoạt động chính xác theo chuẩn y khoa.

### 5.2. Bảng yêu cầu chức năng chi tiết

#### 🔐 MODULE: XÁC THỰC

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **KMA-AUTH-01** | **Đăng nhập Portal Tri thức** | Chuyên viên nhập Username + Mật khẩu. Hệ thống xác thực, kiểm tra `role = 'knowledge_admin'` và `is_active = true`. | `Staff_Accounts` |
| **KMA-AUTH-02** | **Đăng xuất** | Xóa session state, trở về màn hình đăng nhập. | — |

#### 🏥 MODULE: QUẢN LÝ CHUYÊN KHOA & BỆNH LÝ

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **KMA-SPEC-01** | **Xem danh sách Chuyên khoa** | Hiển thị bảng danh mục chuyên khoa: ID, Mã code (unique), Tên khoa, Mô tả. Sắp xếp theo ID tăng dần. | `Specialties` |
| **KMA-DIS-01** | **Xem danh sách Bệnh lý** | Hiển thị bảng: ID, Mã ICD-10, Tên bệnh, Chuyên khoa điều trị, Mô tả. JOIN bảng `Diseases` với `Specialties`. | `Diseases`, `Specialties` |
| **KMA-DIS-02** | **Thêm mới Bệnh lý** | Nhập: Tên bệnh, Mã ICD-10, Chuyên khoa (dropdown), Mô tả/Lời khuyên. Nhấn "Lưu". Hệ thống: (1) Tự động gọi `get_embedding()` để mã hóa mô tả thành vector(1024). (2) INSERT vào bảng `Diseases` kèm embedding. **Validate:** `icd_code` phải unique, `specialty_id` hợp lệ (FK). | `Diseases` |

#### 🤒 MODULE: QUẢN LÝ TRIỆU CHỨNG

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **KMA-SYM-01** | **Xem danh sách Triệu chứng** | Hiển thị 50 triệu chứng gần nhất: ID, Mã code, Tên chuẩn y khoa, Câu hỏi xác nhận AI, Cờ Red Flag. Sắp xếp theo ID giảm dần. | `Symptoms` |
| **KMA-SYM-02** | **Thêm mới Triệu chứng** | Nhập: Mã triệu chứng (uppercase), Tên chuẩn y khoa, Câu hỏi xác nhận AI (VD: "Bạn có bị ho không?"), Checkbox Red Flag, Từ đồng nghĩa (phẩy cách). Hệ thống: (1) Tự động embedding tên triệu chứng → vector(1024). (2) INSERT vào `Symptoms`. (3) Parse và INSERT từ đồng nghĩa vào `Symptom_Synonyms`. **Ràng buộc:** Bọc trong 1 SQL Transaction để đảm bảo tính toàn vẹn. | `Symptoms`, `Symptom_Synonyms` |

#### ⛓️ MODULE: CẤU HÌNH MA TRẬN LUẬT SUY DIỄN

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **KMA-RULE-01** | **Xem luật suy diễn hiện có** | Hiển thị 50 luật gần nhất: ID, Bệnh lý, Triệu chứng, Trọng số (weight), Bắt buộc (is_mandatory), Loại trừ (is_exclusion). | `Knowledge_Rules`, `Diseases`, `Symptoms` |
| **KMA-RULE-02** | **Thêm mới luật suy diễn** | Chọn: Bệnh lý đích (dropdown), Triệu chứng (dropdown). Kéo slider: Trọng số (0.0 → 2.0, bước 0.05). Checkbox: Bắt buộc / Loại trừ. Nhấn "Ghi nhận Luật". INSERT vào `Knowledge_Rules` với `disease_id`, `symptom_id`, `weight`, `is_mandatory`, `is_exclusion`. | `Knowledge_Rules` |

> **Giải thích logic luật:**
> - **weight** (Trọng số): Mức độ liên quan giữa triệu chứng và bệnh. Weight càng cao → triệu chứng càng đặc trưng cho bệnh.
> - **is_mandatory** (Bắt buộc): Nếu triệu chứng bắt buộc vắng mặt → loại bỏ bệnh khỏi kết quả.
> - **is_exclusion** (Loại trừ): Nếu triệu chứng loại trừ có mặt → loại bỏ bệnh khỏi kết quả.

#### 🧪 MODULE: SANDBOX KIỂM THỬ AI

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **KMA-SAND-01** | **Kiểm thử Động cơ suy diễn** | Chuyên viên nhập mô tả bệnh ảo (VD: "đau bụng dữ dội, nôn mửa"). Hệ thống chạy tuần tự 3 bước: **Bước 1 — Vector Match:** Hiển thị triệu chứng nhận diện được + độ tin cậy. **Bước 2 — Red Flag:** Kiểm tra cờ đỏ (An toàn / Cảnh báo). **Bước 3 — Suy diễn:** Hiển thị bảng kết quả (Tên bệnh, Chuyên khoa, Điểm rule). **⚠️ RÀNG BUỘC QUAN TRỌNG:** Tuyệt đối KHÔNG lưu kết quả vào DB, tránh làm bẩn dữ liệu khám thật. | `Symptoms`, `Knowledge_Rules`, `Diseases` (chỉ READ) |

### 5.3. Luồng xử lý chính (Knowledge Admin Flow)

```
┌────────────────┐     ┌──────────────────────────────────────────────┐
│  Đăng nhập     │────▶│  Tab 1: Chuyên khoa & Bệnh lý              │
│  Portal KMA    │     │  → Xem danh sách / Thêm mới bệnh lý        │
└────────────────┘     ├──────────────────────────────────────────────┤
                       │  Tab 2: Triệu chứng                         │
                       │  → Thêm triệu chứng + từ đồng nghĩa        │
                       ├──────────────────────────────────────────────┤
                       │  Tab 3: Ma trận Luật                         │
                       │  → Thêm luật: Bệnh ↔ Triệu chứng + weight  │
                       ├──────────────────────────────────────────────┤
                       │  Tab 4: Sandbox AI                           │
                       │  → Test thử suy diễn (KHÔNG lưu DB)         │
                       └──────────────────────────────────────────────┘
```

---

## 6. ROLE 4: QUẢN TRỊ VIÊN HỆ THỐNG (SYSTEM ADMIN / IT)

### 6.1. Tổng quan
Quản trị viên IT có quyền cao nhất trong hệ thống. Chịu trách nhiệm quản lý tài khoản nhân sự, giám sát hoạt động hệ thống, nạp dữ liệu RAG, debug AI, và cấu hình tham số kỹ thuật.

### 6.2. Bảng yêu cầu chức năng chi tiết

#### 🔐 MODULE: XÁC THỰC

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **SA-AUTH-01** | **Đăng nhập Portal Quản trị** | Admin nhập Username + Mật khẩu. Hệ thống xác thực, kiểm tra `role = 'admin'` và `is_active = true`. Chỉ admin mới truy cập được các Route quản trị. | `Staff_Accounts` |
| **SA-AUTH-02** | **Đăng xuất** | Xóa session state. | — |

#### 👥 MODULE: QUẢN LÝ NHÂN SỰ

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **SA-USER-01** | **Xem danh sách tài khoản** | Hiển thị bảng nhân viên: ID, Username, Email, Họ tên, Role, Khoa (nếu bác sĩ), Trạng thái Active. JOIN bảng `Staff_Accounts` với `Specialties`. | `Staff_Accounts`, `Specialties` |
| **SA-USER-02** | **Tạo mới tài khoản nhân viên** | Admin nhập: Username, Email, Họ tên, Mật khẩu (Bcrypt hash), Role (doctor / knowledge_admin / admin), Khoa (cho bác sĩ). Nhấn "Tạo tài khoản". **Validate:** Username và Email unique. Nếu role = 'doctor' → bắt buộc chọn `specialty_id`. | `Staff_Accounts` |
| **SA-USER-03** | **Khóa / Mở khóa tài khoản** | Admin chọn nhân viên từ dropdown, chọn "Khóa" hoặc "Mở khóa". UPDATE `is_active = true/false` trong `Staff_Accounts`. **Ràng buộc cứng:** Admin KHÔNG THỂ tự khóa chính mình → hiển thị lỗi "Admin không thể tự khóa chính mình!". | `Staff_Accounts` |

#### 🗂️ MODULE: QUẢN LÝ KHO TRI THỨC RAG

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **SA-RAG-01** | **Xem danh sách Knowledge Chunks** | Hiển thị 20 chunks gần nhất: ID, Loại nguồn (`source_type`), Preview 100 ký tự đầu, Triệu chứng liên quan, Ngày tạo. | `Knowledge_Chunks` |
| **SA-RAG-02** | **Nạp tri thức mới (RAG Ingestion)** | Admin nhập: Đoạn kiến thức y khoa (textarea), Loại nguồn (combined_medical / textbook / medical_article), Triệu chứng liên quan (optional). Nhấn "Nạp & Vectorize". Hệ thống: (1) Gọi `get_embedding()` để mã hóa thành vector(1024). (2) INSERT vào `Knowledge_Chunks` kèm embedding. | `Knowledge_Chunks` |

#### 📈 MODULE: BẢNG ĐIỀU KHIỂN THỐNG KÊ (DASHBOARD)

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **SA-DASH-01** | **Xem tổng quan hệ thống** | Hiển thị 3 metric chính: (1) Tổng số phiên chat (`COUNT(*) FROM Chat_Sessions`). (2) Tỷ lệ cảnh báo khẩn cấp (% emergency). (3) Số nhân viên đang hoạt động. | `Chat_Sessions`, `Staff_Accounts` |
| **SA-DASH-02** | **Biểu đồ phân bổ chuyên khoa** | Biểu đồ cột (Bar chart) hiển thị số lượng phiên chat được phân luồng về từng chuyên khoa. Dữ liệu: `GROUP BY suggested_specialty_id JOIN Specialties`. | `Chat_Sessions`, `Specialties` |

#### 💬 MODULE: DEBUG AI

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **SA-DEBUG-01** | **Xem AI Debug Logs** | Hiển thị 50 message gần nhất: ID, Session ID, Loại người gửi, Nội dung (preview 200 ký tự), Metadata (JSONB), Thời gian gửi. Phục vụ IT debug các phiên chat bị phàn nàn sai lệch. | `Message_Logs` |

#### ⚙️ MODULE: CẤU HÌNH THAM SỐ AI

| Mã | Chức năng | Mô tả chi tiết | Bảng CSDL liên quan |
|:---:|:---|:---|:---|
| **SA-CONFIG-01** | **Điều chỉnh ngưỡng Confidence** | Kéo slider điều chỉnh `confidence_threshold` (0.0 → 1.0, bước 0.05). Đây là ngưỡng tin cậy tối thiểu để hệ thống NLP chấp nhận 1 triệu chứng đã bóc tách. Giá trị mặc định: 0.55. | `System_Configs` |
| **SA-CONFIG-02** | **Tùy chỉnh tin nhắn chào** | Thay đổi nội dung tin nhắn chào mừng mặc định của Chatbot (`chatbot_welcome_message`). | `System_Configs` |
| **SA-CONFIG-03** | **Lưu cấu hình** | Nhấn "Lưu cấu hình". Hệ thống thực hiện UPSERT vào bảng `System_Configs` (ON CONFLICT DO UPDATE). Cấu hình có hiệu lực ngay lập tức (reload tại runtime). | `System_Configs` |

### 6.3. Luồng xử lý chính (Admin Flow)

```
┌────────────────┐     ┌──────────────────────────────────────────────┐
│  Đăng nhập     │────▶│  Tab 1: 👥 Nhân sự                          │
│  Portal Admin  │     │  → Xem / Tạo / Khóa tài khoản               │
└────────────────┘     ├──────────────────────────────────────────────┤
                       │  Tab 2: 🗂️ RAG                              │
                       │  → Xem / Nạp tri thức mới                    │
                       ├──────────────────────────────────────────────┤
                       │  Tab 3: 📈 Thống kê                          │
                       │  → Dashboard: Metrics + Biểu đồ              │
                       ├──────────────────────────────────────────────┤
                       │  Tab 4: 💬 Debug                              │
                       │  → Xem Message Logs gần nhất                 │
                       ├──────────────────────────────────────────────┤
                       │  Tab 5: ⚙️ Cấu hình AI                      │
                       │  → Ngưỡng confidence, Tin nhắn chào          │
                       └──────────────────────────────────────────────┘
```

---

## 7. MA TRẬN PHÂN QUYỀN TỔNG HỢP

| Chức năng | Bệnh nhân | Bác sĩ | Chuyên viên TT | Admin IT |
|:---|:---:|:---:|:---:|:---:|
| Đăng ký tài khoản | ✅ | ❌ | ❌ | ❌ |
| Đăng nhập / Đăng xuất | ✅ | ✅ | ✅ | ✅ |
| Chatbot sàng lọc triệu chứng | ✅ | ❌ | ❌ | ❌ |
| Xem/Cập nhật hồ sơ sức khỏe | ✅ | ❌ | ❌ | ❌ |
| Xem lịch sử tư vấn cá nhân | ✅ | ❌ | ❌ | ❌ |
| Xem hàng đợi sàng lọc (theo khoa) | ❌ | ✅ | ❌ | ✅* |
| Xem chi tiết báo cáo sàng lọc | ❌ | ✅ | ❌ | ✅* |
| Feedback Loop — Xác minh AI | ❌ | ✅ | ❌ | ✅* |
| Xuất báo cáo sàng lọc | ❌ | ✅ | ❌ | ❌ |
| Quản lý Chuyên khoa | ❌ | ❌ | ✅ (Xem) | ❌ |
| Quản lý Triệu chứng | ❌ | ❌ | ✅ | ❌ |
| Quản lý Bệnh lý | ❌ | ❌ | ✅ | ❌ |
| Quản lý Luật suy diễn | ❌ | ❌ | ✅ | ❌ |
| Sandbox kiểm thử AI | ❌ | ❌ | ✅ | ❌ |
| Quản lý tài khoản nhân sự | ❌ | ❌ | ❌ | ✅ |
| Nạp dữ liệu RAG | ❌ | ❌ | ❌ | ✅ |
| Xem Dashboard thống kê | ❌ | ❌ | ❌ | ✅ |
| Debug AI Logs | ❌ | ❌ | ❌ | ✅ |
| Cấu hình tham số AI | ❌ | ❌ | ❌ | ✅ |

> *\* Admin có quyền truy cập hàng đợi sàng lọc và chi tiết báo cáo (cùng quyền với Doctor trong API `/api/doctor/`).*

---

## 8. YÊU CẦU PHI CHỨC NĂNG

### 8.1. Bảo mật (Security)
| Mã | Yêu cầu | Mô tả |
|:---:|:---|:---|
| NFR-SEC-01 | Mã hóa mật khẩu | Tất cả mật khẩu được hash bằng **Bcrypt** trước khi lưu DB |
| NFR-SEC-02 | Phân quyền API | Mỗi endpoint kiểm tra `session['user_type']` trước khi xử lý. Trả 403 nếu không đủ quyền |
| NFR-SEC-03 | Bảo vệ Admin | Admin không thể tự khóa tài khoản chính mình |
| NFR-SEC-04 | CORS | Hỗ trợ CORS với `supports_credentials=True` |

### 8.2. Hiệu năng (Performance)
| Mã | Yêu cầu | Mô tả |
|:---:|:---|:---|
| NFR-PERF-01 | Offline 100% | Hệ thống chạy hoàn toàn offline, không gọi API bên ngoài |
| NFR-PERF-02 | AI Engine Singleton | Model NLP chỉ load 1 lần duy nhất khi khởi động (`@st.cache_resource`) |
| NFR-PERF-03 | Connection Pooling | Database connection tự động tạo lại nếu bị đóng hoặc lỗi |
| NFR-PERF-04 | Phân trang | Các danh sách dữ liệu lớn giới hạn LIMIT (20-50 records/trang) |

### 8.3. Khả dụng (Usability)
| Mã | Yêu cầu | Mô tả |
|:---:|:---|:---|
| NFR-USE-01 | Ngôn ngữ | Giao diện hoàn toàn bằng **Tiếng Việt** |
| NFR-USE-02 | Guest Mode | Cho phép khách (chưa đăng nhập) sử dụng chatbot |
| NFR-USE-03 | Tối đa 6 câu hỏi | Chatbot không hỏi quá 6 câu hỏi xác nhận follow-up để tránh gây phiền |
| NFR-USE-04 | Disclaimer | Kết quả sàng lọc kèm cảnh báo "Chỉ mang tính tham khảo, không thay thế chẩn đoán bác sĩ" |

### 8.4. Triển khai (Deployment)
| Mã | Yêu cầu | Mô tả |
|:---:|:---|:---|
| NFR-DEP-01 | Docker Compose | Hệ thống đóng gói bằng Docker Compose (App + PostgreSQL + pgvector) |
| NFR-DEP-02 | Biến môi trường | Cấu hình DB và Secret Key qua file `.env` |
| NFR-DEP-03 | Port mặc định | Flask chạy port `5002`, Streamlit chạy port `8501`, PostgreSQL port `5433` |

---

## PHỤ LỤC: SƠ ĐỒ QUAN HỆ CÁC BẢNG DỮ LIỆU

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Specialties │◄────│   Diseases   │◄────│ Knowledge_Rules  │
│  (Chuyên    │     │  (Bệnh lý)  │     │  (Luật suy diễn) │
│   khoa)     │     └──────────────┘     └────────┬─────────┘
└──────┬──────┘                                    │
       │                                    ┌──────▼─────────┐
       │          ┌──────────────┐          │    Symptoms     │
       │          │   Patients   │          │  (Triệu chứng) │
       │          │ (Bệnh nhân) │          └──────┬──────────┘
       │          └──────┬───────┘                 │
       │                 │                  ┌──────▼──────────┐
       │          ┌──────▼───────┐          │Symptom_Synonyms │
       │          │Medical_      │          │(Từ đồng nghĩa)  │
       │          │ Profiles     │          └─────────────────┘
       │          └──────────────┘
       │
       │          ┌──────────────┐     ┌──────────────────┐
       ├──────────│Chat_Sessions │────▶│  Message_Logs    │
       │          │ (Phiên chat) │     │  (Log tin nhắn)  │
       │          └──────┬───────┘     └──────────────────┘
       │                 │
       │          ┌──────▼──────────────┐
       │          │Session_Symptoms     │
       │          │(Triệu chứng phiên) │
       │          └─────────────────────┘
       │          ┌──────────────────────┐
       │          │Session_Disease_Scores│
       │          │(Điểm bệnh lý)       │
       │          └──────────────────────┘
       │          ┌──────────────────────┐
       │          │Session_Recommendations│
       │          │(Khuyến nghị)          │
       │          └──────────────────────┘

┌─────────────────┐     ┌──────────────────┐
│ Staff_Accounts  │     │ Knowledge_Chunks │
│ (Tài khoản NV)  │     │ (Kho tri thức)   │
└─────────────────┘     └──────────────────┘

┌─────────────────┐
│ System_Configs  │
│ (Cấu hình HT)  │
└─────────────────┘
```

---

> 📝 **Ghi chú:** Tài liệu SRS này được xây dựng dựa trên phân tích source code thực tế của dự án (server.py, app_web.py, chatbot_logic.py, triage_engine.py, schema.sql) kết hợp với tài liệu yêu cầu nghiệp vụ đã có (database chatbot sàng lọc bệnh.md).
