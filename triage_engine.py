import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import json

load_dotenv()


class TriageEngine:
    def __init__(self):
        print("💡 Đang tải Model ngôn ngữ...")
        self.embedding_model = SentenceTransformer('BAAI/bge-m3')

        self._db_params = {
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": os.getenv("DB_PORT", "5433"),
            "database": os.getenv("DB_NAME", "triage_bot"),
            "user": os.getenv("DB_USER", "admin"),
            "password": os.getenv("DB_PASS", "123"),
        }
        self._conn = None
        # Kiểm tra kết nối ngay khi khởi tạo
        try:
            conn = self._get_conn()
            print("✅ Kết nối Database & pgvector thành công!")
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Engine: {e}")

    # ─── Quản lý kết nối DB an toàn ───
    def _get_conn(self):
        """Trả về một connection hợp lệ, tự tạo lại nếu cần."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self._db_params)
            register_vector(self._conn)
        else:
            # Kiểm tra connection có đang ở trạng thái lỗi không
            try:
                self._conn.isolation_level  # Quick check
                if self._conn.status != psycopg2.extensions.STATUS_READY:
                    try:
                        self._conn.rollback()
                    except Exception:
                        self._conn = psycopg2.connect(**self._db_params)
                        register_vector(self._conn)
            except Exception:
                self._conn = psycopg2.connect(**self._db_params)
                register_vector(self._conn)
        return self._conn

    @property
    def conn(self):
        """Backward compatibility: self.conn trả về connection an toàn."""
        return self._get_conn()

    # ─── Embedding ───
    def get_embedding(self, text: str):
        return self.embedding_model.encode(text, normalize_embeddings=True)

    # ─── RAG: Tìm triệu chứng tương tự ───
    def rag_retrieve(self, query_text: str, top_k: int = 5):
        query_embedding = self.get_embedding(query_text)
        sql = """
            SELECT s.id AS symptom_id, s.name AS symptom_name,
                   1 - (s.embedding <=> %s) AS similarity
            FROM Symptoms s
            WHERE s.embedding IS NOT NULL
            ORDER BY s.embedding <=> %s
            LIMIT %s;
        """
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (query_embedding, query_embedding, top_k))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi RAG retrieve: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return []

    # ─── RAG: Tìm Knowledge Chunks tương tự ───
    def rag_retrieve_chunks(self, query_text: str, top_k: int = 3):
        query_embedding = self.get_embedding(query_text)
        sql = """
            SELECT chunk_text, mapped_symptoms,
                   1 - (embedding <=> %s) AS similarity
            FROM Knowledge_Chunks
            ORDER BY embedding <=> %s
            LIMIT %s;
        """
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (query_embedding, query_embedding, top_k))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi RAG chunks: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return []

    # ─── Inference Engine: Rule-based scoring ───
    def rule_based_score(self, symptom_ids: list):
        if not symptom_ids:
            return []

        # Động cơ suy diễn (Inference Engine):
        # 1. candidate_diseases: Bệnh lý có ít nhất 1 triệu chứng khớp.
        # 2. excluded_by_rules: Loại trừ bệnh nếu triệu chứng loại trừ có mặt.
        # 3. mandatory_checks: Kiểm tra triệu chứng bắt buộc.
        # 4. failed_mandatory: Bỏ bệnh nếu thiếu triệu chứng bắt buộc.
        # 5. Tính tổng trọng số.
        query = """
            WITH candidate_diseases AS (
                SELECT DISTINCT disease_id
                FROM Knowledge_Rules
                WHERE symptom_id = ANY(%s)
            ),
            excluded_by_rules AS (
                SELECT DISTINCT disease_id
                FROM Knowledge_Rules
                WHERE symptom_id = ANY(%s) AND is_exclusion = true
            ),
            mandatory_checks AS (
                SELECT disease_id, symptom_id
                FROM Knowledge_Rules
                WHERE is_mandatory = true
                AND disease_id IN (SELECT disease_id FROM candidate_diseases)
            ),
            failed_mandatory AS (
                SELECT DISTINCT disease_id
                FROM mandatory_checks
                WHERE NOT (symptom_id = ANY(%s))
            )
            SELECT
                d.id AS disease_id,
                d.name AS disease_name,
                s.id AS specialty_id,
                s.name AS specialty_name,
                COALESCE(SUM(kr.weight), 0) AS rule_score,
                COUNT(kr.symptom_id) AS matched_symptoms
            FROM Diseases d
            JOIN Specialties s ON d.specialty_id = s.id
            JOIN Knowledge_Rules kr ON d.id = kr.disease_id
            WHERE d.id IN (SELECT disease_id FROM candidate_diseases)
              AND d.id NOT IN (SELECT disease_id FROM excluded_by_rules)
              AND d.id NOT IN (SELECT disease_id FROM failed_mandatory)
              AND kr.symptom_id = ANY(%s)
              AND kr.is_exclusion = false
            GROUP BY d.id, d.name, s.id, s.name
            ORDER BY rule_score DESC
            LIMIT 10;
        """
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (symptom_ids, symptom_ids, symptom_ids, symptom_ids))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi rule-based: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return []

    # ─── Diagnose: Kết hợp kết quả suy diễn ───
    def diagnose(self, symptom_ids: list):
        results = self.rule_based_score(symptom_ids)
        formatted = []
        for row in results:
            formatted.append({
                'disease_id': row['disease_id'],
                'disease_name': row['disease_name'],
                'specialty_id': row['specialty_id'],
                'specialty_name': row['specialty_name'],
                'rule_score': round(float(row['rule_score']), 3),
                'matched_symptoms': row['matched_symptoms'],
            })
        return formatted

    # ─── Check Red Flags ───
    def check_red_flags(self, symptom_ids: list):
        if not symptom_ids:
            return []
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name FROM Symptoms WHERE is_red_flag=true AND id=ANY(%s)", (symptom_ids,))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi Red Flags: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return []

    # ==========================================
    # DATABASE HELPERS
    # ==========================================

    def get_or_create_patient(self, external_id, full_name, phone=None, gender=None, dob=None):
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM Patients WHERE external_patient_id=%s", (external_id,))
                row = cur.fetchone()
                if row:
                    return row['id']
                cur.execute("""
                    INSERT INTO Patients (external_patient_id, full_name, phone, gender, dob)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id;
                """, (external_id, full_name, phone, gender, dob))
                new_id = cur.fetchone()['id']
                cur.execute("INSERT INTO Medical_Profiles (patient_id) VALUES (%s) ON CONFLICT DO NOTHING", (new_id,))
                conn.commit()
                return new_id
        except Exception as e:
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            print(f"❌ Lỗi get_or_create_patient: {e}")
            return None

    def get_patient_profile(self, patient_id):
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT p.id, p.external_patient_id, p.full_name, p.phone, p.gender, p.dob,
                           mp.height, mp.weight, mp.blood_type, mp.allergies, mp.underlying_conditions
                    FROM Patients p
                    LEFT JOIN Medical_Profiles mp ON p.id = mp.patient_id
                    WHERE p.id = %s
                """, (patient_id,))
                return cur.fetchone()
        except Exception as e:
            print(f"❌ Lỗi get_patient_profile: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return None

    def update_medical_profile(self, patient_id, height, weight, blood_type, allergies, conditions):
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO Medical_Profiles (patient_id, height, weight, blood_type, allergies, underlying_conditions)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (patient_id) DO UPDATE SET
                        height=EXCLUDED.height, weight=EXCLUDED.weight,
                        blood_type=EXCLUDED.blood_type, allergies=EXCLUDED.allergies,
                        underlying_conditions=EXCLUDED.underlying_conditions, updated_at=NOW();
                """, (patient_id, height, weight, blood_type, allergies, conditions))
                conn.commit()
                return True
        except Exception as e:
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            print(f"❌ Lỗi update_medical_profile: {e}")
            return False

    def create_chat_session(self, patient_id, initial_complaint=""):
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO Chat_Sessions (patient_id, initial_complaint, status)
                    VALUES (%s, %s, 'in_progress') RETURNING id;
                """, (patient_id, initial_complaint))
                sid = cur.fetchone()['id']
                conn.commit()
                return sid
        except Exception as e:
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            print(f"❌ Lỗi create_chat_session: {e}")
            return None

    def log_message(self, session_id, sender_type, message_text, metadata=None):
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO Message_Logs (session_id, sender_type, message_text, metadata)
                    VALUES (%s, %s, %s, %s);
                """, (session_id, sender_type, message_text, json.dumps(metadata) if metadata else None))
                conn.commit()
                return True
        except Exception as e:
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            print(f"❌ Lỗi log_message: {e}")
            return False

    def save_session_symptoms(self, session_id, extracted_symptoms, source="llm_extract"):
        """
        extracted_symptoms: list of dicts {id, confidence, is_present}
        """
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                for sym in extracted_symptoms:
                    cur.execute("""
                        INSERT INTO Session_Symptoms (session_id, symptom_id, is_present, confidence, source)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (session_id, sym['id'], sym.get('is_present', True), sym.get('confidence', 0.8), source))
                conn.commit()
                return True
        except Exception as e:
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            print(f"❌ Lỗi save_session_symptoms: {e}")
            return False

    def get_session_symptoms(self, session_id):
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ss.symptom_id, s.name, s.code, ss.is_present, ss.confidence, ss.source
                    FROM Session_Symptoms ss JOIN Symptoms s ON ss.symptom_id=s.id
                    WHERE ss.session_id=%s
                """, (session_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi get_session_symptoms: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return []

    def save_screening_result(self, session_id, suggested_specialty_id, triage_urgency,
                              recommendation_text, disease_scores):
        """
        disease_scores: list of dicts {disease_id, rule_score, rank}
        """
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                # 1. Update session
                cur.execute("""
                    UPDATE Chat_Sessions
                    SET suggested_specialty_id=%s, triage_urgency=%s, end_time=NOW(), status='completed'
                    WHERE id=%s;
                """, (suggested_specialty_id, triage_urgency, session_id))

                # 2. Save recommendation
                cur.execute("DELETE FROM Session_Recommendations WHERE session_id=%s", (session_id,))
                cur.execute("INSERT INTO Session_Recommendations (session_id, content) VALUES (%s, %s)",
                            (session_id, recommendation_text))

                # 3. Save disease scores
                cur.execute("DELETE FROM Session_Disease_Scores WHERE session_id=%s", (session_id,))
                for sc in disease_scores:
                    cur.execute("""
                        INSERT INTO Session_Disease_Scores (session_id, disease_id, hybrid_score, rank)
                        VALUES (%s, %s, %s, %s);
                    """, (session_id, sc['disease_id'], sc.get('rule_score', 0), sc.get('rank', 0)))

                conn.commit()
                return True
        except Exception as e:
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            print(f"❌ Lỗi save_screening_result: {e}")
            return False

    def get_past_sessions(self, patient_id):
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT cs.id, cs.start_time, cs.end_time, cs.status, cs.triage_urgency,
                           s.name AS specialty_name, sr.content AS recommendation
                    FROM Chat_Sessions cs
                    LEFT JOIN Specialties s ON cs.suggested_specialty_id = s.id
                    LEFT JOIN Session_Recommendations sr ON cs.id = sr.session_id
                    WHERE cs.patient_id = %s
                    ORDER BY cs.start_time DESC;
                """, (patient_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi get_past_sessions: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return []

    def get_session_messages(self, session_id):
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT sender_type, message_text, sent_at, metadata
                    FROM Message_Logs WHERE session_id=%s ORDER BY sent_at ASC;
                """, (session_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi get_session_messages: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return []

    def get_session_recommendation(self, session_id):
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute("SELECT content FROM Session_Recommendations WHERE session_id=%s LIMIT 1", (session_id,))
                res = cur.fetchone()
                return res[0] if res else ""
        except Exception as e:
            print(f"❌ Lỗi get_session_recommendation: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return ""

    def get_session_disease_scores(self, session_id):
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT sds.disease_id, d.name AS disease_name, sds.hybrid_score, sds.rank,
                           sds.is_doctor_verified, sds.actual_disease_id
                    FROM Session_Disease_Scores sds
                    JOIN Diseases d ON sds.disease_id = d.id
                    WHERE sds.session_id=%s ORDER BY sds.rank ASC;
                """, (session_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Lỗi get_session_disease_scores: {e}")
            try:
                self._get_conn().rollback()
            except Exception:
                pass
            return []

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            print("🔌 Đã đóng kết nối Database.")