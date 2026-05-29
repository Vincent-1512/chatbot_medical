# XÁC ĐỊNH YÊU CẦU HỆ THỐNG

**Đề tài:** Chatbot sàng lọc triệu chứng bệnh: Tích hợp hệ chuyên gia vào website phòng khám để hỏi bệnh nhân về các triệu chứng và gợi ý chuyên khoa cần khám.

## Phạm vi áp dụng đề tài

* **Phạm vi nghiệp vụ:** Hệ thống số hóa quy trình tư vấn y tế ban đầu và hỗ trợ chẩn đoán sơ bộ thông qua giao diện trò chuyện (Chatbot). Hệ thống kết hợp Khai phá dữ liệu văn bản (NLP), công nghệ Truy xuất Tăng cường (RAG – Retrieval-Augmented Generation) và Hệ chuyên gia (Expert System) để tự động phân tích triệu chứng từ ngôn ngữ tự nhiên, đối chiếu với cơ sở tri thức y khoa, dự đoán bệnh lý tiềm năng và đưa ra gợi ý chuyên khoa phù hợp nhất.

* **Phạm vi đối tượng:** Phục vụ **Bệnh nhân** (tương tác chat trực tiếp, khai báo triệu chứng bằng ngôn ngữ tự nhiên), **Bác sĩ/Quản trị Y khoa** (cấu hình bộ luật tri thức, quản lý triệu chứng/bệnh lý, theo dõi ca chờ khám) và **Quản trị viên / IT** (quản lý tài khoản nội bộ, nạp dữ liệu RAG, theo dõi hiệu năng hệ thống AI).

* **Giới hạn đề tài:** Hệ thống tập trung vào sàng lọc triệu chứng và gợi ý chuyên khoa ban đầu, mang tính hỗ trợ và không thay thế hoàn toàn quyết định của bác sĩ. Không bao gồm các nghiệp vụ thanh toán viện phí, đặt lịch khám chi tiết, hay kê đơn thuốc.

## Các bước xác định yêu cầu

Quá trình thực hiện xác định yêu cầu gồm 2 bước chính như sau:

* **Bước 1:** Khảo sát hiện trạng, kết quả nhận được là các báo cáo về quy trình tư vấn y tế ban đầu tại phòng khám và nhu cầu tư vấn y tế từ xa của bệnh nhân.
* **Bước 2:** Lập danh sách các yêu cầu, kết quả nhận được là danh sách các yêu cầu chức năng và phi chức năng sẽ được thực hiện trên hệ thống phần mềm.

---

## 1. Đối tượng tham gia xác định yêu cầu

Gồm 2 nhóm người:

* **Chuyên viên tin học (Kỹ sư IT/AI):** Thiết kế kiến trúc nhận diện thực thể (Named Entity Recognition – NER), xây dựng kho tri thức RAG bằng cơ sở dữ liệu Vector (PostgreSQL + pgvector), triển khai mô hình nhúng ngôn ngữ (SentenceTransformer – BAAI/bge-m3) và lập trình Động cơ suy diễn (Inference Engine) dựa trên tập luật trọng số.

* **Nhà chuyên môn (Bác sĩ, Cán bộ y tế):** Cung cấp danh mục chuyên khoa, từ điển triệu chứng chuẩn y khoa, thiết lập bộ luật chẩn đoán (Knowledge Rules) bao gồm trọng số (weight), luật bắt buộc (is\_mandatory) và luật loại trừ (is\_exclusion). Trực tiếp biên soạn và chuẩn hóa bộ dữ liệu văn bản y khoa để nạp vào kho tri thức AI.

Hai nhóm người này phối hợp thật chặt chẽ để có thể xác định đầy đủ và chính xác các yêu cầu.

---

## 2. Khảo sát hiện trạng quy trình tư vấn y tế ban đầu

### 2.1. Mục tiêu khảo sát

Tìm hiểu chi tiết cách thức phòng khám hiện tại đang tiếp nhận bệnh nhân và tư vấn chuyên khoa thủ công (qua lễ tân hoặc y tá trực). Từ đó, xác định các "điểm nghẽn" trong quá trình giao tiếp để chuyển đổi sang mô hình Chatbot tự động, giúp tối ưu hóa thời gian chờ đợi và tăng độ chính xác khi gợi ý chuyên khoa lâm sàng.

### 2.2. Các hình thức thực hiện khảo sát

Để thu thập dữ liệu đa chiều, dự án sử dụng kết hợp các phương pháp sau:

* **Quan sát thực tế (Observation):**
    * Theo dõi trực tiếp quá trình bệnh nhân mô tả triệu chứng bằng ngôn ngữ đời thường cho nhân viên tư vấn tại quầy tiếp đón.
    * Ghi nhận cách thức nhân viên y tế đặt các "câu hỏi đóng" (Có/Không) để xác nhận hoặc loại trừ các chuyên khoa không liên quan.

* **Phỏng vấn chuyên sâu (Interviews):**
    * *Đối với Bác sĩ/Chuyên gia Y tế:* Khai thác tư duy chẩn đoán (Diagnostic Logic). Ví dụ: Đặt câu hỏi *"Khi bệnh nhân kêu đau đầu, bác sĩ sẽ hỏi thêm những triệu chứng đi kèm nào để phân biệt giữa chuyên khoa Thần kinh và chuyên khoa Tai Mũi Họng?"*.
    * *Đối với Bệnh nhân:* Tìm hiểu những khó khăn khi tự đánh giá bệnh trạng, nguyên nhân dẫn đến việc đi khám sai chuyên khoa và thói quen sử dụng từ ngữ mô tả bệnh (phục vụ cho việc nhận diện thực thể – NER sau này).

### 2.3. Thu thập thông tin và tài liệu (Data Collection)

Quá trình số hóa Hệ chuyên gia đòi hỏi các nguồn tài liệu đầu vào có tính chính xác cao:

* **Tài liệu hành chính:**
    * Danh mục các chuyên khoa hiện có của phòng khám (Mục tiêu: Làm dữ liệu đích – Target Output cho thuật toán gợi ý).
    * Các biểu mẫu khai báo y tế cơ bản (tiền sử bệnh lý, dị ứng, nhóm máu) để xây dựng bộ hồ sơ người dùng tiêu chuẩn.

* **Tài liệu chuyên môn Y khoa:**
    * Sổ tay hướng dẫn phân loại bệnh lý, giáo trình y khoa (Ví dụ: Giáo trình bệnh truyền nhiễm, nội khoa).
    * *Mục đích:* Dùng làm cơ sở tri thức (Knowledge Base) để lập trình các tập luật (Rules) – định nghĩa trọng số giữa các Triệu chứng (`Symptoms`) và Bệnh lý (`Diseases`) cho Động cơ suy diễn (Inference Engine) của phần mềm.

---

## 3. Quy trình thực hiện khảo sát và phân tích

### 3.1. Tìm hiểu tổng quan về thế giới thực

Hệ thống Chatbot đóng vai trò như một "Trợ lý tư vấn y tế kỹ thuật số" (Digital Medical Assistant), hoạt động 24/7 để hỗ trợ tư vấn y tế ban đầu. Mục tiêu cốt lõi là giải quyết tình trạng bệnh nhân không có chuyên môn y tế, mô tả triệu chứng mơ hồ dẫn đến đi khám sai chuyên khoa, đồng thời giảm tải áp lực khai thác bệnh sử thủ công (hỏi đáp lặp đi lặp lại) cho đội ngũ y tế tại quầy tiếp đón.

### 3.2. Tìm hiểu hiện trạng tổ chức (Xác định các tác nhân tham gia)

