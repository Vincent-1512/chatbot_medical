import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5433"),
    "database": os.getenv("DB_NAME", "triage_bot"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASS", "123")
}

def create_defaults():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get Specialty IDs
    cur.execute("SELECT id, name FROM Specialties")
    specialties = {row[1]: row[0] for row in cur.fetchall()}
    print(f"Specialties mapping: {specialties}")

    # Helper function to find a specialty id that contains the keyword
    def find_spec_id(keyword):
        for name, spec_id in specialties.items():
            if keyword.lower() in name.lower():
                return spec_id
        return None

    # Default passwords
    admin_pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
    doctor_pw = bcrypt.hashpw(b"doctor123", bcrypt.gensalt()).decode('utf-8')
    expert_pw = bcrypt.hashpw(b"expert123", bcrypt.gensalt()).decode('utf-8')

    # Users to insert
    users = [
        ("admin", "admin@clinic.com", "Quản Trị Hệ Thống", admin_pw, "admin", None),
        ("dr_viet", "viet.nguyen@clinic.com", "BS. Nguyễn Quốc Việt", doctor_pw, "doctor", find_spec_id("Nội khoa") or find_spec_id("internal") or 1),
        ("dr_huong", "huong.le@clinic.com", "BS. Lê Thanh Hương", doctor_pw, "doctor", find_spec_id("Nhi khoa") or find_spec_id("pediatric") or 2),
        ("dr_son", "son.tran@clinic.com", "BS. Trần Thế Sơn", doctor_pw, "doctor", find_spec_id("Ngoại khoa") or find_spec_id("surgical") or 3),
        ("expert_nguyen", "expert.nguyen@clinic.com", "Chuyên Gia Nguyễn Văn Đạt", expert_pw, "knowledge_admin", None)
    ]

    print("👤 Đang nạp tài khoản nhân viên mặc định...")
    for username, email, full_name, pw_hash, role, spec_id in users:
        try:
            cur.execute("""
                INSERT INTO Staff_Accounts (username, email, full_name, password_hash, role, specialty_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, (username, email, full_name, pw_hash, role, spec_id))
        except Exception as e:
            print(f"❌ Lỗi nạp user {username}: {e}")

    # Configs to insert
    configs = [
        ("confidence_threshold", "0.55", "Ngưỡng tin cậy tối thiểu khi trích xuất triệu chứng (0.0 -> 1.0)"),
        ("session_timeout_seconds", "1800", "Thời gian tự động kết thúc phiên chat không hoạt động (giây)"),
        ("chatbot_welcome_message", "Xin chào! Tôi là Trợ lý Y tế AI của phòng khám. Tôi có thể hỗ trợ gì cho sức khỏe của bạn hôm nay?", "Lời chào mặc định khi mở chatbot")
    ]

    print("⚙️ Đang nạp cấu hình hệ thống mặc định...")
    for key, value, desc in configs:
        try:
            cur.execute("""
                INSERT INTO System_Configs (config_key, config_value, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (config_key) DO NOTHING
            """, (key, value, desc))
        except Exception as e:
            print(f"❌ Lỗi nạp config {key}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print("🎉 Hoàn tất nạp tài khoản và cấu hình mặc định!")

if __name__ == "__main__":
    create_defaults()
