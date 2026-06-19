import os
import ssl
import pandas as pd
from datasets import load_dataset

# Tắt kiểm tra SSL để né lỗi trên macOS
os.environ['CURL_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context

# Giờ mới tải dataset
datasets_to_load = [
    {"path": "tarudesu/ViHealthQA", "split": "train"},
    {"path": "tmnam20/ViMedAQA", "split": "train"},
    {"path": "hungsvdut2k2/vietnamese-medical-chat", "split": "train"}
]

all_dfs = []

for item in datasets_to_load:
    try:
        print(f"📥 Đang tải dataset: {item['path']}...")
        ds = load_dataset(item['path'], split=item['split'])
        df = pd.DataFrame(ds)
        
        # Chuẩn hóa tên cột để merge (question, answer)
        if 'question' not in df.columns and 'input' in df.columns:
            df = df.rename(columns={'input': 'question'})
        if 'answer' not in df.columns and 'output' in df.columns:
            df = df.rename(columns={'output': 'answer'})
        
        # Fallback cho các cấu trúc khác
        if 'Instruction' in df.columns:
             df = df.rename(columns={'Instruction': 'question'})
        if 'Response' in df.columns:
             df = df.rename(columns={'Response': 'answer'})

        # Lấy các cột cần thiết
        if 'question' in df.columns and 'answer' in df.columns:
            all_dfs.append(df[['question', 'answer']])
            print(f"✅ Đã tải xong {item['path']} ({len(df)} dòng)")
        else:
            print(f"⚠️ Dataset {item['path']} thiếu cột question/answer. Các cột hiện có: {df.columns.tolist()}")
    except Exception as e:
        print(f"❌ Lỗi khi tải {item['path']}: {e}")

if all_dfs:
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df.to_csv("vihealthqa_raw.csv", index=False, encoding='utf-8-sig')
    print(f"🎉 TỔNG CỘNG: Đã hợp nhất {len(combined_df)} câu hỏi vào vihealthqa_raw.csv")
else:
    print("❌ Không tải được dataset nào!")