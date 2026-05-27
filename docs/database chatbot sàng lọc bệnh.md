# Chatbot sàng lọc triệu chứng bệnh: Tích hợp hệ chuyên gia vào website phòng khám để hỏi bệnh nhân về các triệu chứng và gợi ý chuyên khoa cần khám.

## 1\. Khảo sát hiện trạng quy trình phân luồng chuyên khoa

### **1.1. Mục tiêu khảo sát** Tìm hiểu chi tiết cách thức phòng khám hiện tại đang tiếp nhận bệnh nhân và phân luồng chuyên khoa thủ công (qua lễ tân hoặc y tá trực). Từ đó, xác định các "điểm nghẽn" trong quá trình giao tiếp để chuyển đổi sang mô hình Chatbot tự động, giúp tối ưu hóa thời gian chờ đợi và tăng độ chính xác khi chỉ định chuyên khoa lâm sàng.

### **1.2. Các hình thức thực hiện khảo sát** Để thu thập dữ liệu đa chiều, dự án sử dụng kết hợp các phương pháp sau:

* ### **Quan sát thực tế (Observation):** \* Theo dõi trực tiếp quá trình bệnh nhân mô tả triệu chứng bằng ngôn ngữ đời thường cho nhân viên phân luồng tại quầy tiếp đón.

  * ### Ghi nhận cách thức nhân viên y tế đặt các "câu hỏi đóng" (Có/Không) để xác nhận hoặc loại trừ các chuyên khoa không liên quan.

* ### **Phỏng vấn chuyên sâu (Interviews):**

  * ### *Đối với Bác sĩ/Chuyên gia Y tế:* Khai thác tư duy chẩn đoán (Diagnostic Logic). Ví dụ: Đặt câu hỏi *"Khi bệnh nhân kêu đau đầu, bác sĩ sẽ hỏi thêm những triệu chứng đi kèm nào để phân biệt giữa chuyên khoa Thần kinh và chuyên khoa Tai Mũi Họng?"*.

  * ### *Đối với Bệnh nhân:* Tìm hiểu những khó khăn khi tự đánh giá bệnh trạng, nguyên nhân dẫn đến việc đi khám sai chuyên khoa và thói quen sử dụng từ ngữ mô tả bệnh (phục vụ cho việc nhận diện thực thể \- NER sau này).

### **1.3. Thu thập thông tin và tài liệu (Data Collection)** Quá trình số hóa Hệ chuyên gia đòi hỏi các nguồn tài liệu đầu vào có tính chính xác cao. Các tài liệu được thu thập bao gồm:

* ### **Tài liệu hành chính:**

  * ### Danh mục các chuyên khoa hiện có của phòng khám (Mục tiêu: Làm dữ liệu đích \- Target Output cho thuật toán gợi ý).

  * ### Các biểu mẫu khai báo y tế cơ bản (tiền sử bệnh lý, dị ứng, nhóm máu) để xây dựng bộ hồ sơ người dùng tiêu chuẩn.

* ### **Tài liệu chuyên môn Y khoa:**

  * ### Sổ tay hướng dẫn phân loại bệnh lý, giáo trình y khoa (Ví dụ: Giáo trình bệnh truyền nhiễm, nội khoa).

  * ### *Mục đích:* Dùng làm cơ sở tri thức (Knowledge Base) để lập trình các tập luật (Rules) – định nghĩa trọng số giữa các Triệu chứng (Symptoms) và Bệnh lý (Diseases) cho Động cơ suy diễn (Inference Engine) của phần mềm.

## 2\. Quy trình thực hiện khảo sát và phân tích

### **2.1. Tìm hiểu tổng quan về thế giới thực** Hệ thống Chatbot đóng vai trò như một "Y tá phân luồng kỹ thuật số" (Digital Triage Nurse), hoạt động 24/7 để hỗ trợ tư vấn y tế ban đầu. Mục tiêu cốt lõi là giải quyết tình trạng bệnh nhân không có chuyên môn y tế, mô tả triệu chứng mơ hồ dẫn đến đi khám sai chuyên khoa, đồng thời giảm tải áp lực khai thác bệnh sử thủ công (hỏi đáp lặp đi lặp lại) cho đội ngũ y tế tại quầy tiếp đón.