Cơ cấu vận hành của hệ thống phần mềm xoay quanh 3 nhóm đối tượng chính với vai trò tách biệt:

* **Đối ngoại (Bệnh nhân / Người dùng cuối):** **Quyền hạn:** Là người trực tiếp tương tác với Chatbot bằng văn bản (ngôn ngữ tự nhiên) để khai báo bệnh trạng và nhận tư vấn gợi ý chuyên khoa. **Trách nhiệm:** Cung cấp thông tin chính xác để hệ thống gợi ý chuyên khoa phù hợp.

* **Đối nội (Bác sĩ / Nhân viên y tế):** **Quyền hạn:** Được hệ thống tự động phân quyền truy cập, hiển thị và tra cứu "Phiếu tóm tắt triệu chứng" cùng lịch sử phiên chat của những bệnh nhân được gợi ý về khoa mình. **Trách nhiệm:** Kiểm tra đối chiếu thông tin sàng lọc của AI để làm cơ sở lâm sàng nhanh, đảm bảo tính chính xác trước khi tiếp nhận bệnh nhân vào khám thực tế.

* **Đối nội (Quản trị viên / Kỹ sư tri thức y khoa):** **Quyền hạn:** Được quyền nạp dữ liệu y khoa, cấu hình trọng số và tinh chỉnh các tập luật (Rules) cho Hệ chuyên gia. **Trách nhiệm:**  Đảm bảo tính chính xác, an toàn của cơ sở tri thức y tế.

### 3.3. Tìm hiểu hiện trạng nghiệp vụ (Phân loại công việc trên máy tính)

Toàn bộ quy trình hoạt động của hệ thống được bóc tách và phân thành 4 nhóm nghiệp vụ đặc thù của một Hệ chuyên gia:

* **Nghiệp vụ Tra cứu (Retrieval):**
    * Hệ thống tự động tra cứu danh mục "Từ đồng nghĩa" (`Symptom_Synonyms`) để ánh xạ ngôn ngữ đời thường của bệnh nhân sang từ vựng y khoa chuẩn.
    * Bác sĩ tra cứu lại nguyên văn lịch sử trò chuyện (`Message_Logs`) của bệnh nhân khi cần đối chiếu.

* **Nghiệp vụ Lưu trữ (Storage):**
    * Ghi nhận và số hóa các triệu chứng mà mô hình NLP đã bóc tách được (`Session_Symptoms`) kèm theo độ tin cậy.
    * Lưu vết quá trình tư duy và chấm điểm của AI (`Session_Disease_Scores`) để phục vụ công tác kiểm toán y khoa.

* **Nghiệp vụ Tính toán & Logic (Processing & Reasoning):**
    * Đây là nghiệp vụ cốt lõi nhất. Động cơ suy diễn (Inference Engine) thực hiện tính toán tổng điểm trọng số (`weight`) của các triệu chứng, đồng thời quét qua các bộ luật bắt buộc (`is_mandatory`) và luật loại trừ (`is_exclusion`) để triệt tiêu các bệnh lý không phù hợp.

* **Nghiệp vụ Tổng hợp, Thống kê (Output/Reporting):**
    * Hiển thị kết luận cuối cùng trên màn hình Chatbot để gợi ý người bệnh đến đúng chuyên khoa.
    * Tự động sinh ra "Phiếu tóm tắt sàng lọc" đính kèm vào hồ sơ bệnh án điện tử để chuyển lên phòng khám chuyên khoa tương ứng.
    * Hệ thống tổng hợp lưu lượng bệnh nhân được gợi ý về các chuyên khoa theo ngày/tháng để phục vụ công tác thống kê, báo cáo tình hình tại phòng khám.

---

## 4. Lập danh sách các yêu cầu

Dựa trên kết quả khảo sát hiện trạng, tiến hành xác định các chức năng hệ thống sẽ thực hiện trên máy tính. Vì phạm vi dự án tập trung hoàn toàn vào Khai phá dữ liệu văn bản (NLP) và Hệ chuyên gia (Expert System), các yêu cầu chức năng nghiệp vụ được phân chia theo 3 bộ phận người dùng cốt lõi như sau:

### 4.1. Bảng yêu cầu chức năng nghiệp vụ tổng quan (Master Epic List)

| Mã Phân hệ | Tên Phân hệ (Module) | Mã Epic | Tên Nghiệp vụ Tổng quan (Epic) | Khối Giá trị mang lại (Value Proposition) |
|:---:|:---|:---:|:---|:---|
| MOD-01 | Hệ tri thức Y khoa (Medical Knowledge Base) | EP-01 | Quản trị Cây tri thức Y khoa (Ontology Management) | Số hóa và cấu trúc hóa toàn bộ danh mục bệnh lý, triệu chứng lâm sàng thành một hệ sinh thái dữ liệu chuẩn mực, làm nền tảng cốt lõi cho AI học tập và suy diễn. |
| | | EP-02 | Cấu hình Động cơ Suy diễn (Inference Engine Setup) | Trao quyền cho chuyên gia y tế thiết lập hệ thống luật (Rules), ma trận trọng số, đảm bảo mọi quyết định của AI đều minh bạch và tuân thủ chuẩn y khoa. |
| MOD-02 | Tương tác Sàng lọc (Chatbot Engine) | EP-03 | Khai thác Triệu chứng Tự nhiên (Natural Symptom Extraction) | Ứng dụng NLP để tự động nhận diện, bóc tách và phân loại các dấu hiệu bất thường từ ngôn ngữ giao tiếp tự do của bệnh nhân theo thời gian thực. |
| | | EP-04 | Suy diễn Bệnh lý & Gợi ý Lâm sàng (Clinical Suggestion) | Tự động đối chiếu dữ kiện với hệ tri thức để tính toán điểm số bệnh lý, từ đó gợi ý chuyên khoa phù hợp nhất cho bệnh nhân đi khám. |
| | | EP-05 | Kết xuất Báo cáo Hỗ trợ Quyết định (Decision Support Reporting) | Đóng gói toàn bộ lịch sử hội thoại và kết quả suy diễn thành "Phiếu tóm tắt sàng lọc", giúp bác sĩ tiết kiệm thời gian khai thác bệnh sử và tăng độ chính xác khi thăm khám. |
| MOD-03 | Quản lý Định danh (Identity Management) | EP-06 | Quản lý Truy cập & Phân quyền (Access Control) | Quản lý vòng đời tài khoản của đa dạng người dùng (Admin, Bác sĩ, Bệnh nhân) và hỗ trợ chế độ Khách (Guest) để tối ưu hóa phễu trải nghiệm mà không gây rào cản đăng nhập. |
| | | EP-07 | Số hóa Tiền sử Y tế (Medical Profile Digitization) | Thu thập và lưu trữ an toàn các chỉ số sinh tồn, tiền sử dị ứng, bệnh nền của bệnh nhân, biến chúng thành các tham số tĩnh để cá nhân hóa kết quả sàng lọc của AI. |

---

### 4.2. Xác định yêu cầu chức năng nghiệp vụ chi tiết

---

## A. BỘ PHẬN: NGƯỜI DÙNG (BỆNH NHÂN) | Mã số: BN

### 1. Bảng yêu cầu chức năng nghiệp vụ

