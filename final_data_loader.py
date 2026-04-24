import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from collections import Counter
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5433"),
    "database": os.getenv("DB_NAME", "triage_bot"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASS", "123")
}

def load_all_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("💡 Đang tải Model ngôn ngữ (BAAI/bge-m3)...")
    model = SentenceTransformer('BAAI/bge-m3')

    print("🚀 Bắt đầu đọc dữ liệu từ thư mục 'data/'...")
    df_dataset = pd.read_csv('data/dataset.csv')
    df_sym_map = pd.read_csv('data/symptom_mapping.csv')
    df_dis_map = pd.read_csv('data/disease_mapping.csv')
    df_severity = pd.read_csv('data/Symptom-severity.csv')
    df_precaution = pd.read_csv('data/symptom_precaution_vn.csv')

    # Làm sạch dữ liệu
    df_severity['Symptom'] = df_severity['Symptom'].str.strip()
    df_sym_map.columns = ['STT', 'English_Name', 'Vietnamese_Name']
    df_sym_map['English_Name'] = df_sym_map['English_Name'].str.strip()
    df_sym_map['Vietnamese_Name'] = df_sym_map['Vietnamese_Name'].str.strip()

    print("🧹 Đang dọn dẹp Database cũ (Reset)...")
    cur.execute("TRUNCATE TABLE Knowledge_Rules, Diseases, Symptoms, Specialties RESTART IDENTITY CASCADE")

    # 1. Nạp Chuyên Khoa
    print("🏥 Đang nạp danh mục Chuyên khoa...")
    specialties = df_dis_map['Specialty_Code'].dropna().unique()
    for spec in specialties:
        cur.execute("INSERT INTO Specialties (code, name) VALUES (%s, %s)", (spec, f"Khoa {spec}"))

    # 2. Nạp Triệu Chứng (Kèm Embedding & Red Flag)
    print("🤒 Đang tạo Vector và nạp triệu chứng (có thể mất 1-2 phút)...")
    sym_data = []
    vn_names = df_sym_map['Vietnamese_Name'].tolist()
    embeddings = model.encode(vn_names, normalize_embeddings=True)

    for i, row in df_sym_map.iterrows():
        eng_name = str(row['English_Name']).strip()
        vn_name = str(row['Vietnamese_Name']).strip()
        sev_row = df_severity[df_severity['Symptom'] == eng_name]
        # Ngưỡng cờ đỏ: Các triệu chứng có điểm nguy hiểm từ 6 trở lên (thang 1-7)
        is_red = int(sev_row['weight'].values[0]) >= 4 if not sev_row.empty else False
        embedding = embeddings[i].tolist()
        sym_data.append((eng_name.upper(), vn_name, f"Bạn có bị {vn_name.lower()} không?", is_red, embedding))

    execute_values(cur, """
        INSERT INTO Symptoms (code, name, question_text, is_red_flag, embedding) 
        VALUES %s
    """, sym_data)

    # 3. Nạp Bệnh Lý
    print("🦠 Đang nạp Bệnh lý & Lời khuyên...")
    for _, row in df_dis_map.iterrows():
        eng_dis = str(row['English_Name']).strip()
        vn_dis = str(row['Vietnamese_Name']).strip()
        spec_code = str(row['Specialty_Code']).strip()
        prec_row = df_precaution[df_precaution['Disease'].str.strip() == eng_dis]
        advice_text = ""
        if not prec_row.empty:
            p_list = [prec_row.iloc[0].get(f'Precaution_{i}', '') for i in range(1, 5)]
            valid_p = [str(p).strip() for p in p_list if pd.notna(p) and str(p).strip() != '']
            if valid_p: advice_text = "Lời khuyên: " + " | ".join(valid_p)
        
        cur.execute("SELECT id FROM Specialties WHERE code = %s", (spec_code,))
        spec_res = cur.fetchone()
        if spec_res:
            cur.execute("INSERT INTO Diseases (specialty_id, name, description) VALUES (%s, %s, %s)", (spec_res[0], vn_dis, advice_text))
            
    # 4. Nạp Knowledge Rules
    print("🧠 Đang tính toán Trọng số quy tắc...")
    rules_data = []
    for dis_eng in df_dataset['Disease'].unique():
        dis_eng_clean = str(dis_eng).strip()
        disease_df = df_dataset[df_dataset['Disease'] == dis_eng]
        total_cases = len(disease_df)
        vn_dis_rows = df_dis_map[df_dis_map['English_Name'].str.strip() == dis_eng_clean]['Vietnamese_Name'].values
        if len(vn_dis_rows) == 0: continue
        vn_dis_name = vn_dis_rows[0]
        cur.execute("SELECT id FROM Diseases WHERE name = %s", (vn_dis_name,))
        d_res = cur.fetchone()
        if not d_res: continue
        
        symptoms_list = disease_df.iloc[:, 1:].values.flatten()
        symptoms_list = [str(s).strip() for s in symptoms_list if pd.notna(s) and str(s).strip() != '']
        counts = Counter(symptoms_list)
        for sym_eng, count in counts.items():
            sev_val = df_severity[df_severity['Symptom'] == sym_eng]['weight'].values
            weight_factor = (sev_val[0] / 7) if len(sev_val) > 0 else 0.5
            final_weight = (count / total_cases) * weight_factor
            cur.execute("SELECT id FROM Symptoms WHERE code = %s", (sym_eng.upper(),))
            s_res = cur.fetchone()
            if s_res: rules_data.append((d_res[0], s_res[0], float(round(final_weight, 3))))

    execute_values(cur, "INSERT INTO Knowledge_Rules (disease_id, symptom_id, weight) VALUES %s", rules_data)
    conn.commit()
    cur.close()
    conn.close()
    print("🎉 HOÀN THÀNH XUẤT SẮC! Hệ thống đã sẵn sàng với AI Embedding.")

if __name__ == "__main__":
    load_all_data()