### **2.2. Tìm hiểu hiện trạng tổ chức (Xác định các tác nhân tham gia)** Cơ cấu vận hành của hệ thống phần mềm xoay quanh 3 nhóm đối tượng chính với vai trò tách biệt:

* ### **Đối ngoại (Bệnh nhân / Người dùng cuối): Quyền hạn:** Là người trực tiếp tương tác với Chatbot bằng văn bản (ngôn ngữ tự nhiên) để khai báo bệnh trạng và nhận tư vấn định hướng chuyên khoa. **Trách nhiệm:** cung cấp thông tin chính xác để hệ thống phân luồng.

* ### **Đối nội (Bác sĩ / Nhân viên y tế): Quyền hạn:** Được hệ thống tự động phân quyền truy cập, hiển thị và tra cứu "Phiếu tóm tắt triệu chứng" cùng lịch sử phiên chat của những bệnh nhân được điều hướng về khoa mình. **Trách nhiệm:** Kiểm tra đối chiều thông tin sàng lọc của AI để làm cơ sở lâm sàng nhanh, đảm bảo tính chính xác trược khi tiếp nhận bệnh nhân vào khám thưc tế. 

* ### **Đối nội (Quản trị viên / Kỹ sư tri thức y khoa): Quyền hạn:** Được quyền  nạp dữ liệu y khoa, cấu hình trọng số và tinh chỉnh các tập luật (Rules) cho Hệ chuyên gia. **Trách nhiệm:**  Đảm bảo tính chính xác, an toàn của cơ sở tri thức y tế.

### **2.3. Tìm hiểu hiện trạng nghiệp vụ (Phân loại công việc trên máy tính)** Toàn bộ quy trình hoạt động của hệ thống được bóc tách và phân thành 4 nhóm nghiệp vụ đặc thù của một Hệ chuyên gia:

* ### **Nghiệp vụ Tra cứu (Retrieval):** \* Hệ thống tự động tra cứu danh mục "Từ đồng nghĩa" (`Symptom_Synonyms`) để ánh xạ ngôn ngữ đời thường của bệnh nhân sang từ vựng y khoa chuẩn.

  * ### Bác sĩ tra cứu lại nguyên văn lịch sử trò chuyện (`Message_Logs`) của bệnh nhân khi cần đối chiếu.

* ### **Nghiệp vụ Lưu trữ (Storage):** \* Ghi nhận và số hóa các triệu chứng mà mô hình NLP đã bóc tách được (`Session_Symptoms`) kèm theo độ tin cậy.

  * ### Lưu vết quá trình tư duy và chấm điểm của AI (`Session_Disease_Scores`) để phục vụ công tác kiểm toán y khoa.

* ### **Nghiệp vụ Tính toán & Logic (Processing & Reasoning):** Đây là nghiệp vụ cốt lõi nhất. Động cơ suy diễn (Inference Engine) thực hiện tính toán tổng điểm trọng số (`weight`) của các triệu chứng, đồng thời quét qua các bộ luật bắt buộc (`is_mandatory`) và luật loại trừ (`is_exclusion`) để triệt tiêu các bệnh lý không phù hợp.

* ### **Nghiệp vụ Tổng hợp, Thống kê (Output/Reporting):** \* Hiển thị kết luận cuối cùng trên màn hình Chatbot để định hướng người bệnh đến đúng chuyên khoa.

  * ### Tự động sinh ra "Phiếu tóm tắt sàng lọc" đính kèm vào hồ sơ bệnh án điện tử để chuyển lên phòng khám chuyên khoa tương ứng.

  * ### Hệ thống tổng hợp lưu lượng bệnh nhân được phân luồng về các chuyên khoa theo ngày/tháng để phục vụ công tác thống kê, báo cáo tình hình quá tải tại phòng khám.

## 3\. Lập danh sách các yêu cầu

