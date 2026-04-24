import pandas as pd
import os

print("🚀 BẮT ĐẦU QUÁ TRÌNH AUTO-MAPPING...")

# 1. Đọc dữ liệu
try:
    qa_df = pd.read_csv("vihealthqa_raw.csv")
    symp_df = pd.read_csv("symptom_mapping.csv")
except FileNotFoundError as e:
    print(f"❌ Lỗi: Không tìm thấy file - {e}")
    print("💡 Vui lòng đảm bảo 2 file vihealthqa_raw.csv và symptom_mapping.csv nằm cùng thư mục với script.")
    exit()

# 2. Tạo từ điển triệu chứng
# Lấy cột English_Name (ID chuẩn) và Vietnamese_Name (Từ khóa để quét)
keywords = symp_df[['English_Name', 'Vietnamese_Name']].dropna().to_dict('records')
mapped_data = []

print(f"🔄 Đang quét {len(qa_df)} câu hỏi. Vui lòng đợi vài giây...")

# 3. Quét và Map tự động
for index, row in qa_df.iterrows():
    question_text = str(row['question'])
    question_lower = question_text.lower()
    found_symptoms = []

    # Kiểm tra xem câu hỏi có chứa triệu chứng nào không
    for item in keywords:
        # Tách các từ đồng nghĩa nếu bạn có lưu dạng "đau dạ dày / đau thượng vị"
        vn_names = str(item['Vietnamese_Name']).lower().split('/') 
        eng_name = str(item['English_Name']).strip()
        
        for vn_name in vn_names:
            vn_name = vn_name.strip()
            if len(vn_name) > 2 and vn_name in question_lower:
                found_symptoms.append(eng_name)

    # Nếu câu hỏi có chứa ít nhất 1 triệu chứng của hệ thống -> Giữ lại
    if len(found_symptoms) > 0:
        mapped_data.append({
            "chunk_text": question_text, # Câu hỏi tự nhiên của bệnh nhân
            "mapped_symptoms": ", ".join(list(set(found_symptoms))), # Danh sách ID triệu chứng (đã lọc trùng)
            "doctor_answer": row['answer'] # Câu trả lời của bác sĩ
        })

# 4. Xuất ra file dữ liệu "Sạch" để nạp vào Chatbot
output_file = "knowledge_chunks.csv"
result_df = pd.DataFrame(mapped_data)
result_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print("\n✅ HOÀN THÀNH!")
print(f"📊 Từ {len(qa_df)} câu rác ban đầu, đã chắt lọc được {len(result_df)} câu hỏi 'vàng' khớp với hệ thống của bạn.")
print(f"📁 Đã lưu kết quả vào file: {output_file}")