import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

def ingest_chunks():
    # 1. Đọc dữ liệu đã map
    csv_path = os.path.join(os.path.dirname(__file__), '../data/knowledge_chunks.csv')
    if not os.path.exists(csv_path):
        print(f"❌ Lỗi: Không tìm thấy file {csv_path}. Hãy chạy scripts/auto_mapping.py trước.")
        return
    
    df = pd.read_csv(csv_path)
    print(f"🚀 Bắt đầu nạp {len(df)} chunks vào Database...")

    # 2. Load Model Embedding
    print("🧠 Đang load model BAAI/bge-m3 để tạo vector...")
    model = SentenceTransformer('BAAI/bge-m3')
    print("✅ Model loaded.")

    # 3. Kết nối DB
    print("🔌 Đang kết nối Database...")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5433"),
        database=os.getenv("DB_NAME", "triage_bot"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASS", "123")
    )
    cur = conn.cursor()
    print("✅ Database connected.")

    # 4. Xóa dữ liệu cũ trong bảng Knowledge_Chunks (nếu muốn nạp lại từ đầu)
    cur.execute("TRUNCATE TABLE Knowledge_Chunks RESTART IDENTITY")

    # 5. Tạo Vector và Nạp theo từng đợt (batch) để tránh tràn RAM
    batch_size = 50
    print(f"📦 Sử dụng batch_size = {batch_size}")
    
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i : i + batch_size]
        print(f"🔄 Đang xử lý batch {i//batch_size + 1} ({i} -> {i + len(batch_df)})...")
        
        texts = batch_df['chunk_text'].tolist()
        print(f"   - Đang tạo embeddings cho {len(texts)} câu...")
        embeddings = model.encode(texts, normalize_embeddings=True)
        print(f"   - Đã tạo xong embeddings.")
        
        data_to_insert = []
        for idx, row in enumerate(batch_df.to_dict('records')):
            data_to_insert.append((
                "combined_medical",      # source_type
                None,               # source_id
                row['chunk_text'], # Câu hỏi thực tế
                row['mapped_symptoms'], # Triệu chứng đã map
                embeddings[idx].tolist() # Vector 1024D
            ))
            
        print(f"   - Đang nạp vào Database...")
        execute_values(cur, """
            INSERT INTO Knowledge_Chunks (source_type, source_id, chunk_text, mapped_symptoms, embedding)
            VALUES %s
        """, data_to_insert)
        conn.commit() # Commit mỗi batch để đảm bảo dữ liệu được lưu
        
        print(f"✅ Đã nạp thành công: {i + len(batch_df)} / {len(df)}")
    cur.close()
    conn.close()
    print("\n🎉 HOÀN THÀNH! 1.536 câu hỏi thực tế đã được 'não hóa' thành Vector trong Database.")

if __name__ == "__main__":
    ingest_chunks()