### Dựa trên kết quả khảo sát hiện trạng, tiến hành xác định các chức năng hệ thống sẽ thực hiện trên máy tính. Vì phạm vi dự án tập trung hoàn toàn vào Khai phá dữ liệu văn bản (NLP) và Hệ chuyên gia (Expert System), các yêu cầu chức năng nghiệp vụ được phân chia theo 3 bộ phận người dùng cốt lõi như sau:

**BẢNG YÊU CẦU CHỨC NĂNG NGHIỆP VỤ TỔNG QUAN (MASTER EPIC LIST)**

| Mã Phân hệ  | Tên Phân hệ (Module)  | Mã Epic  | Tên Nghiệp vụ Tổng quan (Epic)  | Khối Giá trị mang lại (Value Proposition)  |
| :---: | :---- | :---: | :---- | :---- |
| MOD-01  | Hệ tri thức Y khoa (Medical Knowledge Base)  | EP-01  | Quản trị Cây tri thức Y khoa (Ontology Management)  | Số hóa và cấu trúc hóa toàn bộ danh mục bệnh lý, triệu chứng lâm sàng thành một hệ sinh thái dữ liệu chuẩn mực, làm nền tảng cốt lõi cho AI học tập và suy diễn.  |
|  |  | EP-02  | Cấu hình Động cơ Suy diễn (Inference Engine Setup)  | Trao quyền cho chuyên gia y tế thiết lập hệ thống luật (Rules), ma trận trọng số và các cờ cảnh báo rủi ro, đảm bảo mọi quyết định của AI đều minh bạch và tuân thủ chuẩn y khoa.  |
| MOD-02  | Tương tác Sàng lọc (Triage Chatbot Engine)  | EP-03  | Khai thác Triệu chứng Tự nhiên (Natural Symptom Extraction)  | Ứng dụng NLP để tự động nhận diện, bóc tách và phân loại các dấu hiệu bất thường từ ngôn ngữ giao tiếp tự do của bệnh nhân theo thời gian thực.  |
|  |  | EP-04  | Đánh giá Rủi ro & Gợi ý Lâm sàng (Clinical Routing)  | Tự động đối chiếu dữ kiện với hệ tri thức để tính toán điểm số bệnh lý, từ đó phát cảnh báo cấp cứu (nếu có) hoặc định tuyến bệnh nhân đến đúng chuyên khoa cần khám.  |
|  |  | EP-05  | Kết xuất Báo cáo Hỗ trợ Quyết định (Decision Support Reporting)  | Đóng gói toàn bộ lịch sử hội thoại và kết quả suy diễn thành "Phiếu tóm tắt sàng lọc", giúp bác sĩ tiết kiệm thời gian khai thác bệnh sử và tăng độ chính xác khi thăm khám.  |
| MOD-03  | Quản lý Định danh (Identity Management)  | EP-06  | Quản lý Truy cập & Phân quyền (Access Control)  | Quản lý vòng đời tài khoản của đa dạng người dùng (Admin, Bác sĩ, Bệnh nhân) và hỗ trợ chế độ Khách (Guest) để tối ưu hóa phễu trải nghiệm mà không gây rào cản đăng nhập.  |
|  |  | EP-07  | Số hóa Tiền sử Y tế (Medical Profile Digitization)  | Thu thập và lưu trữ an toàn các chỉ số sinh tồn, tiền sử dị ứng, bệnh nền của bệnh nhân, biến chúng thành các tham số tĩnh để cá nhân hóa kết quả sàng lọc của AI.  |

### 

### 

### 

### 

### **Bảng 1: Dành cho đối tượng sử dụng dịch vụ (Người dùng cuối)**

**Bộ phận: Bệnh nhân | Mã số: BN**

**1\. Bảng yêu cầu chức năng nghiệp vụ**