| STT | Công việc | Loại việc | Quy định | Ghi chú giao diện |
|:---:|:---|:---:|:---:|:---|
| **I. Quản lý tài khoản cá nhân** | | | | |
| 1 | Đăng ký tài khoản mới | Lưu trữ | BN_QĐ 1 | Form nhập Họ tên, Số điện thoại, Giới tính, Mật khẩu. Nút ẩn/hiện mật khẩu. |
| 2 | Đăng nhập hệ thống | Tra cứu | BN_QĐ 2 | Cho phép đăng nhập bằng Số điện thoại + Mật khẩu. Tab chuyển đổi vai trò Bệnh nhân / Nhân viên. |
| 3 | Quên mật khẩu | Lưu trữ | BN_QĐ 2b | Nhấn "Quên mật khẩu", nhập SĐT để nhận mã OTP khôi phục. |
| 4 | Đăng xuất | Hệ thống | — | Nhấn avatar góc phải, chọn "Đăng xuất". |
| **II. Hồ sơ bệnh nhân** | | | | |
| 4 | Xem thông tin hồ sơ y tế | Tra cứu | BN_QĐ 3 | Hiển thị hồ sơ dạng thẻ: Tên, Giới tính, Chiều cao, Cân nặng, Nhóm máu, Dị ứng, Bệnh nền. |
| 5 | Cập nhật tiền sử bệnh lý | Lưu trữ | BN_QĐ 4 | Ô nhập text "Dị ứng", "Bệnh nền". Ô số "Chiều cao", "Cân nặng". Nút "Lưu". Khóa cứng (Read-only) các trường: Tên, SĐT, Giới tính. |
| **III. Tương tác AI (Chatbot Sàng lọc)** | | | | |
| 6 | Khởi tạo phiên tư vấn mới | Lưu trữ | BN_QĐ 5 | Bấm "Bắt đầu tư vấn". Giao diện khung chat mở ra kèm tin nhắn chào mừng tự động từ AI. |
| 7 | Trò chuyện khai báo bệnh trạng | Tra cứu, Tính toán | BN_QĐ 6 | Gõ văn bản mô tả triệu chứng tự do vào ô input, bấm Enter hoặc nút "Gửi". |
| 8 | Trả lời câu hỏi xác nhận AI | Tra cứu, Tính toán | BN_QĐ 7 | Đọc câu hỏi AI (VD: "Bạn có bị đau đầu không?"). Chọn nút phản hồi nhanh: [Có], [Không], [Không rõ]. |
| 9 | Nhận kết quả sàng lọc | Kết xuất | BN_QĐ 8 | Khung nhập bị khóa. Hiển thị "Phiếu kết quả": Chuyên khoa gợi ý, Bệnh lý nghi ngờ, Lời khuyên chăm sóc. |
| 10 | Kết thúc phiên Chatbot | Hệ thống | BN_QĐ 9 | Bấm nút [X] hoặc "Đóng Chatbot" ở góc màn hình. |
| **IV. Tra cứu lịch sử** | | | | |
| 11 | Tra cứu danh sách tư vấn | Tra cứu | BN_QĐ 10 | Click tab "Lịch sử tư vấn". Xem danh sách thẻ tóm tắt (Mã phiên, Ngày giờ, Chuyên khoa gợi ý). Phân trang 10 dòng/trang. |
| 12 | Xem chi tiết phiên chat cũ | Tra cứu | BN_QĐ 11 | Click vào 1 thẻ lịch sử. Xem lại toàn bộ bong bóng chat cũ và Phiếu kết quả. Khung nhập bị ẩn (Read-only). |

### 2. Bảng Quy định / Công thức liên quan — Bệnh nhân

**BN_QĐ 1 — Quy định Đăng ký tài khoản**

| STT | Tên thông tin | Định dạng nhập | Bắt buộc | Ràng buộc / Ghi chú |
|:---:|:---|:---:|:---:|:---|
| 1 | Số điện thoại | Ký tự số (tối đa 15) | **Có** | Là định danh chính (primary key logic). Không được trùng lặp trong hệ thống (`UNIQUE` constraint trên bảng `Patients`). |
| 2 | Họ và tên | Văn bản (tối đa 100 ký tự) | **Có** | Tên đầy đủ của bệnh nhân. |
| 3 | Giới tính | Danh sách chọn (Nam/Nữ) | Không | Lưu vào cột `gender` bảng `Patients`. |
| 4 | Mật khẩu | Văn bản | **Có** | Hệ thống tự động mã hóa bằng thuật toán **Bcrypt** trước khi lưu trữ vào cột `external_patient_id` dưới định dạng JSON `{"phone": "...", "pw": "$2b$..."}`. |

Quy tắc xử lý:
* Hệ thống sẽ tự động tạo một `Medical_Profiles` (hồ sơ y tế trống) liên kết với tài khoản `Patients` mới ngay khi đăng ký thành công.
* Tài khoản được tạo thành công sẽ tự động đăng nhập và chuyển vào màn hình chính.

**BN_QĐ 2 — Quy định Đăng nhập**

| STT | Tên thông tin | Định dạng nhập | Bắt buộc | Ràng buộc / Ghi chú |
|:---:|:---|:---:|:---:|:---|
| 1 | Số điện thoại | Ký tự số | **Có** | Dùng để truy vấn bản ghi trong bảng `Patients`. |
| 2 | Mật khẩu | Văn bản | **Có** | Hệ thống đối chiếu với hash Bcrypt đã lưu trong `external_patient_id`. |

Quy tắc xử lý:
* Nếu nhập sai thông tin, hệ thống chỉ báo chung chung *"Thông tin đăng nhập không chính xác"* để bảo vệ thông tin.
* Sau khi đăng nhập thành công, hệ thống thiết lập Session lưu `patient_id`, `user_type`, `user_name` phía server.

**BN_QĐ 2b — Quy định Quên mật khẩu (Bệnh nhân)**
* Bệnh nhân chọn "Quên mật khẩu" và nhập Số điện thoại đã đăng ký.
* Hệ thống kiểm tra SĐT trong bảng `Patients`. Nếu hợp lệ, hệ thống sinh mã OTP có thời hạn và gửi qua SMS (hoặc giả lập trả về UI).
* Sau khi bệnh nhân xác thực OTP thành công, cho phép thiết lập mật khẩu mới. Mật khẩu mới tự động được mã hóa Bcrypt trước khi lưu vào DB.

**BN_QĐ 3 — Quy định Xem thông tin hồ sơ y tế**
* Quyền truy cập: Bệnh nhân chỉ xem được hồ sơ của chính mình sau khi đã đăng nhập.
* Dữ liệu hiển thị: Thực hiện phép `JOIN` bảng `Patients` và `Medical_Profiles` theo `patient_id`. Trả về: Tên, SĐT, Giới tính, Chiều cao, Cân nặng, Nhóm máu, Dị ứng, Bệnh nền.
* Ràng buộc UI: Khóa cứng (Read-only) các trường thông tin hành chính (Tên, SĐT, Giới tính) — chỉ cho phép chỉnh sửa thông tin y tế.

**BN_QĐ 4 — Quy định Cập nhật Tiền sử bệnh lý**

| STT | Tên thông tin | Định dạng nhập | Được sửa | Ghi chú |
|:---:|:---|:---:|:---:|:---|
| 1 | Họ và tên | Văn bản | **Không** | Thông tin định danh cốt lõi, không được phép thay đổi. |
| 2 | Số điện thoại | Ký tự số | **Không** | Thông tin đăng nhập, không được phép thay đổi. |
| 3 | Chiều cao (cm) | Số thực | **Có** | Validate: > 0. |
| 4 | Cân nặng (kg) | Số thực | **Có** | Validate: > 0. |
| 5 | Nhóm máu | Danh sách chọn | **Có** | Các giá trị: A, B, AB, O. |
| 6 | Tiền sử dị ứng | Văn bản | **Có** | Nhập tự do, có tùy chọn "Không có". |
| 7 | Bệnh nền | Văn bản | **Có** | Nhập tự do, có tùy chọn "Không có". |

