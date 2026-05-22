"""
server.py — Flask Backend cho Website Phòng Khám + Chatbot AI
"""

import os
import json
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
from triage_engine import TriageEngine
from symptom_extractor import SymptomExtractor
from chatbot_logic import ChatbotSession

load_dotenv()

# ════════════════════════════════════════════
# KHỞI TẠO APP
# ════════════════════════════════════════════

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "phongkham_secret_key_2026")
CORS(app, supports_credentials=True)

# ─── Load AI Engine 1 lần duy nhất ───
print("🚀 Đang khởi tạo AI Engine...")
engine = TriageEngine()
extractor = SymptomExtractor(engine)
print("✅ AI Engine sẵn sàng!")

# ─── In-memory chat sessions ───
active_chats = {}  # session_id (int) -> ChatbotSession

# ─── DB helper ───
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5433"),
    "database": os.getenv("DB_NAME", "triage_bot"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASS", "123"),
}

def get_db():
    conn = psycopg2.connect(**DB_PARAMS)
    return conn


# ════════════════════════════════════════════
# TRANG CHỦ
# ════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


# ════════════════════════════════════════════
# AUTH API
# ════════════════════════════════════════════

@app.route('/api/auth/register', methods=['POST'])
def register_patient():
    data = request.json
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    gender = data.get('gender', '').strip()

    if not full_name or not phone or not password:
        return jsonify({"error": "Vui lòng điền đầy đủ thông tin"}), 400

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM Patients WHERE phone=%s", (phone,))
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "Số điện thoại đã được đăng ký"}), 409

            cur.execute("""
                INSERT INTO Patients (external_patient_id, full_name, phone, gender)
                VALUES (%s, %s, %s, %s) RETURNING id;
            """, (f"WEB_{phone}", full_name, phone, gender))
            patient_id = cur.fetchone()['id']

            # Tạo medical profile trống
            cur.execute("INSERT INTO Medical_Profiles (patient_id) VALUES (%s) ON CONFLICT DO NOTHING", (patient_id,))

            # Lưu password hash vào external_patient_id column (tạm dùng cho demo)
            # Trong thực tế nên có bảng riêng cho auth
            cur.execute("UPDATE Patients SET external_patient_id=%s WHERE id=%s",
                        (json.dumps({"phone": phone, "pw": pw_hash}), patient_id))

            conn.commit()
        conn.close()

        session['user_type'] = 'patient'
        session['patient_id'] = patient_id
        session['user_name'] = full_name

        return jsonify({"success": True, "patient_id": patient_id, "name": full_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    user_type = data.get('user_type', 'patient')  # patient | staff

    if not username or not password:
        return jsonify({"error": "Vui lòng nhập thông tin đăng nhập"}), 400

    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if user_type == 'patient':
                cur.execute("SELECT id, full_name, external_patient_id FROM Patients WHERE phone=%s", (username,))
                patient = cur.fetchone()
                if not patient:
                    conn.close()
                    return jsonify({"error": "Không tìm thấy tài khoản"}), 404

                try:
                    auth_data = json.loads(patient['external_patient_id'])
                    if not bcrypt.checkpw(password.encode(), auth_data['pw'].encode()):
                        conn.close()
                        return jsonify({"error": "Mật khẩu không đúng"}), 401
                except (json.JSONDecodeError, KeyError, TypeError):
                    conn.close()
                    return jsonify({"error": "Tài khoản chưa được thiết lập mật khẩu"}), 401

                conn.close()
                session['user_type'] = 'patient'
                session['patient_id'] = patient['id']
                session['user_name'] = patient['full_name']
                return jsonify({
                    "success": True,
                    "user_type": "patient",
                    "patient_id": patient['id'],
                    "name": patient['full_name']
                })

            else:  # staff login
                cur.execute("""
                    SELECT sa.id, sa.username, sa.full_name, sa.password_hash, sa.role,
                           sa.specialty_id, COALESCE(s.name, '') AS specialty_name
                    FROM Staff_Accounts sa
                    LEFT JOIN Specialties s ON sa.specialty_id = s.id
                    WHERE (sa.username=%s OR sa.email=%s) AND sa.is_active=true
                """, (username, username))
                staff = cur.fetchone()
                if not staff:
                    conn.close()
                    return jsonify({"error": "Tài khoản không tồn tại hoặc đã bị khóa"}), 404

                if not bcrypt.checkpw(password.encode(), staff['password_hash'].encode()):
                    conn.close()
                    return jsonify({"error": "Mật khẩu không đúng"}), 401

                conn.close()
                session['user_type'] = staff['role']
                session['staff_id'] = staff['id']
                session['user_name'] = staff['full_name']
                session['specialty_id'] = staff['specialty_id']
                return jsonify({
                    "success": True,
                    "user_type": staff['role'],
                    "staff_id": staff['id'],
                    "name": staff['full_name'],
                    "role": staff['role'],
                    "specialty_name": staff['specialty_name']
                })
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    if 'user_type' not in session:
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in": True,
        "user_type": session.get('user_type'),
        "user_name": session.get('user_name'),
        "patient_id": session.get('patient_id'),
        "staff_id": session.get('staff_id'),
        "specialty_id": session.get('specialty_id'),
    })