| Mã ID | Tên chức năng (Feature) | Thao tác của Bệnh nhân trên UI (User Actions) | Xử lý ngầm của Hệ thống (Backend & Database) |
| :---- | :---- | :---- | :---- |
| **US-01** | **Đồng bộ đăng nhập (SSO)** | Bệnh nhân không cần đăng nhập lại. Truy cập trực tiếp vào module Chatbot thông qua nút "Tư vấn AI" trên website phòng khám. | Đọc JWT Token từ Request Header. Decode để lấy external\_patient\_id. • **Nếu có:** Truy xuất patient\_id để thiết lập phiên. • **Nếu chưa:** INSERT hồ sơ mới vào bảng Patients. |
| **US-02** | **Xem thông tin hồ sơ y tế** | Truy cập màn hình "Hồ sơ y tế". Xem danh sách các trường thông tin: Tên, Giới tính, Tuổi, Chiều cao, Cân nặng, Dị ứng, Bệnh nền. | Thực hiện phép JOIN bảng Patients và Medical\_Profiles. Trả về dữ liệu hiển thị. • **Ràng buộc UI:** Khóa cứng (Read-only) các trường thông tin hành chính (Tên, SĐT, Giới tính). |
| **US-03** | **Cập nhật Tiền sử bệnh lý** | Nhập text vào ô "Tiền sử dị ứng", "Bệnh nền" (có tùy chọn chọn "Không có"). Nhập số thực vào ô "Chiều cao", "Cân nặng". Bấm nút "Lưu". | Validate payload: Chiều cao, Cân nặng \> 0. • Thực hiện lệnh UPSERT vào bảng Medical\_Profiles. • Trả về HTTP 200 để Frontend hiển thị thông báo thành công. |
| **CB-01** | **Khởi tạo phiên tư vấn mới** | Bấm nút "Bắt đầu tư vấn". Chờ giao diện khung chat mở ra và nhận được tin nhắn chào mừng tự động từ AI. | INSERT 1 dòng vào Chat\_Sessions với status \= 'in\_progress'. • Sinh ra session\_id trả về cho Frontend quản lý state. • Kích hoạt API gửi câu chào mặc định. |
| **CB-02** | **Trò chuyện khai báo bệnh trạng** | Gõ văn bản mô tả triệu chứng tự do vào ô input và bấm phím Enter hoặc nút "Gửi". | 1\. INSERT text vào Message\_Logs (role: PATIENT). 2\. Đẩy text qua Model NER để bóc tách thực thể. 3\. INSERT danh sách ID triệu chứng vào Session\_Symptoms với is\_present \= true, confidence từ AI, và source \= 'user\_free\_text'. |
| **CB-03** | **Trả lời câu hỏi xác nhận AI** | Đọc câu hỏi truy vấn của AI (VD: "Bạn có bị đau đầu không?"). Bấm chọn các nút phản hồi nhanh: \[Có\], \[Không\], hoặc \[Không rõ\]. | 1\. Nhận payload từ nút bấm. 2\. INSERT vào Session\_Symptoms với is\_present tương ứng và source \= 'confirmation'. 3\. Kích hoạt Động cơ suy diễn (Inference Engine) tính lại tổng điểm. |
| **CB-04** | **Nhận kết quả sàng lọc** | Khung nhập liệu bị khóa. Đọc "Phiếu kết quả" hiện ra ở cuối đoạn chat bao gồm: Chuyên khoa gợi ý, Lời khuyên, và Cảnh báo đỏ (nếu có). | Khi điểm vượt ngưỡng tin cậy: 1\. INSERT điểm số vào Session\_Disease\_Scores. 2\. INSERT nội dung phiếu kết quả vào Session\_Recommendations. 3\. UPDATE cột suggested\_specialty\_id, triage\_urgency, và end\_time trong Chat\_Sessions. Bắn cờ disable UI ô chat. |
| **CB-05** | **Kết thúc phiên Chatbot** | Bấm nút \[X\] hoặc "Đóng Chatbot" ở góc màn hình. Giao diện Chatbot đóng lại, trở về giao diện website gốc. | UPDATE cột status trong Chat\_Sessions thành completed (nếu đã có kết quả) hoặc abandoned (nếu thoát ngang). • Xóa state nội bộ, tuyệt đối không gọi API logout của web mẹ. |
| **CB-06** | **Tra cứu danh sách tư vấn** | Click vào tab "Lịch sử tư vấn". Xem danh sách các thẻ tóm tắt (Mã phiên, Ngày giờ, Chuyên khoa gợi ý). | SELECT danh sách từ Chat\_Sessions dựa theo patient\_id. • **Ràng buộc Query:** Ép buộc dùng ORDER BY start\_time DESC. • Hỗ trợ phân trang bằng Limit/Offset (10 items/page). |
| **CB-07** | **Xem chi tiết phiên chat cũ** | Click vào 1 thẻ lịch sử cụ thể. Xem lại toàn bộ bong bóng chat cũ và Phiếu kết quả. Khung nhập liệu bị ẩn đi. | Truyền session\_id để SELECT toàn bộ record trong Message\_Logs và Session\_Recommendations. • Render UI ở trạng thái Read-only. Chặn mọi thao tác gửi tin nhắn mới. |

