import re
from triage_engine import TriageEngine

class SymptomExtractor:
    def __init__(self, triage_engine: TriageEngine):
        self.engine = triage_engine
        self.conn = triage_engine.conn

    def _split_clauses(self, text: str):
        """
        Tách câu dài thành các vế ngắn để tìm vector chính xác hơn.
        Dựa vào dấu câu và các liên từ phổ biến trong tiếng Việt.
        """
        # Regex chia dựa trên dấu phẩy, chấm phẩy, chấm, và các chữ "và", "hoặc", "kèm theo"
        parts = re.split(r'[,;\.\n]|\b(?:và|hoặc|kèm theo|cùng với)\b', text.lower())
        return [p.strip() for p in parts if p and p.strip()]

    def extract(self, user_input: str, threshold: float = 0.55):
        """
        🔴 PHASE 1: NGUYÊN LÝ VECTOR (Khối RAG & NLP)
        Dịch ngôn ngữ của con người thành các ID chuẩn xác bằng Vector Similarity.
        Kết hợp so khớp trực tiếp Triệu chứng và so khớp qua "Bộ nhớ tri thức" (Chunks).
        """
        print(f"\n🧠 PHASE 1: NGUYÊN LÝ VECTOR (Extracting Symptoms)")
        clauses = self._split_clauses(user_input)
        print(f"   - Phân tách vế câu: {clauses}")
        
        extracted_symptoms = {}
        
        # Cache mapping Code -> ID để tăng tốc
        with self.conn.cursor() as cur:
            cur.execute("SELECT code, id, name FROM Symptoms")
            symptom_lookup = {row[0].upper(): {"id": row[1], "name": row[2]} for row in cur.fetchall()}

        for clause in clauses:
            if len(clause) < 2:
                continue

            # --- CÁCH 1: Tìm trực tiếp trong bảng Symptoms ---
            results = self.engine.rag_retrieve(clause, top_k=3)
            for res in results:
                if res['similarity'] >= threshold:
                    sym_id = res['symptom_id']
                    if sym_id not in extracted_symptoms or res['similarity'] > extracted_symptoms[sym_id]['confidence']:
                        extracted_symptoms[sym_id] = {
                            "id": sym_id,
                            "name": res['symptom_name'],
                            "confidence": round(res['similarity'], 3),
                            "source": "Direct Match"
                        }

            # --- CÁCH 2: Tìm trong Knowledge Chunks (Câu thực tế) ---
            chunk_results = self.engine.rag_retrieve_chunks(clause, top_k=1)
            for cr in chunk_results:
                if cr['similarity'] >= 0.80: # Ngưỡng tin cậy cao cho câu thực tế
                    codes = [c.strip().upper() for c in str(cr['mapped_symptoms']).split(',')]
                    for code in codes:
                        if code in symptom_lookup:
                            sym = symptom_lookup[code]
                            sym_id = sym['id']
                            # Tăng confidence nếu khớp cả với câu thực tế
                            new_conf = round(cr['similarity'] * 1.1, 3) # Bonus 10% confidence
                            if sym_id not in extracted_symptoms or new_conf > extracted_symptoms[sym_id]['confidence']:
                                extracted_symptoms[sym_id] = {
                                    "id": sym_id,
                                    "name": sym['name'],
                                    "confidence": min(new_conf, 1.0),
                                    "source": "Knowledge Base"
                                }
        
        # Chuyển dict thành list và xếp theo confidence
        final_list = list(extracted_symptoms.values())
        final_list.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"   - Rút trích thành công {len(final_list)} triệu chứng")
        for s in final_list:
            print(f"     + {s['name']} (Độ tự tin: {s['confidence']*100:.1f}%) - Nguồn: {s['source']}")
            
        return final_list


# ====================== TEST ======================
if __name__ == "__main__":
    engine = TriageEngine()
    extractor = SymptomExtractor(engine)
    
    user_text = "Tôi bị đau đầu kèm theo buồn nôn và thi thoảng chóng mặt"
    
    print(f"\n📝 Câu nói của bệnh nhân: '{user_text}'")
    
    # Phase 1: Vector Search Extraction
    extracted_symptoms = extractor.extract(user_text, threshold=0.55)
    
    symptom_ids = [sym['id'] for sym in extracted_symptoms]
    print(f"\n   -> Danh sách ID: {symptom_ids}")
    
    # Phase 2: Lọc sinh tồn
    red_flags = engine.check_red_flags(symptom_ids)
    if red_flags:
        print("\n🚨 CẢNH BÁO: CÓ TRIỆU CHỨNG CỜ ĐỎ!")
    else:
        # Phase 3: Thuật toán suy diễn
        results = engine.diagnose(symptom_ids)
        
        print("\n--- KẾT QUẢ DIAGNOSIS ---")
        for rank, row in enumerate(results[:3], start=1):
            print(f"Top {rank}: {row.get('disease_name')} ({row.get('specialty_name')}) - Điểm Rule: {row.get('rule_score'):.2f}")
    
    engine.close()