# ════════════════════════════════════════════
# CHATBOT API
# ════════════════════════════════════════════

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    patient_id = session.get('patient_id')
    if not patient_id:
        # Cho phép khách (guest) dùng chatbot
        patient_id = None

    # Tạo session trong DB
    if patient_id:
        session_id = engine.create_chat_session(patient_id, "")
    else:
        # Guest mode: tạo patient tạm
        guest_id = engine.get_or_create_patient("GUEST_TEMP", "Khách", None, None, None)
        session_id = engine.create_chat_session(guest_id, "")
        patient_id = guest_id

    if not session_id:
        return jsonify({"error": "Không thể tạo phiên chat"}), 500

    # Tạo ChatbotSession
    chat = ChatbotSession(engine, extractor, session_id, patient_id)
    active_chats[session_id] = chat

    greeting = chat.get_greeting()

    # Log greeting
    for msg in greeting:
        engine.log_message(session_id, "bot", msg['text'])

    return jsonify({
        "session_id": session_id,
        "messages": greeting,
        "status": chat.phase,
    })


@app.route('/api/chat/send', methods=['POST'])
def send_message():
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message', '').strip()

    if not session_id or not message:
        return jsonify({"error": "Thiếu session_id hoặc message"}), 400

    chat = active_chats.get(session_id)
    if not chat:
        return jsonify({"error": "Phiên chat không tồn tại hoặc đã hết hạn"}), 404

    # Xử lý tin nhắn
    responses = chat.process_message(message)

    # Log bot responses
    for msg in responses:
        engine.log_message(session_id, "bot", msg['text'])

    return jsonify({
        "messages": responses,
        "status": chat.phase,
        "state": chat.to_dict(),
    })


@app.route('/api/chat/history/<int:session_id>', methods=['GET'])
def get_chat_history(session_id):
    messages = engine.get_session_messages(session_id)
    formatted = []
    for m in messages:
        formatted.append({
            "role": m['sender_type'],
            "text": m['message_text'],
            "time": m['sent_at'].isoformat() if m.get('sent_at') else None,
        })
    return jsonify({"messages": formatted})


# ════════════════════════════════════════════
# PATIENT API
# ════════════════════════════════════════════

@app.route('/api/patient/profile', methods=['GET'])
def get_profile():
    pid = session.get('patient_id')
    if not pid:
        return jsonify({"error": "Chưa đăng nhập"}), 401
    profile = engine.get_patient_profile(pid)
    if not profile:
        return jsonify({"error": "Không tìm thấy hồ sơ"}), 404
    # Serialize dates
    result = dict(profile)
    if result.get('dob'):
        result['dob'] = result['dob'].isoformat()
    return jsonify(result)


