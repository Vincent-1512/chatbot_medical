import streamlit as st
import time
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from triage_engine import TriageEngine
from symptom_extractor import SymptomExtractor

load_dotenv()

# --- SETUP CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="AI Triage Hub — Hệ Thống Sàng Lọc Y Tế", page_icon="🏥", layout="wide")

# --- CUSTOM CSS CHO GIAO DIỆN PREMIUM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0d6efd 0%, #02b373 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle {
        text-align: center;
        color: #6C757D;
        font-size: 1.05rem;
        margin-bottom: 25px;
    }
    .glass-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #E9ECEF;
        margin-bottom: 20px;
    }
    .emergency-card {
        background: #FFF5F5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(220, 53, 69, 0.05);
        border: 1px solid #FEB2B2;
        margin-bottom: 20px;
        color: #C53030;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# KHỞI TẠO AI ENGINE (cache, chỉ load 1 lần)
# ============================================================
@st.cache_resource
def load_ai_engine():
    engine = TriageEngine()
    extractor = SymptomExtractor(engine)
    return engine, extractor

try:
    engine, extractor = load_ai_engine()
except Exception as e:
    st.error(f"Không thể tải AI Engine: {e}")
    st.stop()

# ============================================================
# DATABASE HELPERS — mỗi lần gọi tạo connection mới, an toàn cho Streamlit
# ============================================================
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5433"),
        database=os.getenv("DB_NAME", "triage_bot"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASS", "123")
    )

def fetch_system_configs():
    configs = {}
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT config_key, config_value FROM System_Configs")
            for row in cur.fetchall():
                configs[row['config_key']] = row['config_value']
        conn.close()
    except Exception:
        pass
    return configs

# Tải cấu hình hệ thống
sys_configs = fetch_system_configs()
confidence_threshold = float(sys_configs.get("confidence_threshold", "0.55"))
welcome_msg = sys_configs.get("chatbot_welcome_message",
    "Xin chào! Tôi là Trợ lý Y tế AI. Hãy mô tả triệu chứng của bạn để tôi hỗ trợ.")

# --- PHÂN QUYỀN VAI TRÒ ---
with st.sidebar:
    st.markdown("### 🏥 HỆ THỐNG PHÒNG KHÁM")
    role = st.selectbox(
        "Lựa chọn Cổng thông tin:",
        ["👤 Bệnh nhân", "🥼 Bác sĩ", "🧠 Chuyên viên Tri thức", "⚙️ Quản trị IT"]
    )
    st.divider()

# ╔══════════════════════════════════════════════════════════════╗
# ║  👤  CỔNG THÔNG TIN: BỆNH NHÂN                              ║
# ╚══════════════════════════════════════════════════════════════╝
if role == "👤 Bệnh nhân":
    st.markdown("<h1 class='main-title'>🏥 HỆ THỐNG SÀNG LỌC BỆNH NHÂN</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Tích hợp trợ lý chatbot sàng lọc triệu chứng và gợi ý chuyên khoa khám</p>", unsafe_allow_html=True)

    # --- SIDEBAR: Giả lập SSO ---
    st.sidebar.subheader("👤 Giả lập SSO Website")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, external_patient_id, full_name FROM Patients ORDER BY id")
    patients_list = cur.fetchall()
    conn.close()

    if patients_list:
        sso_choice = st.sidebar.radio("Phương thức:", ["Chọn tài khoản có sẵn", "Đăng ký mới"])
    else:
        sso_choice = "Đăng ký mới"
        st.sidebar.info("Chưa có bệnh nhân nào. Hãy đăng ký bên dưới.")

    patient_id = None

    if sso_choice == "Chọn tài khoản có sẵn" and patients_list:
        patient_options = {f"{p['full_name']} (Mã: {p['external_patient_id'] or 'N/A'})": p['id'] for p in patients_list}
        selected_patient = st.sidebar.selectbox("Chọn bệnh nhân:", list(patient_options.keys()))
        patient_id = patient_options[selected_patient]
    else:
        with st.sidebar.form("sso_register_form"):
            new_ext_id = st.text_input("Mã bệnh nhân:", f"PAT_{int(time.time())}")
            new_name = st.text_input("Họ và tên:", "Nguyễn Thị Mai")
            new_phone = st.text_input("Số điện thoại:", "0987654321")
            new_gender = st.selectbox("Giới tính:", ["Nam", "Nữ", "Khác"])
            new_dob = st.date_input("Ngày sinh:", min_value=datetime(1930, 1, 1))
            submit_reg = st.form_submit_button("Đồng bộ & Đăng nhập")
            if submit_reg:
                patient_id = engine.get_or_create_patient(new_ext_id, new_name, new_phone, new_gender, str(new_dob))
                if patient_id:
                    st.sidebar.success(f"Đã đồng bộ: {new_name}")
                    st.rerun()

    # Fallback: nếu chưa có patient_id nhưng có danh sách
    if not patient_id:
        if patients_list:
            patient_id = patients_list[0]['id']
        else:
            st.warning("Vui lòng đăng ký bệnh nhân ở Sidebar để bắt đầu.")
            st.stop()

    # Lấy profile
    patient_profile = engine.get_patient_profile(patient_id)
    if not patient_profile:
        st.error("Không tìm thấy hồ sơ bệnh nhân.")
        st.stop()
    st.sidebar.success(f"Đăng nhập: **{patient_profile['full_name']}**")

    # Tabs
    tab_chat, tab_profile, tab_history = st.tabs(["💬 Tư vấn Chatbot AI", "📋 Hồ sơ Sức khỏe", "📜 Lịch sử Sàng lọc"])

    # ─────────────── TAB 1: CHATBOT ───────────────
    with tab_chat:
        st.markdown("### 🗣️ Trợ lý Sàng lọc Triệu chứng AI")

        # Khởi tạo session state
        if "active_session_id" not in st.session_state:
            st.session_state.active_session_id = None
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "extracted_syms" not in st.session_state:
            st.session_state.extracted_syms = []
        if "followup_symptom_id" not in st.session_state:
            st.session_state.followup_symptom_id = None
        if "session_finished" not in st.session_state:
            st.session_state.session_finished = False

        # ─── Trạng thái: Chưa có phiên ───
        if not st.session_state.active_session_id:
            st.markdown("""
            <div class='glass-card'>
                <h4>Bắt đầu phiên sàng lọc mới</h4>
                <p>Hệ thống chatbot sẽ hỏi bạn một số câu hỏi về triệu chứng cơ thể.
                Dựa trên câu trả lời, AI sẽ tự động phân loại mức độ khẩn cấp và gợi ý khoa lâm sàng phù hợp nhất.</p>
            </div>
            """, unsafe_allow_html=True)
            st.warning("⚠️ **Lưu ý:** Kết quả sàng lọc chỉ mang tính chất tham khảo, không thay thế chẩn đoán của bác sĩ.")

            if st.button("🚀 Bắt đầu tư vấn mới", type="primary"):
                session_id = engine.create_chat_session(patient_id, "Khởi tạo qua web")
                st.session_state.active_session_id = session_id
                st.session_state.chat_history = [{"role": "assistant", "content": welcome_msg}]
                st.session_state.extracted_syms = []
                st.session_state.followup_symptom_id = None
                st.session_state.session_finished = False
                engine.log_message(session_id, "assistant", welcome_msg)
                st.rerun()

        # ─── Trạng thái: Đang trong phiên chat ───
        else:
            # Render lịch sử chat
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Nếu phiên đã kết thúc (có kết quả hoặc abandoned), chỉ hiển thị + nút tạo mới
            if st.session_state.session_finished:
                st.divider()
                if st.button("🔄 Bắt đầu phiên mới"):
                    st.session_state.active_session_id = None
                    st.session_state.chat_history = []
                    st.session_state.extracted_syms = []
                    st.session_state.followup_symptom_id = None
                    st.session_state.session_finished = False
                    st.rerun()

            # Nếu đang chờ câu hỏi xác nhận follow-up
            elif st.session_state.followup_symptom_id:
                conn = get_db_connection()
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT name, question_text FROM Symptoms WHERE id = %s", (st.session_state.followup_symptom_id,))
                sym_row = cur.fetchone()
                conn.close()

                if not sym_row:
                    st.session_state.followup_symptom_id = None
                    st.rerun()

                q_text = sym_row['question_text'] or f"Bạn có bị {sym_row['name'].lower()} không?"
                st.markdown(f"**🤖 AI hỏi:** {q_text}")

                col_yes, col_no, col_skip = st.columns(3)
                with col_yes:
                    if st.button("👍 Có", use_container_width=True, key="btn_yes"):
                        engine.save_session_symptoms(
                            st.session_state.active_session_id,
                            [{"id": st.session_state.followup_symptom_id, "confidence": 1.0, "is_present": True}],
                            source="confirmation")
                        engine.log_message(st.session_state.active_session_id, "user", "Có")
                        engine.log_message(st.session_state.active_session_id, "assistant", f"✅ Ghi nhận: {sym_row['name']}")
                        st.session_state.chat_history.append({"role": "user", "content": "Có"})
                        st.session_state.chat_history.append({"role": "assistant", "content": f"✅ Ghi nhận: {sym_row['name']}"})
                        st.session_state.extracted_syms.append(st.session_state.followup_symptom_id)
                        st.session_state.followup_symptom_id = None
                        st.rerun()

                with col_no:
                    if st.button("👎 Không", use_container_width=True, key="btn_no"):
                        engine.save_session_symptoms(
                            st.session_state.active_session_id,
                            [{"id": st.session_state.followup_symptom_id, "confidence": 1.0, "is_present": False}],
                            source="confirmation")
                        engine.log_message(st.session_state.active_session_id, "user", "Không")
                        st.session_state.chat_history.append({"role": "user", "content": "Không"})
                        st.session_state.followup_symptom_id = None
                        st.rerun()

                with col_skip:
                    if st.button("❔ Không rõ", use_container_width=True, key="btn_skip"):
                        engine.log_message(st.session_state.active_session_id, "user", "Không rõ")
                        st.session_state.chat_history.append({"role": "user", "content": "Không rõ"})
                        st.session_state.followup_symptom_id = None
                        st.rerun()

            # Nếu đang chờ người dùng nhập tin nhắn tự do
            else:
                user_msg = st.chat_input("Hãy mô tả chi tiết các cảm giác khó chịu của bạn...")
                if user_msg:
                    st.session_state.chat_history.append({"role": "user", "content": user_msg})
                    engine.log_message(st.session_state.active_session_id, "user", user_msg)

                    # Rút trích triệu chứng
                    extracted = extractor.extract(user_msg, threshold=confidence_threshold)

                    if not extracted:
                        reply = "Tôi chưa nhận diện được triệu chứng cụ thể. Bạn hãy mô tả rõ hơn vị trí đau hoặc biểu hiện cơ thể nhé."
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        engine.log_message(st.session_state.active_session_id, "assistant", reply)
                        st.rerun()
                    else:
                        # Lưu triệu chứng
                        syms_to_save = [{"id": s['id'], "confidence": s['confidence'], "is_present": True} for s in extracted]
                        engine.save_session_symptoms(st.session_state.active_session_id, syms_to_save, source="llm_extract")

                        sym_names = [s['name'] for s in extracted]
                        ack_text = f"✅ AI nhận diện được: **{', '.join(sym_names)}**"
                        st.session_state.chat_history.append({"role": "assistant", "content": ack_text})
                        engine.log_message(st.session_state.active_session_id, "assistant", ack_text)

                        for s in extracted:
                            if s['id'] not in st.session_state.extracted_syms:
                                st.session_state.extracted_syms.append(s['id'])

                        # Chạy suy diễn
                        results = engine.diagnose(st.session_state.extracted_syms)

                        if results:
                            top = results[0]

                            # Tìm triệu chứng follow-up liên quan đến bệnh hàng đầu
                            next_sym_id = _find_next_followup(top['disease_id'], st.session_state.extracted_syms)

                            if next_sym_id and len(st.session_state.chat_history) < 12:
                                st.session_state.followup_symptom_id = next_sym_id
                                st.rerun()
                            else:
                                # Đủ thông tin → kết luận
                                _finalize_screening(top, results)
                                st.rerun()
                        else:
                            reply = "Thuật toán suy diễn chưa xác định được bệnh lý phù hợp. Bạn vui lòng tới quầy lễ tân để y tá phân luồng trực tiếp."
                            st.session_state.chat_history.append({"role": "assistant", "content": reply})
                            engine.log_message(st.session_state.active_session_id, "assistant", reply)
                            # Đánh dấu abandoned
                            conn = get_db_connection()
                            with conn.cursor() as cur:
                                cur.execute("UPDATE Chat_Sessions SET status='completed', end_time=NOW() WHERE id=%s",
                                            (st.session_state.active_session_id,))
                            conn.commit()
                            conn.close()
                            st.session_state.session_finished = True
                            st.rerun()

            # Nút hủy phiên (chỉ hiện khi phiên chưa kết thúc)
            if st.session_state.active_session_id and not st.session_state.session_finished:
                if st.button("❌ Huỷ phiên tư vấn hiện tại"):
                    conn = get_db_connection()
                    with conn.cursor() as cur:
                        cur.execute("UPDATE Chat_Sessions SET status='abandoned', end_time=NOW() WHERE id=%s",
                                    (st.session_state.active_session_id,))
                    conn.commit()
                    conn.close()
                    st.session_state.active_session_id = None
                    st.session_state.chat_history = []
                    st.session_state.extracted_syms = []
                    st.session_state.followup_symptom_id = None
                    st.session_state.session_finished = False
                    st.rerun()

    # ─────────────── TAB 2: HỒ SƠ SỨC KHỎE ───────────────
    with tab_profile:
        st.markdown("### 📋 Cập nhật Hồ sơ Sức khỏe Cá nhân")
        with st.form("medical_profile_form"):
            h_val = st.number_input("Chiều cao (cm):", 30.0, 250.0, float(patient_profile['height'] or 165.0))
            w_val = st.number_input("Cân nặng (kg):", 2.0, 200.0, float(patient_profile['weight'] or 60.0))

            blood_options = ["A", "B", "AB", "O", "Không rõ"]
            current_bt = patient_profile['blood_type'] or "Không rõ"
            bt_idx = blood_options.index(current_bt) if current_bt in blood_options else 4
            bt_val = st.selectbox("Nhóm máu:", blood_options, index=bt_idx)

            allergies_val = st.text_area("Tiền sử dị ứng:", value=patient_profile['allergies'] or "Không có dị ứng")
            conditions_val = st.text_area("Bệnh lý mãn tính / bệnh nền:", value=patient_profile['underlying_conditions'] or "Không")

            if st.form_submit_button("Lưu hồ sơ y tế"):
                res = engine.update_medical_profile(patient_id, h_val, w_val, bt_val, allergies_val, conditions_val)
                if res:
                    st.success("Đã lưu thành công!")
                    st.rerun()
                else:
                    st.error("Gặp lỗi khi lưu dữ liệu.")

    # ─────────────── TAB 3: LỊCH SỬ ───────────────
    with tab_history:
        st.markdown("### 📜 Lịch sử các phiên tư vấn")
        past_sessions = engine.get_past_sessions(patient_id)

        if not past_sessions:
            st.info("Bạn chưa thực hiện phiên tư vấn nào.")
        else:
            for idx_s, s in enumerate(past_sessions):
                time_str = s['start_time'].strftime("%d/%m/%Y %H:%M") if s['start_time'] else "N/A"
                status_color = "🔴" if s.get('triage_urgency') == 'emergency' else "🟢"
                spec_label = s.get('specialty_name') or 'Chưa phân loại'

                with st.expander(f"{status_color} Phiên ngày {time_str} — [{spec_label}] ({s['status']})"):
                    if s.get('triage_urgency'):
                        st.markdown(f"**Mức độ:** {s['triage_urgency']}")
                    st.markdown(s.get('recommendation') or "*Không có khuyến nghị*")
                    st.markdown("**💬 Lịch sử chat:**")
                    msgs = engine.get_session_messages(s['id'])
                    for idx_m, m in enumerate(msgs):
                        label = "👤 Bệnh nhân" if m['sender_type'] == 'user' else "🤖 AI"
                        st.markdown(f"**{label}:** {m['message_text']}")


# ╔══════════════════════════════════════════════════════════════╗
# ║  HELPER FUNCTIONS (defined at module level for Streamlit)    ║
# ╚══════════════════════════════════════════════════════════════╝
def _find_next_followup(disease_id: int, already_asked: list) -> int | None:
    """Tìm triệu chứng tiếp theo cần hỏi xác nhận dựa trên bệnh lý nghi ngờ hàng đầu."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if already_asked:
            cur.execute("""
                SELECT kr.symptom_id FROM Knowledge_Rules kr
                WHERE kr.disease_id = %s AND NOT (kr.symptom_id = ANY(%s))
                ORDER BY kr.weight DESC LIMIT 1;
            """, (disease_id, already_asked))
        else:
            cur.execute("""
                SELECT kr.symptom_id FROM Knowledge_Rules kr
                WHERE kr.disease_id = %s
                ORDER BY kr.weight DESC LIMIT 1;
            """, (disease_id,))
        row = cur.fetchone()
        conn.close()
        return row['symptom_id'] if row else None
    except Exception:
        return None


def _finalize_screening(top: dict, results: list):
    """Kết luận phiên sàng lọc và lưu kết quả vào DB."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT description FROM Diseases WHERE id = %s", (top['disease_id'],))
    desc_res = cur.fetchone()
    conn.close()

    advices = desc_res[0] if desc_res and desc_res[0] else "Chưa có lời khuyên cụ thể."
    urgency = "emergency" if top['rule_score'] > 1.2 else "routine"
    urgency_label = "Khẩn cấp" if urgency == "emergency" else "Bình thường"

    result_text = f"""### 📋 Kết quả Sàng lọc AI
👉 **Chuyên khoa đề xuất:** **{top['specialty_name']}**
💡 **Chẩn đoán sơ bộ:** {top['disease_name']}
⚠️ **Mức độ ưu tiên khám:** {urgency_label}

💡 **Lời khuyên chăm sóc ban đầu:**
{advices}"""

    st.session_state.chat_history.append({"role": "assistant", "content": result_text})
    engine.log_message(st.session_state.active_session_id, "assistant", result_text)

    # Chuẩn bị disease_scores với rank
    scored_results = []
    for rank_idx, r in enumerate(results[:5], start=1):
        scored_results.append({
            "disease_id": r['disease_id'],
            "rule_score": r['rule_score'],
            "rank": rank_idx
        })

    engine.save_screening_result(
        st.session_state.active_session_id,
        suggested_specialty_id=top['specialty_id'],
        triage_urgency=urgency,
        recommendation_text=result_text,
        disease_scores=scored_results
    )
    st.session_state.session_finished = True