### **Bảng 2: Dành cho đối tượng Nhân viên y tế (Quản trị tri thức / Bác sĩ)**

**Bộ phận: Quản trị Y khoa & Bác sĩ | Mã số: BS**

**1\. Bảng yêu cầu chức năng nghiệp vụ**

**TẦNG 1: NGHIỆP VỤ LÂM SÀNG (BÁC SĨ TRỰC)**

| Mã ID | Tên chức năng (Feature) | Thao tác của Bác sĩ trên UI (User Actions) | Xử lý ngầm của Hệ thống (Backend & Database) |
| :---- | :---- | :---- | :---- |
| **DOC-01** | **Đăng nhập Portal Y tế** | **Nhập Email/Username và Mật khẩu tại trang Đăng nhập nội bộ. Nhấn "Đăng nhập".** | **Nhận payload, truy vấn bảng** Staff\_Accounts**. So khớp giải mã Bcrypt. • Xử lý Token: Khởi tạo JWT Token chứa** staff\_id**,** role**, và** specialty\_id **(Mã khoa trực). • Trả về HTTP 200\. Frontend lưu token vào HttpOnly Cookie để bảo mật.** |
| **DOC-02** | **Đăng xuất hệ thống** | **Nhấn avatar góc phải màn hình, chọn "Đăng xuất". Trở về màn hình đăng nhập.** | **Xóa Token ở phía Client. • Bảo mật: Đẩy** session\_token **hiện tại vào Blacklist (Redis) để vô hiệu hóa tức thì, chống tấn công Replay Attack.** |
| **DOC-03** | **Theo dõi Ca chờ khám (Triage Queue)** | **Mở màn hình "Danh sách chờ". Xem các bệnh nhân đã được AI định tuyến về khoa của mình. • UI Ràng buộc: Các ca có dấu hiệu nguy kịch sẽ được bôi nền đỏ, ghim lên đầu danh sách kèm icon Cảnh báo.** | SELECT **bảng** Chat\_Sessions JOIN Patients**. • Điều kiện lọc (Filter):** WHERE suggested\_specialty\_id \= \[ID khoa của bác sĩ\] **AND** status \= 'completed'**. • Thuật toán sắp xếp (Sort): Ưu tiên** triage\_urgency \= 'emergency' **lên đầu, sau đó mới** ORDER BY end\_time DESC**. Phân trang 20 records/page.** |
| **DOC-04** | **Xem chi tiết Báo cáo Sàng lọc** | **Click vào 1 ca bệnh cụ thể. Màn hình chia làm 2 phần tĩnh (Read-only): 1\. Bên trái: Thông tin cá nhân, Tiền sử dị ứng, Bệnh nền, Chỉ số sinh tồn. 2\. Bên phải: Phiếu tóm tắt gợi ý của AI và Lịch sử nguyên văn đoạn chat.** | **Lấy** session\_id **để query song song 4 luồng: 1\. Hồ sơ:** JOIN Patients **&** Medical\_Profiles**. 2\. Log chat: Truy xuất** Message\_Logs**. 3\. Kết quả chẩn đoán:** Session\_Disease\_Scores**. 4\. Phiếu tóm tắt:** Session\_Recommendations**.** |
| **DOC-05** | **Xác nhận / Đánh giá AI (Feedback Loop)** | **Cuộn xuống cuối Phiếu kết quả. Bác sĩ đối chiếu với kết quả khám thực tế, sau đó nhấn chọn: • \[AI chẩn đoán Đúng\] • \[AI chẩn đoán Sai\] $\\rightarrow$ Chọn lại bệnh lý thực tế từ danh sách Dropdown.** | **Đây là lõi thu thập dữ liệu huấn luyện (Data Pipeline): • Nhận payload đánh giá.** UPDATE **bảng** Session\_Disease\_Scores**. • Bổ sung cờ** is\_doctor\_verified \= true/false **và** actual\_disease\_id **(nếu AI sai). Dữ liệu này lưu trữ làm Fact để tái huấn luyện trọng số cho model AI sau này.** |
| **DOC-06** | **Kết xuất & In Phiếu bệnh án (Export PDF)** | **Nhấn icon máy in hoặc "Xuất PDF" góc phải màn hình để kẹp vào hồ sơ bệnh án giấy hoặc gửi qua hệ thống HIS của bệnh viện.** | **Backend render HTML template chứa dữ liệu** Medical\_Profiles **và** Session\_Recommendations**. • Sử dụng thư viện convert HTML to PDF (như Puppeteer) và trả file stream về cho trình duyệt tự động tải xuống.** |

