"""
chatbot_logic.py — Bộ não Chatbot Sàng Lọc Triệu Chứng (Multi-turn)

Quản lý hội thoại nhiều lượt:
1. Thu thập triệu chứng từ ngôn ngữ tự nhiên (NLP + RAG)
2. Hỏi thêm triệu chứng liên quan dựa trên bệnh ứng viên
3. Đưa ra kết luận khi đủ thông tin
"""

import re
import json
from triage_engine import TriageEngine
from symptom_extractor import SymptomExtractor


# ─── Từ khóa phát hiện Có / Không / Không rõ ───
YES_KEYWORDS = {"có", "đúng", "ừ", "vâng", "phải", "rồi", "yes", "đúng rồi", "có ạ", "dạ có", "uhm"}
NO_KEYWORDS = {"không", "ko", "k", "no", "chưa", "hông", "không có", "đâu có", "dạ không", "không ạ", "chưa có"}
UNSURE_KEYWORDS = {"không rõ", "không biết", "chưa rõ", "không chắc", "chưa biết", "hình như", "có lẽ", "not sure"}


def detect_response_type(text: str):
    """Phân loại câu trả lời: 'yes', 'no', 'unsure', hoặc 'free_text'."""
    cleaned = text.strip().lower()
    # Kiểm tra exact match ngắn gọn trước
    if cleaned in YES_KEYWORDS:
        return "yes"
    if cleaned in NO_KEYWORDS:
        return "no"
    for kw in UNSURE_KEYWORDS:
        if kw in cleaned:
            return "unsure"
    # Kiểm tra pattern "có ... " ở đầu câu ngắn
    if len(cleaned) < 20:
        if cleaned.startswith("có"):
            return "yes"
        if cleaned.startswith("không") or cleaned.startswith("ko"):
            return "no"
    return "free_text"


