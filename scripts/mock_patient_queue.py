import psycopg2
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5433"),
    "database": os.getenv("DB_NAME", "triage_bot"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASS", "123")
}

def create_mock_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Get Specialties
        cur.execute("SELECT id, name FROM Specialties")
        specialties = cur.fetchall()
        
        if not specialties:
            print("❌ Không có dữ liệu chuyên khoa. Hãy chạy các script load data trước.")
            return

        def find_spec_id(keyword):
            for spec_id, name in specialties:
                if keyword.lower() in name.lower():
                    return spec_id
            return specialties[0][0]

        spec_noi = find_spec_id("Nội khoa")
        spec_nhi = find_spec_id("Nhi khoa")
        spec_ngoai = find_spec_id("Ngoại khoa")

        # Get some diseases for scoring
        cur.execute("SELECT id, name FROM Diseases LIMIT 5")
        diseases = cur.fetchall()
        disease_id = diseases[0][0] if diseases else None

        mock_data = [
            {
                "patient": ("BN_001", "Nguyễn Văn A", "0901234567", "Nam", "1990-05-15"),
                "profile": (170.5, 65.0, "O+", "Hải sản", "Không có"),
                "session": ("completed", "Tôi bị đau đầu và sốt cao từ tối qua.", spec_noi, "normal"),
                "messages": [
                    ("user", "Chào bác sĩ, tôi bị đau đầu và sốt cao từ tối qua."),
                    ("ai", "Chào bạn, nhiệt độ của bạn là bao nhiêu?"),
                    ("user", "Tôi đo được 39 độ."),
                    ("ai", "Bạn có bị ho hay sổ mũi không?"),
                    ("user", "Không, chỉ sốt và mệt mỏi.")
                ],
                "recommendation": "Dựa trên triệu chứng, bạn có khả năng bị Cúm hoặc Sốt virus. Đề nghị nghỉ ngơi và uống nhiều nước. Vui lòng gặp bác sĩ Nội khoa để kiểm tra thêm."
            },
            {
                "patient": ("BN_002", "Trần Bạch Tuyết", "0912345678", "Nữ", "2018-10-20"),
                "profile": (110.0, 20.0, "A+", "Không", "Hen suyễn nhẹ"),
                "session": ("completed", "Cháu nhà tôi bị nổi mẩn đỏ khắp người và ngứa ngáy.", spec_nhi, "emergency"),
                "messages": [
                    ("user", "Cháu nhà tôi tự nhiên nổi mẩn đỏ khắp người và ngứa ngáy lắm."),
                    ("ai", "Bé có biểu hiện khó thở hoặc sưng mặt không ạ?"),
                    ("user", "Có vẻ bé thở hơi khò khè."),
                    ("ai", "Triệu chứng khó thở kèm mẩn đỏ có thể là dị ứng cấp tính, vui lòng đưa bé đi cấp cứu ngay!")
                ],
                "recommendation": "CẢNH BÁO: Dấu hiệu dị ứng cấp tính/phản vệ. Hãy đưa trẻ đến phòng cấp cứu Nhi khoa ngay lập tức."
            },
            {
                "patient": ("BN_003", "Lê Hữu Đạt", "0987654321", "Nam", "1985-02-28"),
                "profile": (175.0, 78.0, "B+", "Không", "Huyết áp cao"),
                "session": ("completed", "Tôi bị đau quặn bụng dưới bên phải, đau lắm.", spec_ngoai, "emergency"),
                "messages": [
                    ("user", "Tôi bị đau quặn vùng bụng dưới bên phải từ sáng, ấn vào rất đau."),
                    ("ai", "Bạn có kèm theo sốt hoặc buồn nôn không?"),
                    ("user", "Tôi thấy buồn nôn và hơi sốt nhẹ."),
                    ("ai", "Đau hố chậu phải kèm buồn nôn có thể là dấu hiệu viêm ruột thừa. Bạn nên đến viện ngay.")
                ],
                "recommendation": "Nghi ngờ Viêm ruột thừa cấp. Yêu cầu nhập viện gấp để bác sĩ Ngoại khoa thăm khám trực tiếp."
            }
        ]

        print("🔄 Bắt đầu nạp mock data...")

        for data in mock_data:
            # Insert Patient
            cur.execute("""
                INSERT INTO Patients (external_patient_id, full_name, phone, gender, dob)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (external_patient_id) DO UPDATE 
                SET full_name = EXCLUDED.full_name
                RETURNING id
            """, data["patient"])
            patient_id = cur.fetchone()[0]

            # Insert Profile
            cur.execute("""
                INSERT INTO Medical_Profiles (patient_id, height, weight, blood_type, allergies, underlying_conditions)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (patient_id) DO NOTHING
            """, (patient_id, *data["profile"]))

            # Insert Session
            end_time = datetime.now() - timedelta(minutes=random.randint(5, 60))
            cur.execute("""
                INSERT INTO Chat_Sessions (patient_id, status, initial_complaint, suggested_specialty_id, triage_urgency, end_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (patient_id, *data["session"], end_time))
            session_id = cur.fetchone()[0]

            # Insert Messages
            msg_time = end_time - timedelta(minutes=10)
            for role, text in data["messages"]:
                cur.execute("""
                    INSERT INTO Message_Logs (session_id, sender_type, message_text, sent_at)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, role, text, msg_time))
                msg_time += timedelta(minutes=1)

            # Insert Scores (if disease exists)
            if disease_id:
                cur.execute("""
                    INSERT INTO Session_Disease_Scores (session_id, disease_id, hybrid_score, rank)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, disease_id, 0.95, 1))

            # Insert Recommendation
            cur.execute("""
                INSERT INTO Session_Recommendations (session_id, content)
                VALUES (%s, %s)
            """, (session_id, data["recommendation"]))

            print(f"✅ Đã tạo mock data cho bệnh nhân {data['patient'][1]}")

        conn.commit()
        print("🎉 Hoàn tất nạp mock data vào hàng đợi!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Có lỗi xảy ra: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_mock_data()