Quy tắc xử lý: Thực hiện lệnh `UPSERT` vào bảng `Medical_Profiles` (nếu chưa có thì `INSERT`, nếu có rồi thì `UPDATE`). Trả về HTTP 200 để Frontend hiển thị thông báo thành công.

**BN_QĐ 5 — Quy định Khởi tạo phiên tư vấn**
* Hệ thống `INSERT` 1 dòng vào bảng `Chat_Sessions` với `status = 'in_progress'`.
* Sinh ra `session_id` trả về cho Frontend quản lý state.
* Kích hoạt API gửi câu chào mặc định: *"Xin chào! Tôi là trợ lý AI sàng lọc triệu chứng của phòng khám. Bạn hãy mô tả các triệu chứng bạn đang gặp phải nhé."*
* Hỗ trợ chế độ **Khách (Guest):** Nếu bệnh nhân chưa đăng nhập, hệ thống tự tạo bản ghi `Patients` tạm (`GUEST_TEMP`) để vẫn cho phép sử dụng Chatbot.

**BN_QĐ 6 — Quy định Trò chuyện khai báo bệnh trạng**
* `INSERT` text vào `Message_Logs` (`sender_type = 'patient'`).
* Đẩy text qua Model NER (`SymptomExtractor`) sử dụng `SentenceTransformer` (BAAI/bge-m3) để bóc tách thực thể triệu chứng bằng kỹ thuật so sánh Vector cosine similarity (ngưỡng ≥ 0.78).
* `INSERT` danh sách ID triệu chứng vào `Session_Symptoms` với `is_present = true`, `confidence` từ AI, và `source = 'llm_extract'`.

**BN_QĐ 7 — Quy định Trả lời câu hỏi xác nhận AI**
* Nhận payload từ nút bấm. Phân loại câu trả lời bằng bộ từ khóa YES/NO/UNSURE.
* Nếu **Có**: `INSERT` vào `Session_Symptoms` với `is_present = true`, `source = 'confirmation'`, `confidence = 0.95`.
* Nếu **Không**: `INSERT` vào `Session_Symptoms` với `is_present = false`.
* Kích hoạt Động cơ suy diễn (Inference Engine) tính lại tổng điểm sau mỗi câu trả lời.
* Hệ thống hỏi tối đa **6 câu hỏi xác nhận**. Ưu tiên hỏi: triệu chứng `is_mandatory` > triệu chứng xuất hiện ở nhiều bệnh ứng viên > triệu chứng có `weight` cao.

**BN_QĐ 8 — Quy định Nhận kết quả sàng lọc**
* Khi điểm vượt ngưỡng hoặc đã hỏi đủ 6 câu:
    1. `INSERT` điểm số vào `Session_Disease_Scores` (top 3 bệnh, gồm `disease_id`, `hybrid_score`, `rank`).
    2. `INSERT` nội dung phiếu kết quả vào `Session_Recommendations`.
    3. `UPDATE` cột `suggested_specialty_id`, `end_time`, `status='completed'` trong `Chat_Sessions`.
* Bắn cờ disable UI ô chat.

**BN_QĐ 9 — Quy định Kết thúc phiên Chatbot**
* `UPDATE` cột `status` trong `Chat_Sessions` thành `completed` (nếu đã có kết quả) hoặc `abandoned` (nếu thoát ngang).
* Xóa state nội bộ trên server (bộ nhớ `active_chats`).

**BN_QĐ 10 — Quy định Tra cứu lịch sử tư vấn**
* `SELECT` danh sách từ `Chat_Sessions` dựa theo `patient_id`.
* Ràng buộc Query: Ép buộc dùng `ORDER BY start_time DESC`. Phân trang bằng Limit/Offset (10 items/page).

**BN_QĐ 11 — Quy định Xem chi tiết phiên chat cũ**
* Truyền `session_id` để `SELECT` toàn bộ record trong `Message_Logs` và `Session_Recommendations`.
* Render UI ở trạng thái Read-only. Chặn mọi thao tác gửi tin nhắn mới.

### 3. Biểu mẫu tiêu biểu (Bệnh nhân)

**BN_BM 1: PHIẾU KẾT QUẢ SÀNG LỌC AI**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 KẾT QUẢ SÀNG LỌC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏥 Chuyên khoa gợi ý:    Tai Mũi Họng

Bệnh lý có thể liên quan:
  1. Viêm họng cấp      [●●●●●●●○○○] (7.0 điểm)
  2. Viêm amidan         [●●●●●○○○○○] (5.0 điểm)
  3. Cảm cúm thông thường[●●●○○○○○○○] (3.0 điểm)

✅ Triệu chứng ghi nhận: đau họng, sốt nhẹ, ho
❌ Triệu chứng đã loại trừ: khó thở

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Kết quả chỉ mang tính tham khảo.
   Vui lòng đến phòng khám để được bác sĩ thăm khám trực tiếp.