class ChatbotSession:
    """
    Quản lý 1 phiên hội thoại chatbot.
    Tích lũy triệu chứng qua nhiều lượt → hỏi thêm → kết luận.
    """

    GREETING_MESSAGE = (
        "Xin chào! Tôi là trợ lý AI sàng lọc triệu chứng của phòng khám. 🏥\n\n"
        "Bạn hãy mô tả các triệu chứng bạn đang gặp phải nhé. "
        "Ví dụ: *\"Tôi bị đau đầu, buồn nôn và hơi chóng mặt\"*"
    )

    MAX_FOLLOW_UP_QUESTIONS = 6  # Tối đa số câu hỏi xác nhận

    def __init__(self, engine: TriageEngine, extractor: SymptomExtractor,
                 session_id: int, patient_id: int):
        self.engine = engine
        self.extractor = extractor
        self.session_id = session_id
        self.patient_id = patient_id

        # ─── Trạng thái triệu chứng ───
        self.confirmed_symptoms = {}   # {symptom_id: {id, name, confidence}}
        self.denied_symptom_ids = set()
        self.unsure_symptom_ids = set()
        self.asked_symptom_ids = set()

        # ─── Trạng thái hội thoại ───
        self.pending_question = None   # {symptom_id, symptom_name, question_text}
        self.follow_up_count = 0
        self.phase = "greeting"        # greeting → collecting → asking → finished
        self.diagnosis_result = None

    # ════════════════════════════════════════════
    # PUBLIC: Xử lý tin nhắn từ bệnh nhân
    # ════════════════════════════════════════════

    def get_greeting(self):
        """Trả về tin nhắn chào mừng."""
        return [{"role": "bot", "text": self.GREETING_MESSAGE}]

    def process_message(self, user_text: str):
        """
        Xử lý 1 tin nhắn và trả về danh sách phản hồi.
        Returns: list of {role, text, type?, options?, result?}
        """
        user_text = user_text.strip()
        if not user_text:
            return [{"role": "bot", "text": "Bạn vui lòng mô tả triệu chứng nhé."}]

        # Log tin nhắn vào DB
        self.engine.log_message(self.session_id, "patient", user_text)

        if self.phase == "finished":
            return [{"role": "bot", "text": "Phiên tư vấn đã kết thúc. Bạn có thể bắt đầu phiên mới nếu cần."}]

        if self.phase == "greeting":
            self.phase = "collecting"
            return self._handle_first_input(user_text)

        if self.phase == "asking" and self.pending_question:
            return self._handle_confirmation_response(user_text)

        # phase == "collecting" — thêm triệu chứng từ free text
        return self._handle_additional_input(user_text)

    # ════════════════════════════════════════════
    # PRIVATE: Xử lý từng loại input
    # ════════════════════════════════════════════

    def _handle_first_input(self, user_text: str):
        """Xử lý tin nhắn đầu tiên: rút trích triệu chứng ban đầu."""
        extracted = self.extractor.extract(user_text, threshold=0.60)

        if not extracted:
            responses = [{
                "role": "bot",
                "text": "Tôi chưa nhận diện được triệu chứng cụ thể. "
                        "Bạn có thể mô tả chi tiết hơn không?\n\n"
                        "Ví dụ: *đau đầu, sốt, ho, đau bụng, buồn nôn...*"
            }]
            self.phase = "collecting"
            return responses

        # Lưu triệu chứng đã xác nhận
        self._add_confirmed_symptoms(extracted)


        # Tạo phản hồi xác nhận + hỏi thêm
        return self._build_followup_response(extracted)

    def _handle_additional_input(self, user_text: str):
        """Xử lý free text bổ sung thêm triệu chứng."""
        extracted = self.extractor.extract(user_text, threshold=0.60)
        new_symptoms = []

        for sym in extracted:
            sid = sym['id']
            if sid not in self.confirmed_symptoms and sid not in self.denied_symptom_ids:
                new_symptoms.append(sym)
                self._add_confirmed_symptoms([sym])

        if not new_symptoms:
            # Không tìm thấy triệu chứng mới, hỏi lại
            return [{
                "role": "bot",
                "text": "Tôi chưa nhận diện thêm triệu chứng mới. "
                        "Bạn có thể mô tả cụ thể hơn không?"
            }]


        return self._build_followup_response(new_symptoms)

    def _handle_confirmation_response(self, user_text: str):
        """Xử lý câu trả lời Có/Không/Không rõ cho câu hỏi xác nhận."""
        response_type = detect_response_type(user_text)
        pending = self.pending_question
        self.pending_question = None

        if response_type == "yes":
            # Xác nhận triệu chứng
            self.confirmed_symptoms[pending['symptom_id']] = {
                'id': pending['symptom_id'],
                'name': pending['symptom_name'],
                'confidence': 0.95,
            }
            self.engine.save_session_symptoms(
                self.session_id,
                [{'id': pending['symptom_id'], 'is_present': True, 'confidence': 0.95}],
                source="confirmation"
            )

        elif response_type == "no":
            self.denied_symptom_ids.add(pending['symptom_id'])
            self.engine.save_session_symptoms(
                self.session_id,
                [{'id': pending['symptom_id'], 'is_present': False, 'confidence': 0.95}],
                source="confirmation"
            )

        elif response_type == "unsure":
            self.unsure_symptom_ids.add(pending['symptom_id'])

        else:
            # Free text response → cố gắng extract thêm triệu chứng
            extracted = self.extractor.extract(user_text, threshold=0.60)
            found_pending = False
            for sym in extracted:
                if sym['id'] == pending['symptom_id']:
                    found_pending = True
                self._add_confirmed_symptoms([sym])

            if not found_pending:
                # Không đề cập triệu chứng đang hỏi → coi như unsure
                self.unsure_symptom_ids.add(pending['symptom_id'])


        # Tiếp tục hỏi hoặc kết luận
        return self._decide_next_step()

    # ════════════════════════════════════════════
    # LOGIC: Quyết định bước tiếp theo
    # ════════════════════════════════════════════

    def _build_followup_response(self, newly_extracted: list):
        """Xác nhận triệu chứng tìm được + quyết định hỏi thêm hay kết luận."""
        # Tạo tin nhắn xác nhận
        names = [s['name'] for s in newly_extracted]
        confirm_text = f"Tôi đã ghi nhận các triệu chứng: **{', '.join(names)}**."
        responses = [{"role": "bot", "text": confirm_text}]

        # Quyết định bước tiếp
        next_msgs = self._decide_next_step()
        responses.extend(next_msgs)
        return responses

    def _decide_next_step(self):
        """Quyết định: hỏi thêm hay đưa kết luận."""
        confirmed_ids = list(self.confirmed_symptoms.keys())

        if not confirmed_ids:
            return [{"role": "bot", "text": "Bạn hãy mô tả thêm triệu chứng nhé."}]

        # Kiểm tra đã hỏi đủ chưa
        if self.follow_up_count >= self.MAX_FOLLOW_UP_QUESTIONS:
            return self._finalize_diagnosis()

        # Tìm câu hỏi tiếp theo
        next_q = self._find_next_question(confirmed_ids)
        if next_q is None:
            # Không còn triệu chứng quan trọng cần hỏi
            return self._finalize_diagnosis()

        # Hỏi triệu chứng tiếp
        self.pending_question = next_q
        self.asked_symptom_ids.add(next_q['symptom_id'])
        self.follow_up_count += 1
        self.phase = "asking"

        question_text = next_q['question_text'] or f"Bạn có bị **{next_q['symptom_name']}** không?"

        return [{
            "role": "bot",
            "text": question_text,
            "type": "question",
            "options": ["Có", "Không", "Không rõ"]
        }]

    def _find_next_question(self, confirmed_ids: list):
        """
        Tìm triệu chứng quan trọng nhất chưa hỏi dựa trên bệnh ứng viên.
        Ưu tiên: is_mandatory > weight cao > xuất hiện ở nhiều bệnh.
        """
        already_known = (
            set(self.confirmed_symptoms.keys())
            | self.denied_symptom_ids
            | self.unsure_symptom_ids
            | self.asked_symptom_ids
        )

        try:
            conn = self.engine.conn
            with conn.cursor() as cur:
                # Lấy top bệnh ứng viên hiện tại
                results = self.engine.diagnose(confirmed_ids)
                if not results:
                    return None

                top_disease_ids = [r['disease_id'] for r in results[:5]]
                if not top_disease_ids:
                    return None

                # Tìm triệu chứng liên quan chưa hỏi, sắp theo ưu tiên
                cur.execute("""
                    SELECT DISTINCT kr.symptom_id, s.name, s.question_text,
                           MAX(kr.weight) AS max_weight,
                           BOOL_OR(kr.is_mandatory) AS has_mandatory,
                           COUNT(DISTINCT kr.disease_id) AS disease_count
                    FROM Knowledge_Rules kr
                    JOIN Symptoms s ON kr.symptom_id = s.id
                    WHERE kr.disease_id = ANY(%s)
                      AND kr.symptom_id != ALL(%s)
                      AND kr.is_exclusion = false
                    GROUP BY kr.symptom_id, s.name, s.question_text
                    ORDER BY has_mandatory DESC, disease_count DESC, max_weight DESC
                    LIMIT 1;
                """, (top_disease_ids, list(already_known)))

                row = cur.fetchone()
                if row:
                    return {
                        'symptom_id': row[0],
                        'symptom_name': row[1],
                        'question_text': row[2],
                    }
        except Exception as e:
            print(f"❌ Lỗi _find_next_question: {e}")
            try:
                self.engine.conn.rollback()
            except Exception:
                pass

        return None

    # ════════════════════════════════════════════
    # LOGIC: Kết luận chẩn đoán
    # ════════════════════════════════════════════

    def _finalize_diagnosis(self):
        """Chạy inference cuối cùng và đưa ra kết quả."""
        self.phase = "finished"
        confirmed_ids = list(self.confirmed_symptoms.keys())

        if not confirmed_ids:
            return [{
                "role": "bot",
                "text": "Tôi chưa thu thập đủ thông tin để đưa ra gợi ý. "
                        "Vui lòng bắt đầu phiên tư vấn mới."
            }]

        results = self.engine.diagnose(confirmed_ids)

        if not results:
            msg = (
                "Dựa trên các triệu chứng bạn mô tả, tôi chưa tìm được bệnh lý phù hợp "
                "trong cơ sở tri thức hiện tại.\n\n"
                "**Khuyến nghị:** Bạn nên đến phòng khám để được bác sĩ thăm khám trực tiếp."
            )
            self._save_result(None, "normal", msg, [])
            return [{"role": "bot", "text": msg}]

        top = results[0]
        top3 = results[:3]

        # Xác định mức độ khẩn cấp
        urgency = "normal"
        if top.get('rule_score', 0) >= 8:
            urgency = "high"

        # Tạo bảng kết quả
        confirmed_names = [s['name'] for s in self.confirmed_symptoms.values()]
        denied_names = self._get_symptom_names(self.denied_symptom_ids)

        result_text = self._format_result(top, top3, confirmed_names, denied_names, urgency)

        # Lưu kết quả vào DB
        scored = [{'disease_id': r['disease_id'], 'rule_score': r['rule_score'], 'rank': i+1}
                  for i, r in enumerate(top3)]
        self._save_result(top['specialty_id'], urgency, result_text, scored)

        self.diagnosis_result = {
            'specialty_name': top['specialty_name'],
            'specialty_id': top['specialty_id'],
            'urgency': urgency,
            'diseases': top3,
            'confirmed_symptoms': confirmed_names,
        }

        return [{
            "role": "bot",
            "text": result_text,
            "type": "result",
            "result": self.diagnosis_result
        }]

    def _format_result(self, top, top3, confirmed_names, denied_names, urgency):
        """Format kết quả chẩn đoán thành text đẹp."""
        urgency_label = {"normal": "Bình thường", "high": "Ưu tiên cao", "emergency": "🚨 Cấp cứu"}
        lines = []
        lines.append("━" * 30)
        lines.append("📋 **KẾT QUẢ SÀNG LỌC**")
        lines.append("━" * 30)
        lines.append("")
        lines.append(f"🏥 **Chuyên khoa gợi ý:** {top['specialty_name']}")
        lines.append(f"⚡ **Mức độ ưu tiên:** {urgency_label.get(urgency, urgency)}")
        lines.append("")
        lines.append("**Bệnh lý có thể liên quan:**")
        for i, d in enumerate(top3, 1):
            score_bar = "●" * min(int(d['rule_score']), 10) + "○" * max(0, 10 - int(d['rule_score']))
            lines.append(f"  {i}. {d['disease_name']} [{score_bar}] ({d['rule_score']:.1f} điểm)")
        lines.append("")
        lines.append(f"✅ **Triệu chứng ghi nhận:** {', '.join(confirmed_names)}")
        if denied_names:
            lines.append(f"❌ **Triệu chứng đã loại trừ:** {', '.join(denied_names)}")
        lines.append("")
        lines.append("━" * 30)
        lines.append("⚠️ *Kết quả chỉ mang tính tham khảo. Vui lòng đến phòng khám để được bác sĩ thăm khám trực tiếp.*")
        return "\n".join(lines)

    # ════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════

    def _add_confirmed_symptoms(self, symptoms: list):
        """Thêm triệu chứng đã xác nhận."""
        for sym in symptoms:
            sid = sym['id']
            if sid not in self.confirmed_symptoms:
                self.confirmed_symptoms[sid] = {
                    'id': sid,
                    'name': sym['name'],
                    'confidence': sym.get('confidence', 0.8),
                }
        # Lưu vào DB
        self.engine.save_session_symptoms(
            self.session_id,
            [{'id': s['id'], 'is_present': True, 'confidence': s.get('confidence', 0.8)}
             for s in symptoms],
            source="llm_extract"
        )



    def _get_symptom_names(self, symptom_ids: set):
        """Lấy tên triệu chứng từ IDs."""
        if not symptom_ids:
            return []
        try:
            conn = self.engine.conn
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM Symptoms WHERE id = ANY(%s)", (list(symptom_ids),))
                return [r[0] for r in cur.fetchall()]
        except Exception:
            return []

    def _save_result(self, specialty_id, urgency, text, disease_scores):
        """Lưu kết quả sàng lọc vào DB."""
        try:
            self.engine.save_screening_result(
                self.session_id, specialty_id, urgency, text, disease_scores
            )
        except Exception as e:
            print(f"❌ Lỗi save result: {e}")

    def to_dict(self):
        """Serialize state cho API response."""
        return {
            'session_id': self.session_id,
            'patient_id': self.patient_id,
            'phase': self.phase,
            'confirmed_symptoms': list(self.confirmed_symptoms.values()),
            'denied_count': len(self.denied_symptom_ids),
            'follow_up_count': self.follow_up_count,
            'diagnosis_result': self.diagnosis_result,
        }
