# A. BỘ PHẬN: BỆNH NHÂN (Mã số: BN)

**1. Bảng yêu cầu chức năng nghiệp vụ**

| STT | Công việc | Loại việc | Quy định | Ghi chú giao diện |
| :---: | :--- | :--- | :--- | :--- |
| **I. Quản lý tài khoản và định danh** | | | | |
| 1 | Đăng ký tài khoản mới | Lưu trữ | BN_QĐ 1 | Biểu mẫu nhập thông tin cơ bản (Họ tên, SĐT, Giới tính, Ngày sinh). Có nút ẩn/hiện mật khẩu. |
| 2 | Đăng nhập hệ thống (SSO) | Tra cứu | BN_QĐ 2 | Hỗ trợ 2 phương thức: Đăng nhập bằng tài khoản nội bộ hoặc Đồng bộ mã bệnh nhân (SSO) từ hệ thống phòng khám. |
| 3 | Đăng xuất | Cập nhật | BN_QĐ 3 | Nút đăng xuất đặt ở thanh menu bên (Sidebar). |
| **II. Hồ sơ y tế cá nhân** | | | | |
| 4 | Xem thông tin hồ sơ y tế | Tra cứu | BN_QĐ 4 | Hiển thị hồ sơ dưới dạng các thẻ thông tin (Card). Các trường hành chính cố định (Tên, Giới tính, SĐT) sẽ bị làm mờ (disable). |
| 5 | Chỉnh sửa tiền sử bệnh lý | Lưu trữ | BN_QĐ 5 | Các ô nhập liệu chiều cao, cân nặng, nhóm máu. Khung văn bản (Textarea) dành cho "Tiền sử dị ứng" và "Bệnh nền". Có nút "Lưu hồ sơ y tế". |
| **III. Tư vấn & Sàng lọc triệu chứng (Chatbot AI)** | | | | |
| 6 | Khởi tạo phiên tư vấn mới | Lưu trữ | BN_QĐ 6a | Nút "🚀 Bắt đầu tư vấn mới" nổi bật. Ngay khi bấm, màn hình hiện giao diện chat và tin nhắn chào mừng tự động từ AI. |
| 7 | Nhập văn bản mô tả triệu chứng | Lưu trữ | BN_QĐ 6b | Ô nhập liệu (Chat input) nằm ở dưới cùng để bệnh nhân gõ tự do các cảm giác khó chịu. Có nút "Gửi" hoặc nhấn Enter. |
| 8 | Trả lời câu hỏi xác nhận từ AI | Lưu trữ | BN_QĐ 6c | Hệ thống hiển thị các nút bấm phản hồi nhanh (Quick Replies) nằm ngang: [👍 Có], [👎 Không], [❔ Không rõ]. |
| 9 | Xem kết quả sàng lọc & Cảnh báo | Tra cứu, Tính toán | BN_QĐ 7 | Hiển thị "Phiếu kết quả sàng lọc" (Chuyên khoa gợi ý, Lời khuyên). Nếu có dấu hiệu nguy hiểm (Red flag), hiển thị khung màu đỏ "🚨 CẢNH BÁO KHẨN CẤP" nổi bật. Ô nhập chat bị khóa (disable). |
| 10 | Hủy phiên tư vấn hiện tại | Cập nhật | BN_QĐ 7b | Nút "❌ Huỷ phiên tư vấn hiện tại" nằm ngoài khung chat, cho phép ngắt ngang quá trình tư vấn nếu người dùng muốn dừng. |
| **IV. Tra cứu lịch sử & Phản hồi** | | | | |
| 11 | Tra cứu danh sách lịch sử tư vấn | Tra cứu | BN_QĐ 8 | Hiển thị danh sách tóm tắt các phiên khám (Ngày giờ, Trạng thái, Chuyên khoa). Có phân trang (hoặc cuộn dọc). Mỗi phiên có một thẻ có thể mở rộng (Expander). |
| 12 | Xem chi tiết phiên chat cũ | Tra cứu | BN_QĐ 9 | Hiển thị nguyên văn đoạn hội thoại (bong bóng chat) và phiếu kết quả cũ ở chế độ chỉ đọc (Read-only). Ô nhập liệu tin nhắn hoàn toàn bị ẩn đi. |
