import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import time

class EmbeddingIngestor:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port="5433",
            database="triage_bot",
            user="admin",
            password="123"
        )
        register_vector(self.conn)
        
        print("Đang tải mô hình BAAI/bge-m3... (lần đầu sẽ chậm)")
        self.model = SentenceTransformer('BAAI/bge-m3')
        print("✅ Đã load mô hình embedding!")

    def ingest_symptoms(self):
        """Tạo embedding cho tất cả triệu chứng (bao gồm cả từ đồng nghĩa)"""
        print("\nĐang ingest embedding cho bảng Symptoms...")
        
        # Reset embedding để nạp lại với synonyms
        with self.conn.cursor() as cur:
            cur.execute("UPDATE Symptoms SET embedding = NULL")
            self.conn.commit()

            cur.execute("SELECT id, name, question_text FROM Symptoms")
            symptoms = cur.fetchall()
            
            print(f"Tìm thấy {len(symptoms)} triệu chứng cần cập nhật embedding...")
            
            for symptom_id, name, question_text in symptoms:
                # Lấy tất cả synonyms cho symptom này
                cur.execute("SELECT synonym FROM Symptom_Synonyms WHERE symptom_id = %s", (symptom_id,))
                synonyms = [row[0] for row in cur.fetchall()]
                synonyms_text = ", ".join(synonyms)
                
                # Kết hợp: Tên chính + Các từ đồng nghĩa + Câu hỏi mẫu
                text_to_embed = f"{name}. {synonyms_text}. {question_text or ''}".strip()
                embedding = self.model.encode(text_to_embed, normalize_embeddings=True)
                
                cur.execute(
                    "UPDATE Symptoms SET embedding = %s WHERE id = %s",
                    (embedding.tolist(), symptom_id)
                )
                self.conn.commit()
                print(f"  ✓ Đã embed triệu chứng ID {symptom_id} (+ {len(synonyms)} synonyms): {name[:40]}...")
        
        print("✅ Hoàn thành ingest Symptoms!")

    def ingest_diseases(self):
        """Tạo embedding cho tất cả bệnh"""
        print("\nĐang ingest embedding cho bảng Diseases...")
        
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM Diseases WHERE embedding IS NULL")
            diseases = cur.fetchall()
            
            for disease_id, name, description in diseases:
                text_to_embed = f"{name}. {description or ''}".strip()
                embedding = self.model.encode(text_to_embed, normalize_embeddings=True)
                
                cur.execute(
                    "UPDATE Diseases SET embedding = %s WHERE id = %s",
                    (embedding.tolist(), disease_id)
                )
                self.conn.commit()
                print(f"  ✓ Đã embed bệnh ID {disease_id}: {name[:60]}...")
        
        print("✅ Hoàn thành ingest Diseases!")

    def close(self):
        self.conn.close()

# ====================== CHẠY INGEST ======================
if __name__ == "__main__":
    ingestor = EmbeddingIngestor()
    
    # Chạy ingest theo thứ tự
    ingestor.ingest_symptoms()
    ingestor.ingest_diseases()
    
    ingestor.close()
    print("\n🎉 Hoàn thành toàn bộ ingestion embedding!")