@app.route('/api/patient/profile', methods=['PUT'])
def update_profile():
    pid = session.get('patient_id')
    if not pid:
        return jsonify({"error": "Chưa đăng nhập"}), 401
    data = request.json
    ok = engine.update_medical_profile(
        pid,
        data.get('height'), data.get('weight'),
        data.get('blood_type', ''),
        data.get('allergies', ''),
        data.get('underlying_conditions', '')
    )
    return jsonify({"success": ok})


@app.route('/api/patient/sessions', methods=['GET'])
def get_patient_sessions():
    pid = session.get('patient_id')
    if not pid:
        return jsonify({"error": "Chưa đăng nhập"}), 401
    sessions = engine.get_past_sessions(pid)
    result = []
    for s in sessions:
        item = dict(s)
        if item.get('start_time'):
            item['start_time'] = item['start_time'].isoformat()
        if item.get('end_time'):
            item['end_time'] = item['end_time'].isoformat()
        result.append(item)
    return jsonify({"sessions": result})


# ════════════════════════════════════════════
# DOCTOR API
# ════════════════════════════════════════════

@app.route('/api/doctor/queue', methods=['GET'])
def doctor_queue():
    if session.get('user_type') not in ('doctor', 'admin'):
        return jsonify({"error": "Không có quyền"}), 403
    specialty_id = session.get('specialty_id')

    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT cs.id, cs.start_time, cs.end_time, cs.status, cs.triage_urgency,
                       p.full_name AS patient_name, p.phone AS patient_phone,
                       sp.name AS specialty_name, sr.content AS recommendation
                FROM Chat_Sessions cs
                JOIN Patients p ON cs.patient_id = p.id
                LEFT JOIN Specialties sp ON cs.suggested_specialty_id = sp.id
                LEFT JOIN Session_Recommendations sr ON cs.id = sr.session_id
                WHERE cs.status = 'completed'
            """
            params = []
            if specialty_id:
                query += " AND cs.suggested_specialty_id = %s"
                params.append(specialty_id)
            query += " ORDER BY CASE WHEN cs.triage_urgency='emergency' THEN 0 ELSE 1 END, cs.end_time DESC LIMIT 50"
            cur.execute(query, params)
            rows = cur.fetchall()

        conn.close()
        result = []
        for r in rows:
            item = dict(r)
            if item.get('start_time'):
                item['start_time'] = item['start_time'].isoformat()
            if item.get('end_time'):
                item['end_time'] = item['end_time'].isoformat()
            result.append(item)
        return jsonify({"queue": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/doctor/session/<int:sid>', methods=['GET'])
def doctor_session_detail(sid):
    if session.get('user_type') not in ('doctor', 'admin'):
        return jsonify({"error": "Không có quyền"}), 403

    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Session info
            cur.execute("""
                SELECT cs.*, p.full_name, p.phone, p.gender, p.dob,
                       mp.height, mp.weight, mp.blood_type, mp.allergies, mp.underlying_conditions,
                       sp.name AS specialty_name
                FROM Chat_Sessions cs
                JOIN Patients p ON cs.patient_id = p.id
                LEFT JOIN Medical_Profiles mp ON p.id = mp.patient_id
                LEFT JOIN Specialties sp ON cs.suggested_specialty_id = sp.id
                WHERE cs.id = %s
            """, (sid,))
            session_info = cur.fetchone()

        conn.close()

        if not session_info:
            return jsonify({"error": "Không tìm thấy phiên"}), 404

        messages = engine.get_session_messages(sid)
        diseases = engine.get_session_disease_scores(sid)
        symptoms = engine.get_session_symptoms(sid)
        recommendation = engine.get_session_recommendation(sid)

        info = dict(session_info)
        for key in ('start_time', 'end_time', 'created_at', 'dob'):
            if info.get(key):
                info[key] = info[key].isoformat()

        msg_list = []
        for m in messages:
            msg_list.append({
                "role": m['sender_type'],
                "text": m['message_text'],
                "time": m['sent_at'].isoformat() if m.get('sent_at') else None,
            })

        return jsonify({
            "session": info,
            "messages": msg_list,
            "diseases": [dict(d) for d in diseases],
            "symptoms": [dict(s) for s in symptoms],
            "recommendation": recommendation,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/doctor/verify/<int:sid>', methods=['POST'])
def doctor_verify(sid):
    if session.get('user_type') not in ('doctor', 'admin'):
        return jsonify({"error": "Không có quyền"}), 403

    data = request.json
    is_correct = data.get('is_correct', True)
    actual_disease_id = data.get('actual_disease_id')

    try:
        conn = get_db()
        with conn.cursor() as cur:
            if is_correct:
                cur.execute("""
                    UPDATE Session_Disease_Scores SET is_doctor_verified=true
                    WHERE session_id=%s AND rank=1
                """, (sid,))
            else:
                cur.execute("""
                    UPDATE Session_Disease_Scores
                    SET is_doctor_verified=false, actual_disease_id=%s
                    WHERE session_id=%s AND rank=1
                """, (actual_disease_id, sid))
            conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════
# ADMIN API — CRUD Specialties, Symptoms, Diseases, Rules
# ════════════════════════════════════════════

@app.route('/api/admin/specialties', methods=['GET'])
def list_specialties():
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, code, name, description FROM Specialties ORDER BY name")
            rows = cur.fetchall()
        conn.close()
        return jsonify({"specialties": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/symptoms', methods=['GET'])
def list_symptoms():
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, code, name, question_text, is_red_flag FROM Symptoms ORDER BY name")
            rows = cur.fetchall()
        conn.close()
        return jsonify({"symptoms": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/diseases', methods=['GET'])
def list_diseases():
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.id, d.icd_code, d.name, d.description,
                       s.name AS specialty_name, d.specialty_id
                FROM Diseases d JOIN Specialties s ON d.specialty_id=s.id
                ORDER BY d.name
            """)
            rows = cur.fetchall()
        conn.close()
        return jsonify({"diseases": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/rules/<int:disease_id>', methods=['GET'])
def get_rules(disease_id):
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT kr.id, kr.symptom_id, s.name AS symptom_name,
                       kr.weight, kr.is_mandatory, kr.is_exclusion
                FROM Knowledge_Rules kr
                JOIN Symptoms s ON kr.symptom_id=s.id
                WHERE kr.disease_id=%s
                ORDER BY kr.weight DESC
            """, (disease_id,))
            rows = cur.fetchall()
        conn.close()
        return jsonify({"rules": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS total FROM Chat_Sessions")
            total_sessions = cur.fetchone()['total']

            cur.execute("SELECT COUNT(*) AS total FROM Chat_Sessions WHERE status='completed'")
            completed = cur.fetchone()['total']

            cur.execute("SELECT COUNT(*) AS total FROM Chat_Sessions WHERE triage_urgency='emergency'")
            emergency = cur.fetchone()['total']

            cur.execute("SELECT COUNT(*) AS total FROM Patients")
            patients = cur.fetchone()['total']

            cur.execute("""
                SELECT s.name, COUNT(cs.id) AS count
                FROM Chat_Sessions cs
                JOIN Specialties s ON cs.suggested_specialty_id = s.id
                WHERE cs.status='completed'
                GROUP BY s.name ORDER BY count DESC LIMIT 10
            """)
            specialty_stats = [dict(r) for r in cur.fetchall()]

        conn.close()
        return jsonify({
            "total_sessions": total_sessions,
            "completed_sessions": completed,
            "emergency_count": emergency,
            "total_patients": patients,
            "specialty_distribution": specialty_stats,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
