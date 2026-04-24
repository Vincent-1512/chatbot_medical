import streamlit as st
import time
from triage_engine import TriageEngine
from symptom_extractor import SymptomExtractor

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="AI Triage Medical", page_icon="🏥", layout="wide")

# Hàm khởi tạo hệ thống AI (Chỉ load 1 lần để tránh giật lag)
@st.cache_resource
def load_ai_engine():
    engine = TriageEngine()
    extractor = SymptomExtractor(engine)
    return engine, extractor

engine, extractor = load_ai_engine()

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align: center; color: #0066cc;'>🏥 Hệ thống Sàng lọc Y tế Thông minh</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Mô tả triệu chứng của bạn, AI sẽ phân tích và gợi ý chuyên khoa phù hợp.</p>", unsafe_allow_html=True)
st.divider()

# Chia trang web thành 2 cột: Khung chat (trái) và Thông tin (phải)
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🗣️ Trợ lý Y tế AI")
    
    # Khởi tạo bộ nhớ tạm cho lịch sử chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Hiển thị các tin nhắn cũ
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Ô nhập liệu của người dùng
    if user_input := st.chat_input("Ví dụ: Tôi bị đau ngực, khó thở và sốt cao..."):
        # In câu của người dùng lên màn hình
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Trợ lý AI bắt đầu suy nghĩ và trả lời
        with st.chat_message("assistant"):
            with st.spinner("🧠 AI đang phân tích dữ liệu y khoa..."):
                try:
                    # ==========================================
                    # PHASE 1: NGUYÊN LÝ VECTOR (Trích xuất)
                    # ==========================================
                    extracted = extractor.extract(user_input, threshold=0.55)
                    if not extracted:
                        response = "Tôi chưa nhận diện được rõ triệu chứng của bạn khớp với hồ sơ y tế nào. Bạn hãy mô tả chi tiết hơn nhé."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.stop()

                    sym_names = [f"{s['name']} ({s['confidence']*100:.0f}%)" for s in extracted]
                    sym_ids = [s['id'] for s in extracted]
                    
                    st.success(f"**Phase 1 (Vector Match):** Đã nhận diện triệu chứng: {', '.join(sym_names)}")

                    # ==========================================
                    # PHASE 2: BỘ LỌC SINH TỒN (Red Flag)
                    # ==========================================
                    red_flag_records = engine.check_red_flags(sym_ids)
                    red_flags = [r['name'] for r in red_flag_records]

                    if red_flags:
                        alert_msg = f"🚨 **PHASE 2 ALERT CẤP CỨU:** Phát hiện nhóm triệu chứng đe dọa sinh mệnh ({', '.join(red_flags)}). Vui lòng đến Bệnh viện hoặc gọi Cấp cứu ngay lập tức!"
                        st.error(alert_msg)
                        st.session_state.messages.append({"role": "assistant", "content": alert_msg})
                        st.stop()
                    else:
                        st.info("**Phase 2 (Sinh tồn):** Không có dấu hiệu đe dọa tính mạng trực tiếp.")

                    # ==========================================
                    # PHASE 3: THUẬT TOÁN SUY DIỄN (Rule-Based)
                    # ==========================================
                    results = engine.diagnose(sym_ids)
                    
                    # ==========================================
                    # PHASE 4: TỔNG HỢP VÀ ĐIỀU HƯỚNG
                    # ==========================================
                    if results:
                        top = results[0]
                        st.markdown(f"### 📋 Kết quả Sàng lọc")
                        st.success(f"👉 **Gợi ý Chuyên khoa ưu tiên:** **{top['specialty_name']}**")
                        st.markdown(f"**Dự đoán bệnh lý (dựa trên Rule-based):** {top['disease_name']} _(Điểm khớp: {top['rule_score']})_")
                        
                        # Truy vấn description từ DB để lấy lời khuyên
                        with engine.conn.cursor() as cur:
                            cur.execute("SELECT description FROM Diseases WHERE id = %s", (top['disease_id'],))
                            desc = cur.fetchone()
                            
                        if desc and desc[0]:
                            st.markdown("💡 **Lời khuyên chăm sóc tại nhà:**")
                            advices = desc[0].replace("Lời khuyên: ", "").split(" | ")
                            for adv in advices:
                                st.markdown(f"- {adv}")
                                
                        # Lưu vào lịch sử chat
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"Gợi ý khám tại **{top['specialty_name']}** (Dự đoán Rule-based: {top['disease_name']})"
                        })
                    else:
                        st.warning("Triệu chứng chưa đủ khớp với bệnh lý cụ thể nào trong DB phân tuyến. Vui lòng hỏi trực tiếp bác sĩ tổng quát.")
                        
                except Exception as e:
                    st.error(f"Đã có lỗi xảy ra trong quá trình xử lý: {e}")

with col2:
    st.markdown("### 📊 Thông tin Hỗ trợ")
    st.info("Hệ thống được huấn luyện trên **131 triệu chứng** và **41 loại bệnh lý** phổ biến.")
    st.warning("**Lưu ý:** Đây là hệ thống AI hỗ trợ phân luồng bệnh nhân, không thay thế chẩn đoán của Bác sĩ chuyên khoa.")