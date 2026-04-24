import os
import ssl

# Tắt kiểm tra SSL để né lỗi trên macOS
os.environ['CURL_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context

from datasets import load_dataset
import pandas as pd

# Giờ mới tải dataset
try:
    ds = load_dataset("tarudesu/ViHealthQA", split='train')
    df = pd.DataFrame(ds)
    df.to_csv("vihealthqa_raw.csv", index=False, encoding='utf-8-sig')
    print("✅ Đã tải và lưu thành công vihealthqa_raw.csv!")
except Exception as e:
    print(f"❌ Vẫn lỗi: {e}")