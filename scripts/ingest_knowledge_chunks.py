import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

def ingest_chunks():
    # 1. Kết nối DB
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5433"),
        database=os.getenv("DB_NAME", "triage_bot"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASS", "123")
    )
    cur = conn.cursor()

    # 2. Đọc dữ liệu đã map
    if not os.path.exists("knowledge_chunks.csv"):
        print("❌ Lỗi: Không tìm thấy file knowledge_chunks.csv. Hãy chạy scripts/auto_mapping.py trước.")
        return
    
    df = pd.read_csv("knowledge_chunks.csv")
    print(f"🚀 Bắt đầu nạp {len(df)} chunks vào Database...")

    # 3. Load Model Embedding
    print("🧠 Đang load model BAAI/bge-m3 để tạo vector...")
    model = SentenceTransformer('BAAI/bge-m3')

    # 4. Xóa dữ liệu cũ trong bảng Knowledge_Chunks (nếu muốn nạp lại từ đầu)
    cur.execute("TRUNCATE TABLE Knowledge_Chunks RESTART IDENTITY")

    # 5. Tạo Vector và Nạp theo từng đợt (batch) để tránh tràn RAM
    batch_size = 100
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i : i + batch_size]
        
        texts = batch_df['chunk_text'].tolist()
        embeddings = model.encode(texts, normalize_embeddings=True)
        
        data_to_insert = []
        for idx, row in enumerate(batch_df.to_dict('records')):
            data_to_insert.append((
                "vihealthqa",      # source_type
                None,               # source_id
                row['chunk_text'], # Câu hỏi thực tế
                row['mapped_symptoms'], # Triệu chứng đã map (mã anh) - MỚI
                embeddings[idx].tolist() # Vector 1024D
            ))
            
        execute_values(cur, """
            INSERT INTO Knowledge_Chunks (source_type, source_id, chunk_text, mapped_symptoms, embedding)
            VALUES %s
        """, data_to_insert)
        
        print(f"✅ Đã nạp thành công: {i + len(batch_df)} / {len(df)}")

    conn.commit()
    cur.close()
    conn.close()
    print("\n🎉 HOÀN THÀNH! 1.536 câu hỏi thực tế đã được 'não hóa' thành Vector trong Database.")

if __name__ == "__main__":
    ingest_chunks()
