# Chatbot Medical (AI Triage System)

Dự án Hệ thống Chatbot AI sàng lọc y tế thông minh (Triage).

## Cấu trúc thư mục mới:

- `app_web.py`: Giao diện Chatbot cơ bản (Streamlit).
- `server.py`: Server Hệ thống Phòng khám Đa khoa & Chatbot (Flask).
- `main_app.py`: Giao diện dòng lệnh Chatbot (CLI).
- `triage_engine.py`, `chatbot_logic.py`, `symptom_extractor.py`: Các file logic xử lý chính của AI.
- `data/`: Chứa các file dữ liệu `.csv` (dataset, từ điển triệu chứng, v.v.).
- `docs/`: Chứa các tài liệu hướng dẫn (`.md`).
- `scripts/`: Chứa các script hỗ trợ (load data, nạp embedding, mapping).

## Hướng dẫn chạy (Sử dụng Makefile)

Dự án đã được tích hợp `Makefile` để thống nhất các lệnh chạy. Bạn chỉ cần mở Terminal và gõ:

```bash
make help
```
Để xem danh sách các lệnh hỗ trợ:
- `make web`: Chạy website phòng khám (Flask) trên cổng 5002.
- `make cli`: Chạy chatbot trên dòng lệnh terminal.
- `make streamlit`: Chạy giao diện chatbot Streamlit.
- `make db-up`: Khởi động Database qua Docker.
- `make db-down`: Tắt Database.
- `make data`: Chạy script nạp lại toàn bộ dữ liệu vào Database.
- `make install`: Cài đặt thư viện cần thiết.