### 

**TẦNG 2: NGHIỆP VỤ QUẢN TRỊ TRI THỨC (MEDICAL ADMIN)**

| Mã ID | Tên chức năng (Feature) | Thao tác của Chuyên gia Y tế trên UI (User Actions) | Xử lý ngầm của Hệ thống (Backend & Database) |
| :---- | :---- | :---- | :---- |
| **KMA-01** | **Quản lý danh mục Chuyên khoa** | Truy cập menu "Chuyên khoa". Xem danh sách. Nhấn \[Thêm mới\] hoặc \[Sửa\] để cập nhật: Mã khoa, Tên khoa, Mô tả. Nhấn \[Lưu\]. | Thực hiện CRUD trên bảng Specialties. • **Validate:** Mã code phải là duy nhất (Unique constraint). • Trả về HTTP 201 (Created) khi thêm mới thành công để UI tự động render lại danh sách. |
| **KMA-02** | **Quản lý Triệu chứng & Từ đồng nghĩa** | Nhấn \[Thêm Triệu chứng\]. Nhập Tên chuẩn y khoa, Câu hỏi xác nhận cho AI (VD: "Bạn có kèm theo ho không?"). • Bật/tắt công tắc is\_red\_flag (Dấu hiệu nguy kịch). • Thêm các từ khóa địa phương vào mục "Từ đồng nghĩa". | 1\. INSERT/UPDATE bảng Symptoms. 2\. **Trigger NLP:** Tự động gọi API Embedding model biến Tên triệu chứng thành vector(1024) lưu vào cột embedding. 3\. INSERT mảng từ khóa vào bảng phụ Symptom\_Synonyms. (Bọc trong 1 Transaction SQL). |
| **KMA-03** | **Quản lý danh mục Bệnh lý** | Truy cập "Bệnh lý". Nhấn \[Thêm mới\]. Nhập Tên bệnh, Mã ICD chuẩn, Mô tả. • Mở Dropdown chọn Chuyên khoa điều trị tương ứng. Nhấn \[Lưu\]. | Thực hiện CRUD bảng Diseases. • **Ràng buộc:** Bắt buộc có specialty\_id hợp lệ làm khóa ngoại (Foreign Key). • **Trigger NLP:** Tự động mã hóa văn bản mô tả thành mảng vector(1024) lưu vào Database để phục vụ RAG. |
| **KMA-04** | **Thiết lập Cây Tri thức (Rules Engine)** | Chọn 1 Bệnh lý đích (VD: Sốt xuất huyết). Giao diện mở ra bảng điều khiển: • Thêm các Triệu chứng điều kiện. • Kéo thanh trượt để set Trọng số (Weight). • Checkbox chọn: "Bắt buộc phải có" hoặc "Triệu chứng loại trừ". | Xử lý mảng payload cực kỳ quan trọng: • INSERT/UPDATE vào bảng Knowledge\_Rules. • Ánh xạ chính xác các trường: disease\_id, symptom\_id, weight (Float), cờ is\_mandatory (Boolean), và cờ is\_exclusion (Boolean). |
| **KMA-05** | **Sandbox Kiểm thử AI nội bộ** | Truy cập màn hình "Giả lập Chat". Đóng vai bệnh nhân nhập text để test thử xem bộ Luật chẩn đoán vừa thiết lập ở KMA-04 có tính toán ra đúng chuyên khoa mong muốn hay không. | Khởi tạo một phiên Chat ảo (Mock Session). • Chạy luồng bóc tách NER và Động cơ suy diễn (Inference Engine) để trả kết quả ra màn hình. • **Ràng buộc:** Tuyệt đối không lưu lịch sử đoạn chat này vào bảng Chat\_Sessions để tránh làm bẩn dữ liệu khám thật. |

