import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class TriageEngine:
    def __init__(self):
        print("💡 Đang tải Model ngôn ngữ...")
        self.embedding_model = SentenceTransformer('BAAI/bge-m3')
        
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "127.0.0.1"),
                port=os.getenv("DB_PORT", "5433"),
                database=os.getenv("DB_NAME", "triage_bot"),
                user=os.getenv("DB_USER", "admin"),
                password=os.getenv("DB_PASS", "123")
            )
            # Quan trọng: Đăng ký pgvector với connection
            register_vector(self.conn)
            print("✅ Kết nối Database & pgvector thành công!")
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Engine: {e}")
            self.conn = None

    def get_embedding(self, text: str):
        return self.embedding_model.encode(text, normalize_embeddings=True)

    def rag_retrieve(self, query_text: str, top_k: int = 5):
        query_embedding = self.get_embedding(query_text)
        
        sql = """
            SELECT 
                s.id AS symptom_id,
                s.name AS symptom_name,
                1 - (s.embedding <=> %s) AS similarity
            FROM Symptoms s
            WHERE s.embedding IS NOT NULL
            ORDER BY s.embedding <=> %s
            LIMIT %s;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (query_embedding, query_embedding, top_k))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi RAG retrieve: {e}")
            return []

    def rag_retrieve_chunks(self, query_text: str, top_k: int = 3):
        query_embedding = self.get_embedding(query_text)
        
        sql = """
            SELECT 
                chunk_text,
                mapped_symptoms,
                1 - (embedding <=> %s) AS similarity
            FROM Knowledge_Chunks
            ORDER BY embedding <=> %s
            LIMIT %s;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (query_embedding, query_embedding, top_k))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi RAG retrieve chunks: {e}")
            return []

    def rule_based_score(self, symptom_ids: list):
        if not symptom_ids:
            return []
        
        query = """
            SELECT 
                d.id AS disease_id,
                d.name AS disease_name, 
                s.name AS specialty_name,
                SUM(kr.weight) AS rule_score,
                COUNT(kr.symptom_id) AS matched_symptoms
            FROM Diseases d
            JOIN Specialties s ON d.specialty_id = s.id
            JOIN Knowledge_Rules kr ON d.id = kr.disease_id
            WHERE kr.symptom_id = ANY(%s)
            GROUP BY d.id, d.name, s.name
            ORDER BY rule_score DESC
            LIMIT 10;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (symptom_ids,))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi rule-based: {e}")
            return []

    def hybrid_score(self, user_input: str, symptom_ids: list):
        """
        Kết hợp điểm số từ Rule-based và Vector Search (nếu cần mở rộng)
        Hiện tại chủ yếu trả về kết quả từ Rule-based chẩn đoán.
        """
        return self.diagnose(symptom_ids)

    def check_red_flags(self, symptom_ids: list):
        if not symptom_ids:
            return []
            
        try:
            query = "SELECT id, name FROM Symptoms WHERE is_red_flag = true AND id = ANY(%s);"
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (symptom_ids,))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi khi kiểm tra Red Flags: {e}")
            return []

    def diagnose(self, symptom_ids: list):
        results = self.rule_based_score(symptom_ids)
        formatted_results = []
        for row in results:
            formatted_results.append({
                'disease_id': row['disease_id'],
                'disease_name': row['disease_name'],
                'specialty_name': row['specialty_name'],
                'rule_score': round(row['rule_score'], 3),
            })
        return formatted_results

    def close(self):
        if self.conn:
            self.conn.close()
            print("🔌 Đã đóng kết nối Database.")