```

---

## B. BỘ PHẬN: NHÂN VIÊN Y TẾ (QUẢN TRỊ TRI THỨC / BÁC SĨ) | Mã số: BS

### TẦNG 1: NGHIỆP VỤ LÂM SÀNG (BÁC SĨ TRỰC)

#### 1. Bảng yêu cầu chức năng nghiệp vụ

| Mã ID | Tên chức năng (Feature) | Thao tác của Bác sĩ trên UI (User Actions) | Xử lý ngầm của Hệ thống (Backend & Database) |
|:---|:---|:---|:---|
| **DOC-01** | **Đăng nhập Portal Y tế** | Nhập Email/Username và Mật khẩu tại trang Đăng nhập nội bộ. Nhấn "Đăng nhập". | Nhận payload, truy vấn bảng `Staff_Accounts`. So khớp giải mã Bcrypt. • Xử lý Session: Lưu `staff_id`, `role`, `specialty_id` (Mã khoa trực) vào server session. • Trả về HTTP 200. |
| **DOC-01b**| **Quên mật khẩu** | Chọn "Quên mật khẩu", nhập Email nội bộ để yêu cầu khôi phục. | Truy vấn bảng `Staff_Accounts`. Gửi liên kết hoặc mã OTP qua Email. Mã hóa Bcrypt mật khẩu mới khi thiết lập lại. |
| **DOC-02** | **Đăng xuất hệ thống** | Nhấn avatar góc phải màn hình, chọn "Đăng xuất". Trở về màn hình đăng nhập. | Xóa toàn bộ dữ liệu Session phía server. |
| **DOC-03** | **Xem chi tiết Báo cáo Sàng lọc** | Click vào 1 ca bệnh cụ thể (thông qua tìm kiếm). Màn hình chia làm 2 phần tĩnh (Read-only): **1.** Bên trái: Thông tin cá nhân, Tiền sử dị ứng, Bệnh nền, Chỉ số sinh tồn. **2.** Bên phải: Phiếu tóm tắt gợi ý của AI và Lịch sử nguyên văn đoạn chat. | Lấy `session_id` để query song song 4 luồng: **1.** Hồ sơ: `JOIN Patients` & `Medical_Profiles`. **2.** Log chat: `SELECT` từ `Message_Logs`. **3.** Kết quả chẩn đoán: `Session_Disease_Scores`. **4.** Phiếu tóm tắt: `Session_Recommendations`. |
| **DOC-04** | **Xác nhận / Đánh giá AI (Feedback Loop)** | Cuộn xuống cuối Phiếu kết quả. Bác sĩ đối chiếu với kết quả khám thực tế, sau đó nhấn chọn: • [AI chẩn đoán Đúng] • [AI chẩn đoán Sai] → Chọn lại bệnh lý thực tế từ danh sách Dropdown. | **Đây là lõi thu thập dữ liệu huấn luyện (Data Pipeline):** • Nhận payload đánh giá. `UPDATE` bảng `Session_Disease_Scores`. • Bổ sung cờ `is_doctor_verified = true/false` và `actual_disease_id` (nếu AI sai). Dữ liệu này lưu trữ làm Fact để tái huấn luyện trọng số cho model AI sau này. |

#### 2. Bảng Quy định liên quan — Bác sĩ trực

**BS_QĐ 1 — Quy định Đăng nhập nội bộ**

| STT | Tên thông tin | Định dạng nhập | Bắt buộc | Ràng buộc / Ghi chú |
|:---:|:---|:---:|:---:|:---|
| 1 | Email / Username | Văn bản | **Có** | Cho phép dùng 1 trong 2 thông tin để đăng nhập. Truy vấn bảng `Staff_Accounts`. |
| 2 | Mật khẩu | Văn bản | **Có** | Hệ thống đối chiếu với `password_hash` đã mã hóa Bcrypt. |

Quy tắc xử lý:
* Nếu nhập sai thông tin, hệ thống chỉ báo chung chung *"Tên đăng nhập hoặc mật khẩu không chính xác"* để bảo vệ thông tin.
* Hệ thống kiểm tra trường `role` trong `Staff_Accounts` để xác định giao diện hiển thị: `doctor` → Portal Bác sĩ, `admin` → Portal Quản trị.

**BS_QĐ 1b — Quy định Quên mật khẩu (Nhân viên Y tế / Bác sĩ)**
* Tại trang đăng nhập Portal nội bộ, chọn "Quên mật khẩu" và nhập Email.
* Hệ thống kiểm tra Email trong bảng `Staff_Accounts`. Nếu tồn tại, gửi một liên kết (hoặc mã OTP) khôi phục mật khẩu có thời hạn qua Email.
* Cho phép người dùng đặt lại mật khẩu mới, hệ thống tự động mã hóa Bcrypt và lưu vào DB.

**BS_QĐ 2 — Quy định Tìm kiếm và Xem chi tiết ca bệnh**

| STT | Thao tác | Thông tin hiển thị | Quy định ràng buộc |
|:---:|:---|:---|:---|
| 1 | Tìm kiếm ca bệnh | Tên BN, SĐT, Chuyên khoa, Thời gian kết thúc. | Tìm kiếm thông qua thanh tìm kiếm hoặc nhập mã phiên. |
| 2 | Click vào ca cụ thể | Chuyển sang màn hình DOC-03. | Truy vấn đầy đủ 4 bảng DB song song. |

---

### TẦNG 2: NGHIỆP VỤ QUẢN TRỊ TRI THỨC (MEDICAL ADMIN)

#### 1. Bảng yêu cầu chức năng nghiệp vụ

| Mã ID | Tên chức năng (Feature) | Thao tác của Chuyên gia Y tế trên UI (User Actions) | Xử lý ngầm của Hệ thống (Backend & Database) |
|:---|:---|:---|:---|
| **KMA-01** | **Quản lý danh mục Chuyên khoa** | Truy cập menu "Chuyên khoa". Xem danh sách. Nhấn [Thêm mới] hoặc [Sửa] để cập nhật: Mã khoa, Tên khoa, Mô tả. Nhấn [Lưu]. | Thực hiện CRUD trên bảng `Specialties`. • **Validate:** Mã `code` phải là duy nhất (Unique constraint). • Trả về HTTP 201 (Created) khi thêm mới thành công để UI tự động render lại danh sách. |
| **KMA-02** | **Quản lý Triệu chứng & Từ đồng nghĩa** | Nhấn [Thêm Triệu chứng]. Nhập Tên chuẩn y khoa, Câu hỏi xác nhận cho AI (VD: "Bạn có kèm theo ho không?"). • Thêm các từ khóa địa phương vào mục "Từ đồng nghĩa". | 1. `INSERT/UPDATE` bảng `Symptoms`. 2. **Trigger NLP:** Tự động gọi API Embedding model (`BAAI/bge-m3`) biến Tên triệu chứng thành `vector(1024)` lưu vào cột `embedding`. 3. `INSERT` mảng từ khóa vào bảng phụ `Symptom_Synonyms`. (Bọc trong 1 Transaction SQL). |
| **KMA-03** | **Quản lý danh mục Bệnh lý** | Truy cập "Bệnh lý". Nhấn [Thêm mới]. Nhập Tên bệnh, Mã ICD chuẩn, Mô tả. • Mở Dropdown chọn Chuyên khoa điều trị tương ứng. Nhấn [Lưu]. | Thực hiện CRUD bảng `Diseases`. • **Ràng buộc:** Bắt buộc có `specialty_id` hợp lệ làm khóa ngoại (Foreign Key). • **Trigger NLP:** Tự động mã hóa văn bản mô tả thành mảng `vector(1024)` lưu vào Database để phục vụ RAG. |
| **KMA-04** | **Thiết lập Cây Tri thức (Rules Engine)** | Chọn 1 Bệnh lý đích (VD: Sốt xuất huyết). Giao diện mở ra bảng điều khiển: • Thêm các Triệu chứng điều kiện. • Kéo thanh trượt để set Trọng số (Weight). • Checkbox chọn: "Bắt buộc phải có" hoặc "Triệu chứng loại trừ". | Xử lý mảng payload cực kỳ quan trọng: • `INSERT/UPDATE` vào bảng `Knowledge_Rules`. • Ánh xạ chính xác các trường: `disease_id`, `symptom_id`, `weight` (Float), cờ `is_mandatory` (Boolean), và cờ `is_exclusion` (Boolean). |
| **KMA-05** | **Sandbox Kiểm thử AI nội bộ** | Truy cập màn hình "Giả lập Chat". Đóng vai bệnh nhân nhập text để test thử xem bộ Luật chẩn đoán vừa thiết lập ở KMA-04 có tính toán ra đúng chuyên khoa mong muốn hay không. | Khởi tạo một phiên Chat ảo (Mock Session). • Chạy luồng bóc tách NER và Động cơ suy diễn (Inference Engine) để trả kết quả ra màn hình. • **Ràng buộc:** Tuyệt đối không lưu lịch sử đoạn chat này vào bảng `Chat_Sessions` để tránh làm bẩn dữ liệu khám thật. |

#### 2. Bảng Quy định liên quan — Quản trị Tri thức

**KMA_QĐ 1 — Quy định Quản lý Chuyên khoa**

| STT | Thao tác | Thông tin được tác động | Quy định ràng buộc |
|:---:|:---|:---|:---|
| 1 | Thêm | Mã khoa, Tên khoa, Mô tả | Mã khoa (`code`) không được trùng lặp (`UNIQUE`). |
| 2 | Sửa | Tên khoa, Mô tả | Không được sửa mã khoa. |
| 3 | Xóa | Trạng thái hoạt động | Chỉ được xóa khi chưa có bệnh lý nào thuộc khoa đó. Ngược lại chỉ được ẩn. |

**KMA_QĐ 2 — Quy định Quản lý Triệu chứng**

| STT | Tên thông tin | Định dạng nhập | Bắt buộc | Ràng buộc / Ghi chú |
|:---:|:---|:---:|:---:|:---|
| 1 | Mã triệu chứng (code) | Văn bản (30 ký tự) | **Có** | Duy nhất, không trùng lặp. |
| 2 | Tên chuẩn y khoa (name) | Văn bản (150 ký tự) | **Có** | Tên chính thức dùng trong suy diễn. |
| 3 | Câu hỏi xác nhận (question_text) | Văn bản (200 ký tự) | Không | Câu hỏi AI sẽ đặt khi cần xác nhận triệu chứng này. |
| 4 | Mảng từ đồng nghĩa | Danh sách văn bản | Không | Lưu vào bảng `Symptom_Synonyms` để hỗ trợ NER nhận diện ngôn ngữ địa phương. |

**KMA_QĐ 3 — Quy định Thiết lập Rules Engine**

| STT | Thao tác | Thông tin được tác động | Quy định ràng buộc |
|:---:|:---|:---|:---|
| 1 | Thêm luật | Bệnh, Triệu chứng, Weight, Bắt buộc, Loại trừ | `INSERT` vào bảng `Knowledge_Rules`. Trường `weight` kiểu Float (0.0 – 10.0). |
| 2 | Sửa luật | Weight, is_mandatory, is_exclusion | `UPDATE` bảng `Knowledge_Rules`. |
| 3 | Xóa luật | Bản ghi luật | `DELETE` vật lý khỏi `Knowledge_Rules`. |

#### 3. Biểu mẫu tiêu biểu (Bác sĩ)

**BS_BM 1: PHIẾU TÓM TẮT SÀNG LỌC AI (DÀNH CHO BÁC SĨ)**

```
════════════════════════════════════════════════════
          PHIẾU TÓM TẮT SÀNG LỌC – MÃ PHIÊN: #10492