### 

### 

### **Bảng 3: Dành cho đối tượng Kỹ thuật & Quản trị Hệ thống**

**Bộ phận: Quản trị Hệ thống (Admin / IT) | Mã số: QTHT**

**1\. Bảng yêu cầu chức năng nghiệp vụ**

| Mã ID | Tên chức năng (Feature) | Thao tác của Quản trị viên trên UI (Admin Actions) | Xử lý ngầm của Hệ thống (Backend & Database) |
| :---: | :---- | :---- | :---- |
| **SA-01** | **Đăng nhập phân hệ quản trị** | Truy cập cổng Portal nội bộ. Nhập Email/Password. Nhận thông báo lỗi nếu tài khoản không đủ thẩm quyền. | Xác thực thông tin. • **Ràng buộc:** Kiểm tra Role (chỉ Super Admin hoặc IT Support mới được cấp JWT Token). Cấp quyền truy cập các Route quản trị. |
| **SA-02** | **Quản lý danh sách tài khoản nội bộ** | Truy cập menu "Nhân sự". Xem danh sách các Bác sĩ, Lễ tân, Quản trị tri thức. Lọc theo trạng thái Hoạt động/Đã khóa. | SELECT danh sách từ bảng tài khoản nội bộ (Staff\_Accounts). • Hỗ trợ bộ lọc filter theo Role và Status. Phân trang dữ liệu hiển thị. |
| **SA-03** | **Tạo mới / Khóa tài khoản nội bộ** | Bấm nút \[Tạo mới\] để phân quyền cho nhân viên mới. Bấm gạt công tắc \[Khóa\] đối với nhân viên nghỉ việc hoặc vi phạm. | INSERT hoặc UPDATE trạng thái tài khoản thành Inactive. • **Điều kiện cứng:** Bắn lỗi 403 (Forbidden) nếu Admin tự gửi Request khóa ID của chính mình. Xóa ngay lập tức JWT Token của tài khoản bị khóa khỏi bộ nhớ Cache. |
| **RAG-01** | **Xem danh sách dữ liệu tri thức (RAG)** | Truy cập menu "Kho tri thức AI". Xem danh sách các đoạn văn bản (Sách y khoa, bài báo) đã nạp. Lọc theo Phân loại nguồn. | SELECT từ bảng Knowledge\_Chunks. • Trả về id, source\_type, source\_id, và trích xuất một phần chunk\_text. • **Ràng buộc:** Phân trang bắt buộc bằng Limit/Offset (50 chunks/trang) để tránh quá tải RAM. |
| **RAG-02** | **Nạp dữ liệu tri thức mới (RAG Ingestion)** | Nhập nội dung kiến thức y khoa vào ô Textarea, chọn Loại nguồn gốc và bấm "Nạp cho AI". Chờ thanh tiến trình (Loading bar) chạy xong. | 1\. Nhận chuỗi chunk\_text từ Frontend. 2\. Gọi API của Embedding Model (VD: BAAI/bge-m3) để mã hóa văn bản thành mảng số thực. 3\. INSERT dữ liệu vào bảng Knowledge\_Chunks với trường embedding là mảng vector(1024). |
| **RAG-03** | **Cập nhật / Xóa dữ liệu RAG** | Mở một đoạn tri thức bị lỗi thời để sửa lại chữ, hoặc bấm nút \[Thùng rác\] để xóa vĩnh viễn khỏi bộ não AI. | • **Khi Cập nhật:** Bắt buộc gọi lại API Embedding Model để sinh Vector mới, sau đó UPDATE chunk\_text và embedding để đảm bảo đồng bộ. • **Khi Xóa:** Thực hiện lệnh DELETE vật lý hoặc gán cờ is\_deleted \= true. |
| **SYS-01** | **Xem Bảng điều khiển (System Dashboard)** | Mở màn hình Tổng quan. Chọn mốc thời gian (Tuần/Tháng). Xem biểu đồ: Tổng số phiên chat, Tỷ lệ cảnh báo khẩn cấp, Top Chuyên khoa. | Chạy các hàm Aggregation SQL: • COUNT(id) từ Chat\_Sessions theo created\_at. • Lọc COUNT theo điều kiện triage\_urgency \= 'emergency'. • GROUP BY suggested\_specialty\_id kết hợp phép JOIN với bảng Specialties để vẽ biểu đồ tròn (Pie chart). |
| **SYS-02** | **Theo dõi Log & Gỡ lỗi (Debug AI)** | Truy cập menu "AI Debug". Click vào một phiên chat bị phàn nàn là chẩn đoán sai. Đọc đoạn text gốc của user và file JSON kỹ thuật mà LLM nhả về. | SELECT từ bảng Message\_Logs. • Frontend parsing trường metadata (đang lưu dưới dạng kiểu jsonb) để bung ra các dữ liệu thô (Raw LLM output, trích xuất NER bị sai lệch). Phục vụ IT báo cáo tinh chỉnh Symptom\_Synonyms. |
| **SYS-03** | **Cấu hình tham số hệ thống AI** | Mở bảng Cài đặt. Điều chỉnh các thanh trượt: Ngưỡng độ tin cậy bóc tách (Confidence Threshold, VD: 0.8), Thời gian timeout của phiên chat. Bấm Lưu. | Nhận payload cấu hình. UPDATE vào bảng cấu hình hệ thống (hoặc cập nhật biến môi trường/Redis). • Restart ngầm các worker/service liên quan để áp dụng ngưỡng confidence mới cho hệ thống. |

