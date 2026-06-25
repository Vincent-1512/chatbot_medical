import re

filepath = "/Volumes/study/môn thực tập/chatbot/app_web.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Helper function addition
helper_func = """
def _run_diagnose_and_followup():
    import streamlit as st
    results = engine.diagnose(st.session_state.extracted_syms)
    if results:
        top = results[0]
        next_sym_id = _find_next_followup(top["disease_id"], st.session_state.asked_syms)
        if next_sym_id and len(st.session_state.chat_history) < 12:
            st.session_state.followup_symptom_id = next_sym_id
        else:
            _finalize_screening(top, results)
    else:
        reply = "Thuật toán suy diễn chưa xác định được bệnh lý phù hợp. Bạn vui lòng tới quầy lễ tân để y tá phân luồng trực tiếp."
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        engine.log_message(st.session_state.active_session_id, "assistant", reply)
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE Chat_Sessions SET status=%s, end_time=NOW() WHERE id=%s", ("completed", st.session_state.active_session_id))
        conn.commit()
        conn.close()
        st.session_state.session_finished = True
"""
if "def _run_diagnose_and_followup" not in content:
    content = content.replace("def _finalize_screening(top: dict, results: list):", helper_func.strip() + "\n\ndef _finalize_screening(top: dict, results: list):")

# 2. Add asked_syms initialization
if "if \"asked_syms\" not in st.session_state:" not in content:
    content = content.replace(
        "if \"extracted_syms\" not in st.session_state:\n            st.session_state.extracted_syms = []",
        "if \"extracted_syms\" not in st.session_state:\n            st.session_state.extracted_syms = []\n        if \"asked_syms\" not in st.session_state:\n            st.session_state.asked_syms = []"
    )

content = content.replace(
    "st.session_state.extracted_syms = []\n                st.session_state.followup_symptom_id = None",
    "st.session_state.extracted_syms = []\n                st.session_state.asked_syms = []\n                st.session_state.followup_symptom_id = None"
)

content = content.replace(
    "st.session_state.extracted_syms = []\n                    st.session_state.followup_symptom_id = None",
    "st.session_state.extracted_syms = []\n                    st.session_state.asked_syms = []\n                    st.session_state.followup_symptom_id = None"
)

# 3. Fix button clicks
yes_block_old = """                        st.session_state.extracted_syms.append(st.session_state.followup_symptom_id)
                        st.session_state.followup_symptom_id = None
                        st.rerun()"""
yes_block_new = """                        st.session_state.extracted_syms.append(st.session_state.followup_symptom_id)
                        if st.session_state.followup_symptom_id not in st.session_state.asked_syms:
                            st.session_state.asked_syms.append(st.session_state.followup_symptom_id)
                        st.session_state.followup_symptom_id = None
                        _run_diagnose_and_followup()
                        st.rerun()"""
content = content.replace(yes_block_old, yes_block_new)

no_block_old = """                        st.session_state.chat_history.append({"role": "user", "content": "Không"})
                        st.session_state.followup_symptom_id = None
                        st.rerun()"""
no_block_new = """                        st.session_state.chat_history.append({"role": "user", "content": "Không"})
                        if st.session_state.followup_symptom_id not in st.session_state.asked_syms:
                            st.session_state.asked_syms.append(st.session_state.followup_symptom_id)
                        st.session_state.followup_symptom_id = None
                        _run_diagnose_and_followup()
                        st.rerun()"""
content = content.replace(no_block_old, no_block_new)

skip_block_old = """                        st.session_state.chat_history.append({"role": "user", "content": "Không rõ"})
                        st.session_state.followup_symptom_id = None
                        st.rerun()"""
skip_block_new = """                        st.session_state.chat_history.append({"role": "user", "content": "Không rõ"})
                        if st.session_state.followup_symptom_id not in st.session_state.asked_syms:
                            st.session_state.asked_syms.append(st.session_state.followup_symptom_id)
                        st.session_state.followup_symptom_id = None
                        _run_diagnose_and_followup()
                        st.rerun()"""
content = content.replace(skip_block_old, skip_block_new)

# 4. Fix st.chat_input block
input_block_old = """                        for s in extracted:
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
                            st.rerun()"""
input_block_new = """                        for s in extracted:
                            if s['id'] not in st.session_state.extracted_syms:
                                st.session_state.extracted_syms.append(s['id'])
                            if s['id'] not in st.session_state.asked_syms:
                                st.session_state.asked_syms.append(s['id'])

                        _run_diagnose_and_followup()
                        st.rerun()"""
content = content.replace(input_block_old, input_block_new)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated successfully")