# ╔══════════════════════════════════════════════════════════════╗
# ║  🥼  CỔNG THÔNG TIN: BÁC SĨ LÂM SÀNG                       ║
# ╚══════════════════════════════════════════════════════════════╝
if role == "🥼 Bác sĩ":
    st.markdown("<h1 class='main-title'>🥼 CỔNG THÔNG TIN BÁC SĨ LÂM SÀNG</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Theo dõi hàng đợi sàng lọc và xác minh kết quả chẩn đoán của AI</p>", unsafe_allow_html=True)

    if "doctor_logged_in" not in st.session_state:
        st.session_state.doctor_logged_in = False
        st.session_state.doctor_user = None
        st.session_state.doctor_specialty_id = None
        st.session_state.doctor_name = None

    if not st.session_state.doctor_logged_in:
        st.subheader("🔑 Đăng nhập Portal Bác sĩ")
        col_l, col_r = st.columns(2)
        with col_l:
            doc_username = st.text_input("Tên đăng nhập:", "dr_viet", key="doc_user")
            doc_password = st.text_input("Mật khẩu:", "doctor123", type="password", key="doc_pass")
            if st.button("Đăng nhập vào Portal", key="doc_login"):
                conn = get_db_connection()
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT id, password_hash, full_name, role, specialty_id FROM Staff_Accounts WHERE username=%s AND is_active=true", (doc_username,))
                staff = cur.fetchone()
                conn.close()
                if staff and bcrypt.checkpw(doc_password.encode(), staff['password_hash'].encode()) and staff['role'] == 'doctor':
                    st.session_state.doctor_logged_in = True
                    st.session_state.doctor_user = doc_username
                    st.session_state.doctor_specialty_id = staff['specialty_id']
                    st.session_state.doctor_name = staff['full_name']
                    st.rerun()
                else:
                    st.error("Sai tên đăng nhập / mật khẩu hoặc tài khoản bị khóa.")
    else:
        st.sidebar.markdown(f"**Bác sĩ:** {st.session_state.doctor_name}")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM Specialties WHERE id=%s", (st.session_state.doctor_specialty_id,))
        row = cur.fetchone()
        spec_name = row[0] if row else "N/A"
        conn.close()
        st.sidebar.info(f"Khoa: **{spec_name}**")

        if st.sidebar.button("🔓 Đăng xuất", key="doc_logout"):
            st.session_state.doctor_logged_in = False
            st.session_state.doctor_user = None
            st.session_state.doctor_specialty_id = None
            st.session_state.doctor_name = None
            if "doctor_viewing_session" in st.session_state:
                del st.session_state.doctor_viewing_session
            st.rerun()

        st.markdown(f"### 📋 Hàng đợi phân luồng — **{spec_name}**")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT cs.id AS session_id, p.full_name, p.gender, p.dob,
                   cs.triage_urgency, cs.end_time
            FROM Chat_Sessions cs
            JOIN Patients p ON cs.patient_id = p.id
            WHERE cs.suggested_specialty_id = %s AND cs.status = 'completed'
            ORDER BY CASE WHEN cs.triage_urgency='emergency' THEN 0 ELSE 1 END, cs.end_time DESC
        """, (st.session_state.doctor_specialty_id,))
        triage_queue = cur.fetchall()
        conn.close()

        if not triage_queue:
            st.info("Hiện không có bệnh nhân nào được phân luồng về khoa của bạn.")
        else:
            for item in triage_queue:
                end_str = item['end_time'].strftime("%H:%M - %d/%m/%Y") if item['end_time'] else "N/A"
                is_emg = item['triage_urgency'] == 'emergency'
                badge = "🚨 CẤP CỨU" if is_emg else "🟢 BÌNH THƯỜNG"
                card_cls = "emergency-card" if is_emg else "glass-card"

                st.markdown(f"""<div class='{card_cls}'>
                    <strong>👤 {item['full_name']}</strong> — {badge}
                    <div style='font-size:0.85rem;color:#718096;margin-top:4px;'>
                        Giới tính: {item['gender'] or 'N/A'} | Sinh: {item['dob'] or 'N/A'} | Sàng lọc: {end_str}
                    </div>
                </div>""", unsafe_allow_html=True)

                if st.button(f"👁️ Xem chi tiết", key=f"view_{item['session_id']}"):
                    st.session_state.doctor_viewing_session = item['session_id']
                    st.rerun()
                st.markdown("---")

        # Chi tiết báo cáo
        if "doctor_viewing_session" in st.session_state:
            s_id = st.session_state.doctor_viewing_session
            st.subheader(f"🔍 Báo cáo Sàng lọc — Phiên #{s_id}")

            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Thông tin bệnh nhân
            cur.execute("""
                SELECT p.full_name, p.gender, p.dob, p.phone,
                       mp.height, mp.weight, mp.blood_type, mp.allergies, mp.underlying_conditions
                FROM Chat_Sessions cs
                JOIN Patients p ON cs.patient_id = p.id
                LEFT JOIN Medical_Profiles mp ON p.id = mp.patient_id
                WHERE cs.id = %s
            """, (s_id,))
            p_info = cur.fetchone()

            # Disease scores
            cur.execute("""
                SELECT sds.id, sds.disease_id, d.name AS disease_name, sds.hybrid_score, sds.rank,
                       sds.is_doctor_verified, sds.actual_disease_id
                FROM Session_Disease_Scores sds
                JOIN Diseases d ON sds.disease_id = d.id
                WHERE sds.session_id = %s ORDER BY sds.rank ASC NULLS LAST
            """, (s_id,))
            scores = cur.fetchall()

            # Recommendation
            cur.execute("SELECT content FROM Session_Recommendations WHERE session_id=%s LIMIT 1", (s_id,))
            rec_row = cur.fetchone()
            ai_rec = rec_row['content'] if rec_row else "Không có khuyến nghị."

            # Messages
            cur.execute("SELECT sender_type, message_text, sent_at FROM Message_Logs WHERE session_id=%s ORDER BY sent_at", (s_id,))
            chats = cur.fetchall()

            # All diseases (for feedback dropdown)
            cur.execute("SELECT id, name FROM Diseases ORDER BY name")
            all_diseases = cur.fetchall()
            conn.close()

            if not p_info:
                st.error("Không tìm thấy thông tin phiên này.")
            else:
                col_left, col_right = st.columns(2)

                with col_left:
                    st.markdown("#### 📝 Thông tin Bệnh nhân")
                    st.markdown(f"**Tên:** {p_info['full_name']}")
                    st.markdown(f"**Giới tính:** {p_info['gender'] or 'N/A'} | **Sinh:** {p_info['dob'] or 'N/A'}")
                    st.markdown(f"**Dị ứng:** <span style='color:red;font-weight:bold;'>{p_info['allergies'] or 'Không'}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Bệnh nền:** {p_info['underlying_conditions'] or 'Không'}")
                    st.markdown(f"**Chỉ số:** Cao {p_info['height'] or 'N/A'} cm | Nặng {p_info['weight'] or 'N/A'} kg")
                    st.divider()
                    st.markdown("#### 💬 Lịch sử Chat")
                    for ci, c in enumerate(chats):
                        speaker = "👤 BN" if c['sender_type'] == 'user' else "🤖 AI"
                        st.markdown(f"**{speaker}:** {c['message_text']}")

                with col_right:
                    st.markdown("#### 🩺 Kết luận AI")
                    st.markdown(ai_rec)

                    if scores:
                        st.markdown("**Bảng điểm AI:**")
                        df_scores = pd.DataFrame(scores)
                        st.dataframe(df_scores[['disease_name', 'hybrid_score', 'rank']], hide_index=True)

                    # ─── Feedback Loop (DOC-05) ───
                    st.divider()
                    st.markdown("#### 🔄 Feedback Loop — Bác sĩ xác minh")

                    is_correct_default = 0
                    if scores and scores[0].get('is_doctor_verified') is not None:
                        is_correct_default = 0 if scores[0]['is_doctor_verified'] else 1

                    doctor_decision = st.radio("Đánh giá:", ["AI chẩn đoán Đúng", "AI chẩn đoán Sai"],
                                               index=is_correct_default, key=f"fb_{s_id}")

                    selected_actual_disease_id = None
                    if doctor_decision == "AI chẩn đoán Sai" and all_diseases:
                        disease_names = [d['name'] for d in all_diseases]
                        sel_name = st.selectbox("Bệnh thực tế:", disease_names, key=f"fb_dis_{s_id}")
                        selected_actual_disease_id = next(d['id'] for d in all_diseases if d['name'] == sel_name)

                    if st.button("💾 Lưu đánh giá", type="primary", key=f"fb_save_{s_id}"):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        is_verified = (doctor_decision == "AI chẩn đoán Đúng")
                        actual_id = selected_actual_disease_id if not is_verified else (scores[0]['disease_id'] if scores else None)
                        cur.execute("""
                            UPDATE Session_Disease_Scores
                            SET is_doctor_verified=%s, actual_disease_id=%s
                            WHERE session_id=%s
                        """, (is_verified, actual_id, s_id))
                        conn.commit()
                        conn.close()
                        st.success("Đã ghi nhận đánh giá!")
                        st.rerun()

                    # Export report
                    st.divider()
                    report_txt = f"""HỆ THỐNG SÀNG LỌC Y TẾ — BÁO CÁO
{'='*40}
Mã phiên: #{s_id}
Bệnh nhân: {p_info['full_name']}
Giới tính: {p_info['gender'] or 'N/A'} | Sinh: {p_info['dob'] or 'N/A'}
Dị ứng: {p_info['allergies'] or 'Không'}
Bệnh nền: {p_info['underlying_conditions'] or 'Không'}

