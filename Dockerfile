FROM python:3.9-slim

WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Expose port của Streamlit
EXPOSE 8501

# Chạy ứng dụng Streamlit
CMD ["streamlit", "run", "app_web.py", "--server.port=8501", "--server.address=0.0.0.0"]