════════════════════════════════════════════════════

THÔNG TIN BỆNH NHÂN:
  Họ tên:          Nguyễn Văn A
  SĐT:             090xxxxxxx
  Giới tính:       Nam
  Dị ứng:          Penicillin
  Bệnh nền:        Không có

KẾT QUẢ AI:
  Chuyên khoa gợi ý:  Hô hấp
  Bệnh nghi ngờ:      1. Viêm phổi cấp (8.5 điểm)
                       2. Hen suyễn (6.2 điểm)

XÁC NHẬN CỦA CHUYÊN GIA:
  [ ] AI chẩn đoán Đúng chuyên khoa
  [ ] AI chẩn đoán Sai → Bệnh thực tế: _______________

════════════════════════════════════════════════════
```

---

## C. BỘ PHẬN: QUẢN TRỊ HỆ THỐNG (ADMIN / IT) | Mã số: QTHT

### 1. Mục tiêu
Cung cấp các công cụ quản lý hệ thống, kiểm soát tài khoản nội bộ, nạp và bảo trì kho dữ liệu RAG (Retrieval-Augmented Generation), theo dõi hiệu suất của mô hình trí tuệ nhân tạo.

### 2. Bảng danh sách các chức năng (Nghiệp vụ)

| STT | Tên chức năng | Loại | Mã số | Ghi chú |
|:---:|:---|:---:|:---:|:---|
| **I. Quản lý tài khoản** | | | | |
| 1 | Đăng nhập phân hệ quản trị | Tra cứu | AD_QĐ 1 | Truy cập trang quản trị. |
| 2 | Quên mật khẩu / Đổi mật khẩu | Lưu trữ | AD_QĐ 1 | Khôi phục và đảm bảo an toàn tài khoản. |
| 3 | Tự động khởi tạo Admin | Hệ thống | AD_QĐ 1 | Khởi tạo tài khoản Admin đầu tiên khi hệ thống chạy lần đầu. |
| **II. Quản lý nhân sự nội bộ** | | | | |
| 4 | Xem danh sách tài khoản nội bộ | Tra cứu | AD_QĐ 2 | Theo dõi Bác sĩ, Lễ tân, Quản trị tri thức. Lọc theo Role và trạng thái. |
| 5 | Tạo mới tài khoản nội bộ | Lưu trữ | AD_QĐ 2 | Phân quyền cho nhân viên mới. |
| 6 | Khóa / Mở khóa tài khoản | Lưu trữ | AD_QĐ 2 | Khóa tài khoản nhân viên nghỉ việc hoặc vi phạm. |
| **III. Quản lý dữ liệu RAG** | | | | |
| 7 | Xem danh sách dữ liệu tri thức | Tra cứu | AD_QĐ 3 | Tra cứu kho tài liệu y khoa đã nạp. Lọc theo phân loại nguồn. |
| 8 | Nạp dữ liệu tri thức mới (RAG Ingestion) | Lưu trữ | AD_QĐ 3 | Textarea nhập nội dung → Loading bar. |
| 9 | Cập nhật / Xóa dữ liệu RAG | Lưu trữ | AD_QĐ 3 | Sửa chữ hoặc xóa vĩnh viễn khỏi bộ não AI. |
| **IV. Hệ thống** | | | | |
| 10 | Bảng điều khiển (Dashboard) | Tra cứu | AD_QĐ 4 | Xem biểu đồ thống kê tổng hợp. |
| 11 | Theo dõi Log & Gỡ lỗi AI (Debug) | Tra cứu | AD_QĐ 5 | Đọc JSON raw từ LLM của ca bị phàn nàn. |
| 12 | Cấu hình tham số hệ thống AI | Lưu trữ | AD_QĐ 6 | Chỉnh ngưỡng Confidence, Timeout. |

### 3. Bảng yêu cầu chức năng nghiệp vụ chi tiết

| Mã ID | Tên chức năng (Feature) | Thao tác của Quản trị viên trên UI (Admin Actions) | Xử lý ngầm của Hệ thống (Backend & Database) |
|:---:|:---|:---|:---|
| **SA-01** | **Đăng nhập phân hệ quản trị** | Truy cập cổng Portal nội bộ. Nhập Email/Password. Nhận thông báo lỗi nếu tài khoản không đủ thẩm quyền. | Xác thực thông tin. • **Ràng buộc:** Kiểm tra `role` (chỉ `admin` mới được cấp quyền quản trị toàn bộ). |
| **SA-01b**| **Quên mật khẩu quản trị** | Nhấn "Quên mật khẩu", cung cấp Email bảo mật của Admin. | Xác thực Email cấp cao. Gửi link reset mật khẩu qua Email. Hỗ trợ khôi phục qua lệnh CLI nếu hệ thống mất SMTP. |
| **SA-02** | **Quản lý danh sách tài khoản nội bộ** | Truy cập menu "Nhân sự". Xem danh sách các Bác sĩ, Lễ tân, Quản trị tri thức. Lọc theo trạng thái Hoạt động/Đã khóa. | `SELECT` danh sách từ bảng `Staff_Accounts`. • Hỗ trợ bộ lọc filter theo `role` và `is_active`. Phân trang dữ liệu hiển thị. |
| **SA-03** | **Tạo mới / Khóa tài khoản nội bộ** | Bấm nút [Tạo mới] để phân quyền cho nhân viên mới. Bấm gạt công tắc [Khóa] đối với nhân viên nghỉ việc hoặc vi phạm. | `INSERT` hoặc `UPDATE` trạng thái tài khoản thành `is_active = false`. • **Điều kiện cứng:** Bắn lỗi 403 (Forbidden) nếu Admin tự gửi Request khóa ID của chính mình. |
| **RAG-01** | **Xem danh sách dữ liệu tri thức (RAG)** | Truy cập menu "Kho tri thức AI". Xem danh sách các đoạn văn bản (Sách y khoa, bài báo) đã nạp. Lọc theo Phân loại nguồn. | `SELECT` từ bảng `Knowledge_Chunks`. • Trả về `id`, `source_type`, `source_id`, và trích xuất một phần `chunk_text`. • **Ràng buộc:** Phân trang bắt buộc bằng `LIMIT/OFFSET` (50 chunks/trang) để tránh quá tải RAM. |
| **RAG-02** | **Nạp dữ liệu tri thức mới (RAG Ingestion)** | Nhập nội dung kiến thức y khoa vào ô Textarea, chọn Loại nguồn gốc và bấm "Nạp cho AI". Chờ thanh tiến trình (Loading bar) chạy xong. | 1. Nhận chuỗi `chunk_text` từ Frontend. 2. Gọi API của Embedding Model (`BAAI/bge-m3`) để mã hóa văn bản thành mảng số thực. 3. `INSERT` dữ liệu vào bảng `Knowledge_Chunks` với trường `embedding` là mảng `vector(1024)`. |
| **RAG-03** | **Cập nhật / Xóa dữ liệu RAG** | Mở một đoạn tri thức bị lỗi thời để sửa lại chữ, hoặc bấm nút [Thùng rác] để xóa vĩnh viễn khỏi bộ não AI. | • **Khi Cập nhật:** Bắt buộc gọi lại API Embedding Model để sinh Vector mới, sau đó `UPDATE` cả `chunk_text` và `embedding` để đảm bảo đồng bộ. • **Khi Xóa:** Thực hiện lệnh `DELETE` vật lý hoặc gán cờ `is_deleted = true`. |
| **SYS-01** | **Xem Bảng điều khiển (System Dashboard)** | Mở màn hình Tổng quan. Chọn mốc thời gian (Tuần/Tháng). Xem biểu đồ: Tổng số phiên chat, Top Chuyên khoa được gợi ý. | Chạy các hàm Aggregation SQL: • `COUNT(id)` từ `Chat_Sessions` theo `created_at`. • `GROUP BY suggested_specialty_id` kết hợp phép `JOIN` với bảng `Specialties` để vẽ biểu đồ cột (Bar chart). |
| **SYS-02** | **Theo dõi Log & Gỡ lỗi (Debug AI)** | Truy cập menu "AI Debug". Click vào một phiên chat bị phàn nàn là chẩn đoán sai. Đọc đoạn text gốc của user và file JSON kỹ thuật mà LLM nhả về. | `SELECT` từ bảng `Message_Logs`. • Frontend parsing trường `metadata` (lưu dưới kiểu `jsonb`) để bung ra các dữ liệu thô (Raw LLM output, trích xuất NER bị sai lệch). Phục vụ IT báo cáo tinh chỉnh `Symptom_Synonyms`. |
| **SYS-03** | **Cấu hình tham số hệ thống AI** | Mở bảng Cài đặt. Điều chỉnh các thanh trượt: Ngưỡng độ tin cậy bóc tách (Confidence Threshold, VD: 0.78), Số câu hỏi xác nhận tối đa (VD: 6), Thời gian timeout phiên chat. Bấm Lưu. | Nhận payload cấu hình. `UPDATE` vào bảng `System_Configs`. • Restart ngầm các worker/service liên quan để áp dụng cấu hình mới cho hệ thống. |

### 4. Bảng Quy định / Công thức liên quan — Quản trị viên

**AD_QĐ 1 — Quy định Tài khoản Quản trị**
* **Tự động khởi tạo (Auto-initialization):** Khi hệ thống khởi chạy lần đầu tiên, một tài khoản Admin mặc định sẽ được tự động sinh ra để thực hiện các thiết lập ban đầu.
* **Bảo mật:** Mật khẩu được mã hóa bằng Bcrypt, lưu trong cột `password_hash` của bảng `Staff_Accounts`.

**AD_QĐ 2 — Quy định Quản lý Tài khoản Nội bộ**

| STT | Tên thông tin | Định dạng nhập | Bắt buộc | Ràng buộc / Ghi chú |
|:---:|:---|:---:|:---:|:---|
| 1 | Username | Văn bản (50 ký tự) | **Có** | Duy nhất (`UNIQUE`). Dùng để đăng nhập. |
| 2 | Email | Văn bản (100 ký tự) | Không | Duy nhất nếu có. |
| 3 | Họ và tên | Văn bản (100 ký tự) | **Có** | Tên hiển thị. |
| 4 | Mật khẩu | Văn bản | **Có** | Hệ thống hash Bcrypt trước khi lưu. |
| 5 | Vai trò (Role) | Danh sách chọn | **Có** | Giá trị: `admin`, `doctor`, `receptionist`, `knowledge_admin`. |
| 6 | Chuyên khoa | Danh sách chọn | Không | Bắt buộc nếu Role = `doctor`. Liên kết FK tới `Specialties`. |

Bảng quy định thao tác Quản lý tài khoản:

| STT | Thao tác | Thông tin được tác động | Quy định ràng buộc |
|:---:|:---|:---|:---|
| 1 | Tạo mới | Toàn bộ các trường | Username không được trùng lặp. |
| 2 | Sửa | Họ tên, Email, Role, Chuyên khoa | Không được sửa Username. |
| 3 | Khóa | `is_active` → `false` | Admin không được tự khóa chính mình (HTTP 403). |
| 4 | Mở khóa | `is_active` → `true` | Cần quyền Admin. |

**AD_QĐ 3 — Quy định Quản lý dữ liệu RAG**

| STT | Tên thông tin | Định dạng nhập | Bắt buộc | Ràng buộc / Ghi chú |
|:---:|:---|:---:|:---:|:---|
| 1 | Nội dung văn bản (chunk_text) | Textarea | **Có** | Đoạn văn bản y khoa sẽ được mã hóa thành vector. |
| 2 | Phân loại nguồn (source_type) | Danh sách chọn | **Có** | VD: `textbook`, `journal`, `guideline`. |
| 3 | Mã tham chiếu (source_id) | Số nguyên | Không | Liên kết tới ID bệnh/triệu chứng nếu có. |

Quy tắc xử lý:
* **Khi thêm mới:** Gọi API `SentenceTransformer.encode()` sinh ra mảng `vector(1024)`. Thao tác INSERT bảng `Knowledge_Chunks` với cả `chunk_text` và `embedding`.
* **Khi cập nhật:** Bắt buộc phải gọi lại API sinh Vector mới rồi mới `UPDATE` — đảm bảo embedding luôn đồng bộ với nội dung text.
* **Khi xóa:** `DELETE` vật lý. Dữ liệu cũ bị loại khỏi kho tri thức AI ngay lập tức.

**AD_QĐ 4 — Quy định Bảng điều khiển Dashboard**
* **Báo cáo phiên chat:** Tổng số phiên, số phiên hoàn thành.
* **Báo cáo chuyên khoa:** Biểu đồ cột (Bar chart) phân bố lượt gợi ý chuyên khoa theo `suggested_specialty_id`.
* **Báo cáo hiệu suất AI:** Thống kê tỷ lệ `is_doctor_verified = true/false` để đánh giá độ chính xác của AI.

**AD_QĐ 5 — Quy định Debug AI**
* **Bước 1 — Chọn phiên:** Hiển thị danh sách phiên chat bị đánh giá sai (`is_doctor_verified = false`).
* **Bước 2 — Phân tích:** Màn hình hiển thị song song: *Tin nhắn gốc bệnh nhân* — *Triệu chứng AI trích xuất* — *Kết quả suy diễn*.
* **Bước 3 — Hành động:** IT tinh chỉnh `Symptom_Synonyms` (thêm từ đồng nghĩa bị thiếu) hoặc điều chỉnh `weight` trong `Knowledge_Rules`.

### 5. Biểu mẫu tiêu biểu (Quản trị viên)

**AD_BM 1: CẤU TRÚC JSON OUTPUT CỦA LLM (KHI DEBUG)**

```json
{
  "session_id": 10492,
  "patient_input": "em bị đau đầu dữ lắm, hơi buồn nôn và chóng mặt",
  "ner_extraction": [
    {"symptom_id": 12, "symptom_code": "SYM012", "symptom_name": "Đau đầu", "confidence": 0.95, "matched_synonym": "đau đầu dữ lắm"},
    {"symptom_id": 8, "symptom_code": "SYM008", "symptom_name": "Buồn nôn", "confidence": 0.88, "matched_synonym": "buồn nôn"},
    {"symptom_id": 15, "symptom_code": "SYM015", "symptom_name": "Chóng mặt", "confidence": 0.82, "matched_synonym": "chóng mặt"}
  ],
  "inference_results": [
    {"disease_id": 5, "disease_name": "Rối loạn tiền đình", "score": 8.5, "matched_symptoms": 3, "missing_mandatory": false},
    {"disease_id": 12, "disease_name": "Viêm xoang", "score": 5.2, "matched_symptoms": 2, "exclusion_hit": null},
    {"disease_id": 3, "disease_name": "Thiếu máu", "score": 4.0, "matched_symptoms": 2, "exclusion_hit": "SYM045"}
  ],
  "suggested_specialty": "Thần kinh"
}
```

**AD_BM 2: BÁO CÁO HIỆU SUẤT AI**

| STT | Mã bệnh (ICD) | Tên bệnh | Số lượt AI đề xuất | Số lượt Bác sĩ xác nhận Đúng | Số lượt AI đoán Sai | Tỷ lệ chính xác |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| 1 | J03 | Viêm amidan cấp | 45 | 42 | 3 | 93.3% |
| 2 | A91 | Sốt xuất huyết Dengue | 28 | 25 | 3 | 89.3% |
| 3 | J18 | Viêm phổi cấp | 15 | 14 | 1 | 93.3% |

Ngày lập báo cáo: ............     Người lập: ............

---

## 5. Xác định yêu cầu chức năng hệ thống & Yêu cầu chất lượng

### 5.1. Bảng yêu cầu chức năng hệ thống

| STT | Nội dung | Mô tả chi tiết | Ghi chú |
|:---:|:---|:---|:---|
| 1 | Nhận diện thực thể (NER) | Sử dụng Sentence Embedding (`BAAI/bge-m3`) kết hợp cosine similarity để trích xuất triệu chứng từ ngôn ngữ tự nhiên. | Ngưỡng mặc định: 0.78. |
| 2 | Hệ chuyên gia (Rule-based) | Động cơ suy diễn tính điểm trọng số, kiểm tra luật bắt buộc (`is_mandatory`) và luật loại trừ (`is_exclusion`). | Bảng `Knowledge_Rules`. |
| 3 | RAG (Truy xuất Tăng cường) | Tìm kiếm đoạn văn bản y khoa liên quan nhất bằng Vector search trên bảng `Knowledge_Chunks`. | pgvector extension. |
| 4 | Bảo mật dữ liệu | Mật khẩu tất cả các loại tài khoản đều được mã hóa bằng **Bcrypt**. API giao tiếp chuẩn CORS. | Tuân thủ quyền riêng tư. |
| 5 | Hỗ trợ chế độ Khách | Bệnh nhân có thể sử dụng Chatbot mà không cần đăng nhập (Guest mode). | Tự tạo `Patients` tạm. |

### 5.2. Bảng yêu cầu về chất lượng hệ thống

| STT | Nội dung | Tiêu chuẩn | Mô tả chi tiết | Ghi chú |
|:---:|:---|:---:|:---|:---|
| 1 | Tốc độ xử lý AI | Hiệu quả | Thời gian bóc tách NER và trả về phản hồi trong vòng **3–5 giây** kể từ lúc bệnh nhân bấm gửi. Phân trang RAG chunking để tránh quá tải RAM. | Đòi hỏi API Embedding nhanh. |
| 2 | Tính bảo mật | An toàn | Toàn bộ password lưu dạng Bcrypt hash. Session management phía server. Hệ thống chỉ hiển thị thông báo lỗi thân thiện cho người dùng, không bao giờ lộ chi tiết lỗi kỹ thuật (SQL error, traceback). | Tuân thủ quyền riêng tư y tế. |
| 3 | Tính tiện dụng | Tiện dụng | Giao diện tối ưu cho cả máy tính và thiết bị di động (Responsive). Thông báo rõ ràng bằng tiếng Việt. Nút phản hồi nhanh [Có/Không/Không rõ] giúp bệnh nhân trả lời dễ dàng. | |
| 4 | Độ tương thích | Tương thích | UI Chatbot hiển thị dạng Widget nhúng trên web, hoạt động ổn định trên các trình duyệt phổ biến (Chrome, Safari, Firefox). | Giao diện không che khuất màn hình. |
| 5 | Khả năng mở rộng | Tiến hóa | Database sử dụng PostgreSQL + `pgvector`, tối ưu chỉ mục vector (IVFFlat hoặc HNSW) để truy vấn siêu tốc. Có thể thay thế/nâng cấp mô hình nhúng mà không ảnh hưởng cấu trúc dữ liệu. | Sẵn sàng mở rộng lên hàng triệu vector. |
| 6 | Tính minh bạch | Traceability | Mọi suy luận của AI đều được truy vết qua bảng `Session_Disease_Scores`, `Session_Symptoms` và `Message_Logs` (kèm `metadata` kiểu jsonb). Bác sĩ có thể đánh giá lại kết quả AI (Feedback Loop). | Tránh hiện tượng "hộp đen" AI. |

---

## 6. Xác định phạm vi dự án

**Phạm vi trong (In-scope):**

* Khảo sát hiện trạng quy trình tư vấn y tế ban đầu tại phòng khám.
* Xây dựng mô hình yêu cầu chức năng (functional requirements) cho hệ thống Chatbot.
* Tập trung hoàn toàn vào **Khai phá dữ liệu văn bản (NLP)** và **Hệ chuyên gia (Expert System)**.
* Thiết kế Cây tri thức Y khoa (Ontology), quy tắc suy diễn (Inference Rules), trọng số triệu chứng (`weight`), luật bắt buộc (`is_mandatory`) và luật loại trừ (`is_exclusion`).
* Hỗ trợ đầy đủ 3 nhóm người dùng: Bệnh nhân (Người dùng cuối), Bác sĩ/Quản trị Y khoa, và Quản trị Hệ thống (Admin/IT).
* Các nghiệp vụ chính: Tra cứu (Retrieval), Lưu trữ (Storage), Tính toán & Logic (Processing & Reasoning), Kết xuất (Output/Reporting).

**Phạm vi ngoài (Out-of-scope):**

* Triển khai thực tế lên server và tích hợp với hệ thống bệnh án điện tử hiện có của phòng khám.
* Thiết kế giao diện UI/UX chi tiết (chỉ tập trung vào yêu cầu chức năng).
* Kiểm thử đầy đủ, bảo trì và vận hành sau khi triển khai.
* Xử lý thanh toán, lịch hẹn khám, hoặc bất kỳ tính năng nào không liên quan trực tiếp đến sàng lọc triệu chứng và gợi ý chuyên khoa.
