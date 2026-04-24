import pandas as pd
import numpy as np

def create_mapping_files():
    # Đọc file dataset gốc
    df = pd.read_csv('data/dataset.csv')
    
    # Lọc 41 bệnh lý duy nhất
    diseases = df['Disease'].str.strip().unique()
    df_disease_map = pd.DataFrame({
        'English_Name': diseases,
        'Vietnamese_Name': '',  # Cột để bạn điền bản dịch
        'Specialty_Code': ''    # Cột để bạn điền ID Khoa (VD: GASTRO, NEURO)
    })
    df_disease_map.to_csv('data/disease_mapping.csv', index=False, encoding='utf-8-sig')
    
    # Lọc 131 triệu chứng duy nhất từ tất cả các cột
    symptoms = pd.unique(df.iloc[:, 1:].values.ravel('K'))
    symptoms = [str(s).strip() for s in symptoms if pd.notna(s) and str(s).strip() != '']
    symptoms = list(set(symptoms))
    
    df_symptom_map = pd.DataFrame({
        'English_Name': symptoms,
        'Vietnamese_Name': ''   # Cột để bạn điền bản dịch
    })
    df_symptom_map.to_csv('data/symptom_mapping.csv', index=False, encoding='utf-8-sig')

    print("✅ Đã tạo thành công 2 file: data/disease_mapping.csv và data/symptom_mapping.csv")

if __name__ == "__main__":
    create_mapping_files()