KẾT QUẢ AI:
{'-'*30}
{ai_rec}

ĐÁNH GIÁ BÁC SĨ:
{'-'*30}
{doctor_decision}
Bác sĩ: {st.session_state.doctor_name}
Ngày: {datetime.now().strftime("%d/%m/%Y")}
"""
                    st.download_button("🖨️ Xuất báo cáo", data=report_txt,
                                       file_name=f"triage_report_{s_id}.txt", mime="text/plain",
                                       key=f"dl_{s_id}")

            if st.button("⬅️ Quay lại danh sách", key="back_list"):
                del st.session_state.doctor_viewing_session
                st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
# ║  🧠  CỔNG THÔNG TIN: CHUYÊN GIA TRI THỨC                    ║
# ╚══════════════════════════════════════════════════════════════╝
elif role == "🧠 Chuyên viên Tri thức":
    st.markdown("<h1 class='main-title'>🧠 CỔNG QUẢN TRỊ CÂY TRI THỨC Y KHOA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Quản lý chuyên khoa, triệu chứng, bệnh lý, luật suy diễn và sandbox AI</p>", unsafe_allow_html=True)

    if "kma_logged_in" not in st.session_state:
        st.session_state.kma_logged_in = False
        st.session_state.kma_name = None

    if not st.session_state.kma_logged_in:
        st.subheader("🔑 Đăng nhập Portal Chuyên gia Tri thức")
        kma_user = st.text_input("Tên đăng nhập:", "expert_nguyen", key="kma_user")
        kma_pass = st.text_input("Mật khẩu:", "expert123", type="password", key="kma_pass")
        if st.button("Đăng nhập", key="kma_login"):
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, password_hash, full_name, role FROM Staff_Accounts WHERE username=%s AND is_active=true", (kma_user,))
            staff = cur.fetchone()
            conn.close()
            if staff and bcrypt.checkpw(kma_pass.encode(), staff['password_hash'].encode()) and staff['role'] == 'knowledge_admin':
                st.session_state.kma_logged_in = True
                st.session_state.kma_name = staff['full_name']
                st.rerun()
            else:
                st.error("Sai thông tin đăng nhập hoặc không đủ quyền.")
    else:
        st.sidebar.markdown(f"**Chuyên gia:** {st.session_state.kma_name}")
        if st.sidebar.button("🔓 Đăng xuất", key="kma_logout"):
            st.session_state.kma_logged_in = False
            st.session_state.kma_name = None
            st.rerun()

        tab_spec, tab_sym, tab_rule, tab_sandbox = st.tabs([
            "🏥 Chuyên khoa & Bệnh lý", "🤒 Triệu chứng", "⛓️ Ma trận Luật", "🧪 Sandbox AI"
        ])

        with tab_spec:
            conn = get_db_connection()
            st.subheader("🏥 Danh sách Chuyên khoa")
            df_spec = pd.read_sql("SELECT id, code, name, description FROM Specialties ORDER BY id", conn)
            st.dataframe(df_spec, use_container_width=True, hide_index=True)

            st.subheader("🦠 Danh sách Bệnh lý")
            df_diseases = pd.read_sql("""
                SELECT d.id, d.icd_code, d.name AS disease_name, s.name AS specialty_name, d.description
                FROM Diseases d JOIN Specialties s ON d.specialty_id = s.id ORDER BY d.id
            """, conn)
            st.dataframe(df_diseases, use_container_width=True, hide_index=True)

            st.markdown("#### ➕ Thêm mới Bệnh lý")
            with st.form("add_disease_form"):
                d_name = st.text_input("Tên bệnh lý:")
                d_icd = st.text_input("Mã ICD-10:")
                d_spec = st.selectbox("Chuyên khoa:", df_spec['name'].tolist())
                d_desc = st.text_area("Mô tả/Lời khuyên:")
                if st.form_submit_button("Lưu bệnh lý") and d_name:
                    spec_id = int(df_spec[df_spec['name'] == d_spec]['id'].values[0])
                    emb = str(engine.get_embedding(f"{d_name}. {d_desc}").tolist())
                    cur = conn.cursor()
                    cur.execute("INSERT INTO Diseases (specialty_id, icd_code, name, description, embedding) VALUES (%s,%s,%s,%s,%s)",
                                (spec_id, d_icd or None, d_name, d_desc, emb))
                    conn.commit()
                    st.success(f"Đã thêm: {d_name}")
                    st.rerun()
            conn.close()

        with tab_sym:
            st.subheader("🤒 Thêm Triệu chứng mới")
            with st.form("add_symptom_form"):
                s_code = st.text_input("Mã triệu chứng (VD: DIARRHEA):").upper().strip()
                s_name = st.text_input("Tên triệu chứng chuẩn y khoa:")
                s_q = st.text_input("Câu hỏi xác nhận AI:")

                s_syns = st.text_area("Từ đồng nghĩa (phẩy cách):")
                if st.form_submit_button("Lưu triệu chứng") and s_code and s_name:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    try:
                        s_emb = str(engine.get_embedding(s_name).tolist())
                        cur.execute("INSERT INTO Symptoms (code,name,question_text,embedding) VALUES (%s,%s,%s,%s) RETURNING id",
                                    (s_code, s_name, s_q, s_emb))
                        sym_id = cur.fetchone()[0]
                        if s_syns:
                            for syn in [x.strip() for x in s_syns.split(",") if x.strip()]:
                                cur.execute("INSERT INTO Symptom_Synonyms (symptom_id,synonym) VALUES (%s,%s)", (sym_id, syn))
                        conn.commit()
                        st.success(f"Đã lưu: {s_name}")
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Lỗi: {e}")
                    finally:
                        conn.close()

            st.subheader("🔍 Tra cứu triệu chứng")
            conn = get_db_connection()
            df_sym = pd.read_sql("SELECT id, code, name, question_text FROM Symptoms ORDER BY id DESC LIMIT 50", conn)
            st.dataframe(df_sym, use_container_width=True, hide_index=True)
            conn.close()

        with tab_rule:
            st.subheader("⛓️ Cấu hình Ma trận Luật (Knowledge Rules)")
            conn = get_db_connection()
            df_d = pd.read_sql("SELECT id, name FROM Diseases ORDER BY name", conn)
            df_s = pd.read_sql("SELECT id, name FROM Symptoms ORDER BY name", conn)

            with st.form("knowledge_rules_form"):
                dis_sel = st.selectbox("Bệnh lý đích:", df_d['name'].tolist())
                sym_sel = st.selectbox("Triệu chứng:", df_s['name'].tolist())
                weight_val = st.slider("Trọng số (Weight):", 0.0, 2.0, 0.8, step=0.05)
                is_mand = st.checkbox("Bắt buộc (Mandatory)")
                is_excl = st.checkbox("Loại trừ (Exclusion)")
                if st.form_submit_button("Ghi nhận Luật"):
                    d_id = int(df_d[df_d['name'] == dis_sel]['id'].values[0])
                    s_id = int(df_s[df_s['name'] == sym_sel]['id'].values[0])
                    cur = conn.cursor()
                    cur.execute("INSERT INTO Knowledge_Rules (disease_id,symptom_id,weight,is_mandatory,is_exclusion) VALUES (%s,%s,%s,%s,%s)",
                                (d_id, s_id, weight_val, is_mand, is_excl))
                    conn.commit()
                    st.success("Đã nạp luật!")

            st.subheader("📊 Luật hiện có")
            df_rules = pd.read_sql("""
                SELECT kr.id, d.name AS disease, s.name AS symptom, kr.weight, kr.is_mandatory, kr.is_exclusion
                FROM Knowledge_Rules kr
                JOIN Diseases d ON kr.disease_id=d.id JOIN Symptoms s ON kr.symptom_id=s.id
                ORDER BY kr.id DESC LIMIT 50
            """, conn)
            st.dataframe(df_rules, use_container_width=True, hide_index=True)
            conn.close()

        with tab_sandbox:
            st.subheader("🧪 Sandbox AI (không lưu DB)")
            st.info("Nhập mô tả triệu chứng để kiểm thử Động cơ suy diễn. Phiên này KHÔNG lưu vào database.")
            sandbox_input = st.text_input("Mô tả bệnh ảo:", key="sandbox_input")
            if sandbox_input:
                sand_ext = extractor.extract(sandbox_input, threshold=confidence_threshold)
                st.write("**Bước 1: Vector Match:**")
                if sand_ext:
                    for s in sand_ext:
                        st.markdown(f"- 🤒 **{s['name']}** ({s['confidence']*100:.1f}%) — {s['source']}")
                    sym_ids = [s['id'] for s in sand_ext]
                    st.write("**Bước 2: Red Flag (Đã vô hiệu hóa)**")
                    results = engine.diagnose(sym_ids)
                        st.write("**Bước 3: Suy diễn:**")
                        if results:
                            st.dataframe(pd.DataFrame(results)[['disease_name','specialty_name','rule_score']], hide_index=True)
                        else:
                            st.warning("Không có bệnh lý khớp.")
                else:
                    st.warning("Không nhận diện được triệu chứng.")


# ╔══════════════════════════════════════════════════════════════╗
# ║  ⚙️  CỔNG THÔNG TIN: QUẢN TRỊ IT                            ║
# ╚══════════════════════════════════════════════════════════════╝
elif role == "⚙️ Quản trị IT":
    st.markdown("<h1 class='main-title'>⚙️ CỔNG QUẢN TRỊ HỆ THỐNG</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Nhân sự, RAG, thống kê, debug và cấu hình tham số AI</p>", unsafe_allow_html=True)

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
        st.session_state.admin_name = None
        st.session_state.admin_username = None

    if not st.session_state.admin_logged_in:
        st.subheader("🔑 Đăng nhập Quản trị")
        adm_user = st.text_input("Tên đăng nhập:", "admin", key="adm_user")
        adm_pass = st.text_input("Mật khẩu:", "admin123", type="password", key="adm_pass")
        if st.button("Đăng nhập", key="adm_login"):
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, password_hash, full_name, role FROM Staff_Accounts WHERE username=%s AND is_active=true", (adm_user,))
            staff = cur.fetchone()
            conn.close()
            if staff and bcrypt.checkpw(adm_pass.encode(), staff['password_hash'].encode()) and staff['role'] == 'admin':
                st.session_state.admin_logged_in = True
                st.session_state.admin_name = staff['full_name']
                st.session_state.admin_username = adm_user
                st.rerun()
            else:
                st.error("Sai thông tin hoặc không đủ quyền.")
    else:
        st.sidebar.markdown(f"**Admin:** {st.session_state.admin_name}")
        if st.sidebar.button("🔓 Đăng xuất", key="adm_logout"):
            st.session_state.admin_logged_in = False
            st.session_state.admin_name = None
            st.session_state.admin_username = None
            st.rerun()

        tab_users, tab_rag, tab_dashboard, tab_debug, tab_configs = st.tabs([
            "👥 Nhân sự", "🗂️ RAG", "📈 Thống kê", "💬 Debug", "⚙️ Cấu hình AI"
        ])

        # ─── NHÂN SỰ ───
        with tab_users:
            st.subheader("👥 Tài khoản nhân viên")
            conn = get_db_connection()
            df_staff = pd.read_sql("""
                SELECT sa.id, sa.username, sa.email, sa.full_name, sa.role,
                       s.name AS specialty, sa.is_active
                FROM Staff_Accounts sa LEFT JOIN Specialties s ON sa.specialty_id=s.id
                ORDER BY sa.id
            """, conn)
            st.dataframe(df_staff, use_container_width=True, hide_index=True)

            st.markdown("#### ➕ Tạo mới tài khoản")
            with st.form("create_staff"):
                nu = st.text_input("Username:")
                ne = st.text_input("Email:")
                nf = st.text_input("Họ tên:")
                np_ = st.text_input("Mật khẩu:", type="password")
                nr = st.selectbox("Role:", ["doctor", "knowledge_admin", "admin"])
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT id, name FROM Specialties")
                specs = cur.fetchall()
                spec_map = {s['name']: s['id'] for s in specs}
                ns = st.selectbox("Khoa (cho bác sĩ):", list(spec_map.keys()))
                if st.form_submit_button("Tạo tài khoản") and nu and np_:
                    pw = bcrypt.hashpw(np_.encode(), bcrypt.gensalt()).decode()
                    sid = spec_map[ns] if nr == 'doctor' else None
                    try:
                        cur2 = conn.cursor()
                        cur2.execute("INSERT INTO Staff_Accounts (username,email,full_name,password_hash,role,specialty_id) VALUES (%s,%s,%s,%s,%s,%s)",
                                     (nu, ne, nf, pw, nr, sid))
                        conn.commit()
                        st.success(f"Đã tạo: {nf}")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Lỗi: {e}")

            st.markdown("#### 🔒 Khóa / Mở khóa")
            with st.form("block_staff"):
                target = st.selectbox("Nhân viên:", df_staff['username'].tolist())
                action = st.radio("Thao tác:", ["Khóa", "Mở khóa"])
                if st.form_submit_button("Áp dụng"):
                    if target == st.session_state.admin_username:
                        st.error("Admin không thể tự khóa chính mình!")
                    else:
                        is_active = (action == "Mở khóa")
                        cur3 = conn.cursor()
                        cur3.execute("UPDATE Staff_Accounts SET is_active=%s WHERE username=%s", (is_active, target))
                        conn.commit()
                        st.success(f"Đã cập nhật '{target}'.")
                        st.rerun()
            conn.close()

        # ─── RAG ───
        with tab_rag:
            st.subheader("🗂️ Kho tri thức RAG")
            conn = get_db_connection()
            st.markdown("#### ➕ Nạp tri thức mới")
            with st.form("rag_form"):
                ct = st.text_area("Đoạn kiến thức y khoa:")
                src = st.selectbox("Loại nguồn:", ["combined_medical", "textbook", "medical_article"])
                ms = st.text_input("Triệu chứng liên quan (VD: HEADACHE, NAUSEA):")
                if st.form_submit_button("Nạp & Vectorize") and ct:
                    emb = str(engine.get_embedding(ct).tolist())
                    cur = conn.cursor()
                    cur.execute("INSERT INTO Knowledge_Chunks (source_type,chunk_text,mapped_symptoms,embedding) VALUES (%s,%s,%s,%s)",
                                (src, ct, ms.strip().upper() or None, emb))
                    conn.commit()
                    st.success("Đã nạp thành công!")

            st.subheader("🔍 Chunks đã nạp")
            df_ch = pd.read_sql("SELECT id, source_type, LEFT(chunk_text,100) AS preview, mapped_symptoms, created_at FROM Knowledge_Chunks ORDER BY id DESC LIMIT 20", conn)
            st.dataframe(df_ch, use_container_width=True, hide_index=True)
            conn.close()

        # ─── DASHBOARD ───
        with tab_dashboard:
            st.subheader("📈 Thống kê hệ thống")
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Chat_Sessions")
            tot = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM Chat_Sessions WHERE triage_urgency='emergency'")
            emg = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM Staff_Accounts WHERE is_active=true")
            staff_count = cur.fetchone()[0]

            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng phiên", tot)
            c2.metric("Tỷ lệ khẩn cấp", f"{emg/tot*100:.1f}%" if tot > 0 else "0%")
            c3.metric("Nhân viên", staff_count)

            st.markdown("#### 🏥 Phân bổ chuyên khoa")
            df_stats = pd.read_sql("""
                SELECT s.name AS specialty, COUNT(cs.id) AS count
                FROM Chat_Sessions cs JOIN Specialties s ON cs.suggested_specialty_id=s.id
                GROUP BY s.name ORDER BY count DESC
            """, conn)
            if not df_stats.empty:
                st.bar_chart(df_stats, x="specialty", y="count")
            else:
                st.info("Chưa có dữ liệu.")
            conn.close()

        # ─── DEBUG ───
        with tab_debug:
            st.subheader("💬 AI Debug Logs")
            conn = get_db_connection()
            df_logs = pd.read_sql("SELECT id, session_id, sender_type, LEFT(message_text,200) AS msg, metadata, sent_at FROM Message_Logs ORDER BY id DESC LIMIT 50", conn)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
            conn.close()

        # ─── CẤU HÌNH ───
        with tab_configs:
            st.subheader("⚙️ Cấu hình tham số AI")
            conn = get_db_connection()
            with st.form("sys_config"):
                nt = st.number_input("Ngưỡng Confidence:", 0.0, 1.0, confidence_threshold, 0.05)
                nw = st.text_area("Tin nhắn chào:", value=welcome_msg)
                if st.form_submit_button("Lưu cấu hình"):
                    cur = conn.cursor()
                    cur.execute("""INSERT INTO System_Configs (config_key,config_value,description) VALUES ('confidence_threshold',%s,'Ngưỡng tin cậy')
                                   ON CONFLICT (config_key) DO UPDATE SET config_value=EXCLUDED.config_value""", (str(nt),))
                    cur.execute("""INSERT INTO System_Configs (config_key,config_value,description) VALUES ('chatbot_welcome_message',%s,'Lời chào')
                                   ON CONFLICT (config_key) DO UPDATE SET config_value=EXCLUDED.config_value""", (nw,))
                    conn.commit()
                    st.success("Đã lưu!")
                    st.rerun()
            conn.close()