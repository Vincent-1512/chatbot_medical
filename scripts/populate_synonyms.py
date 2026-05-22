import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def populate_synonyms():
    # 1. Kết nối DB
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5433"),
        database=os.getenv("DB_NAME", "triage_bot"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASS", "123")
    )
    cur = conn.cursor()

    # 2. Đọc mapping file
    df = pd.read_csv("symptom_mapping.csv")
    
    print("🔄 Đang xóa synonyms cũ...")
    cur.execute("TRUNCATE TABLE Symptom_Synonyms")

    print(f"🔄 Đang xử lý {len(df)} triệu chứng từ mapping file...")
    
    for _, row in df.iterrows():
        code = str(row['English_Name']).strip().upper()
        vn_names = str(row['Vietnamese_Name']).split('/')
        
        # Tìm ID của symptom trong DB
        cur.execute("SELECT id FROM Symptoms WHERE code = %s", (code,))
        res = cur.fetchone()
        
        if res:
            symptom_id = res[0]
            for vn_name in vn_names:
                vn_name = vn_name.strip()
                if vn_name:
                    cur.execute(
                        "INSERT INTO Symptom_Synonyms (symptom_id, synonym) VALUES (%s, %s)",
                        (symptom_id, vn_name)
                    )
        else:
            print(f"⚠️ Cảnh báo: Không tìm thấy symptom code '{code}' trong Database.")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ HOÀN THÀNH! Bảng Symptom_Synonyms đã được cập nhật.")

if __name__ == "__main__":
    populate_synonyms()
