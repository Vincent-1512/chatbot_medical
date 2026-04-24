import pandas as pd
import psycopg2
from triage_engine import TriageEngine
import random

def verify():
    # 1. Khởi tạo Engine
    engine = TriageEngine()
    if not engine.conn:
        print("❌ Lỗi: Không thể kết nối Database.")
        return

    # 2. Đọc dữ liệu mẫu và mapping
    df_dataset = pd.read_csv('data/dataset.csv')
    df_dis_map = pd.read_csv('data/disease_mapping.csv')
    
    # Tạo từ điển dịch Tên Anh -> Tên Việt cho Bệnh để so sánh
    disease_vn_map = dict(zip(df_dis_map['English_Name'].str.strip(), df_dis_map['Vietnamese_Name'].str.strip()))

    # Lấy 100 mẫu ngẫu nhiên
    test_samples = df_dataset.sample(n=min(100, len(df_dataset)))
    
    correct = 0
    total = len(test_samples)
    
    print(f"📊 Đang kiểm thử trên {total} mẫu ngẫu nhiên...")
    print("-" * 50)

    for i, (_, row) in enumerate(test_samples.iterrows(), 1):
        ground_truth_eng = row['Disease'].strip()
        ground_truth_vn = disease_vn_map.get(ground_truth_eng, "N/A")
        
        # Lấy danh sách triệu chứng (bỏ qua các giá trị NaN)
        symptoms_eng = [str(s).strip().upper() for s in row[1:] if pd.notna(s) and str(s).strip() != '']
        
        # Chuyển đổi Tên Anh sang ID trong DB
        symptom_ids = []
        with engine.conn.cursor() as cur:
            for s_code in symptoms_eng:
                cur.execute("SELECT id FROM Symptoms WHERE code = %s", (s_code,))
                res = cur.fetchone()
                if res:
                    symptom_ids.append(res[0])

        # Chẩn đoán
        results = engine.diagnose(symptom_ids)
        
        is_correct = False
        prediction = "N/A"
        if results:
            prediction = results[0]['disease_name']
            if prediction == ground_truth_vn:
                correct += 1
                is_correct = True

        status = "✅" if is_correct else "❌"
        if i % 20 == 0 or not is_correct: # Chỉ in những ca lỗi hoặc mỗi 20 ca để tránh spam terminal
             print(f"Mẫu {i:3}: Thực tế: {ground_truth_vn:25} | Dự đoán: {prediction:25} | {status}")

    accuracy = (correct / total) * 100
    print("-" * 50)
    print(f"📈 KẾT QUẢ CUỐI CÙNG:")
    print(f"   - Số ca khớp chính xác: {correct}/{total}")
    print(f"   - Độ chính xác (Accuracy): {accuracy:.2f}%")
    print("-" * 50)
    
    engine.close()

if __name__ == "__main__":
    verify()