**4\. Xác định phạm vi dự án**

**Phạm vi trong (In-scope):**

* Khảo sát hiện trạng quy trình phân luồng chuyên khoa thủ công tại phòng khám.  
* Xây dựng mô hình yêu cầu chức năng (functional requirements) cho hệ thống Chatbot.  
* Tập trung hoàn toàn vào **Khai phá dữ liệu văn bản (NLP)** và **Hệ chuyên gia (Expert System)**.  
* Thiết kế Cây tri thức Y khoa (Ontology), quy tắc suy diễn (Inference Rules), trọng số triệu chứng (weight), luật bắt buộc (is\_mandatory) và luật loại trừ (is\_exclusion).  
* Hỗ trợ đầy đủ 3 nhóm người dùng: Bệnh nhân (Người dùng cuối), Bác sĩ/Quản trị Y khoa, và Quản trị Hệ thống (Admin/IT).  
* Các nghiệp vụ chính: Tra cứu (Retrieval), Lưu trữ (Storage), Tính toán & Logic (Processing & Reasoning), Kết xuất (Output/Reporting).

**Phạm vi ngoài (Out-of-scope):**

* Triển khai thực tế lên server và tích hợp với hệ thống bệnh án điện tử hiện có của phòng khám.  
* Thiết kế giao diện UI/UX chi tiết (chỉ tập trung vào yêu cầu chức năng).  
* Kiểm thử đầy đủ, bảo trì và vận hành sau khi triển khai.  
* Xử lý thanh toán, lịch hẹn khám, hoặc bất kỳ tính năng nào không liên quan trực tiếp đến sàng lọc triệu chứng và gợi ý chuyên khoa.

