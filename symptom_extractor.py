import re
from triage_engine import TriageEngine


class SymptomExtractor:
    def __init__(self, triage_engine: TriageEngine):
        self.engine = triage_engine

    def _split_clauses(self, text: str):
        """
        Tách câu dài thành các vế ngắn để tìm vector chính xác hơn.
        Dựa vào dấu câu và các liên từ phổ biến trong tiếng Việt.
        """
        parts = re.split(r'[,;\.\n]|\b(?:và|hoặc|kèm theo|cùng với|ngoài ra|thêm)\b', text.lower())
        return [p.strip() for p in parts if p and len(p.strip()) >= 2]

    def _get_symptom_lookup(self):
        """Lấy mapping code -> {id, name} từ DB với connection an toàn."""
        try:
            conn = self.engine.conn  # Sử dụng property an toàn
            with conn.cursor() as cur:
                cur.execute("SELECT code, id, name FROM Symptoms")
                return {row[0].upper(): {"id": row[1], "name": row[2]} for row in cur.fetchall()}
        except Exception as e:
            print(f"❌ Lỗi lấy symptom lookup: {e}")
            try:
                self.engine.conn.rollback()
            except Exception:
                pass
            return {}

    def extract(self, user_input: str, threshold: float = 0.55):
        """
        PHASE 1: NGUYÊN LÝ VECTOR (Khối RAG & NLP)
        Dịch ngôn ngữ tự nhiên → ID triệu chứng chuẩn bằng Vector Similarity.
        Kết hợp: (1) so khớp trực tiếp Symptoms, (2) so khớp qua Knowledge Chunks.
        """
        print(f"\n🧠 PHASE 1: EXTRACTING SYMPTOMS")
        clauses = self._split_clauses(user_input)
        print(f"   - Phân tách vế câu: {clauses}")

        extracted_symptoms = {}

        # Cache mapping Code -> ID
        symptom_lookup = self._get_symptom_lookup()

        for clause in clauses:
            if len(clause) < 2:
                continue

            # --- CÁCH 1: Tìm trực tiếp trong bảng Symptoms ---
            results = self.engine.rag_retrieve(clause, top_k=1)
            for res in results:
                sim = float(res['similarity'])
                if sim >= threshold:
                    sym_id = res['symptom_id']
                    if sym_id not in extracted_symptoms or sim > extracted_symptoms[sym_id]['confidence']:
                        extracted_symptoms[sym_id] = {
                            "id": sym_id,
                            "name": res['symptom_name'],
                            "confidence": round(sim, 3),
                            "source": "Direct Match"
                        }

            # --- CÁCH 2: Tìm trong Knowledge Chunks ---
            chunk_results = self.engine.rag_retrieve_chunks(clause, top_k=1)
            for cr in chunk_results:
                chunk_sim = float(cr['similarity'])
                if chunk_sim >= 0.80 and cr['mapped_symptoms']:
                    codes = [c.strip().upper() for c in str(cr['mapped_symptoms']).split(',') if c.strip()]
                    for code in codes:
                        if code in symptom_lookup:
                            sym = symptom_lookup[code]
                            sym_id = sym['id']
                            new_conf = round(min(chunk_sim * 1.1, 1.0), 3)
                            if sym_id not in extracted_symptoms or new_conf > extracted_symptoms[sym_id]['confidence']:
                                extracted_symptoms[sym_id] = {
                                    "id": sym_id,
                                    "name": sym['name'],
                                    "confidence": new_conf,
                                    "source": "Knowledge Base"
                                }

        # Chuyển dict → list, sắp theo confidence giảm dần
        final_list = sorted(extracted_symptoms.values(), key=lambda x: x['confidence'], reverse=True)

        print(f"   - Rút trích thành công {len(final_list)} triệu chứng")
        for s in final_list:
            print(f"     + {s['name']} ({s['confidence']*100:.1f}%) — {s['source']}")

        return final_list


# ====================== TEST ======================
if __name__ == "__main__":
    engine = TriageEngine()
    extractor = SymptomExtractor(engine)

    user_text = "Tôi bị đau đầu kèm theo buồn nôn và thi thoảng chóng mặt"
    print(f"\n📝 Input: '{user_text}'")

    extracted = extractor.extract(user_text, threshold=0.55)
    sym_ids = [s['id'] for s in extracted]
    print(f"   -> IDs: {sym_ids}")

    results = engine.diagnose(sym_ids)
    print("\n--- KẾT QUẢ ---")
    for rank, row in enumerate(results[:3], 1):
        print(f"Top {rank}: {row['disease_name']} ({row['specialty_name']}) — Score: {row['rule_score']:.2f}")

    engine.close()