import os
import sys
from dotenv import load_dotenv
from triage_engine import TriageEngine
from symptom_extractor import SymptomExtractor

# Nạp API Key từ file .env
load_dotenv()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    # 1. Khởi tạo các bộ máy
    try:
        engine = TriageEngine()
        extractor = SymptomExtractor(engine)
    except Exception as e:
        print(f"❌ Không thể khởi tạo hệ thống: {e}")
        return

    clear_screen()
    print("="*60)
    print("🏥 HỆ THỐNG CHATBOT SÀNG LỌC Y TẾ THÔNG MINH (VISION-GUARD)")
    print("      (Kết hợp AI Trích xuất & Suy diễn Chuyên gia)")
    print("="*60)
    print("Hướng dẫn: Nhập triệu chứng của bạn (Ví dụ: 'Tôi bị đau bụng')")
    print("Nhập 'exit' hoặc 'quit' để thoát.")
    print("-"*60)

    while True:
        user_input = input("\n👤 Bệnh nhân: ").strip()

        if user_input.lower() in ['exit', 'quit', 'thoát']:
            print("\n🔌 Đang đóng kết nối... biến đi bạn!")
            break

        if not user_input:
            continue

        print("🔍 Đang phân tích triệu chứng...")
        
        # 2. Bước 1: Trích xuất ID triệu chứng từ văn bản
        try:
            extracted_symptoms = extractor.extract(user_input)
            
            if not extracted_symptoms:
                print("🤖 Bot: Tôi chưa nhận diện được triệu chứng cụ thể. Bạn mô tả kỹ hơn được không?")
                continue

            # In ra các triệu chứng AI đã nhận diện được
            print("✅ AI nhận diện được:", end=" ")
            print(", ".join([f"{s['name']}" for s in extracted_symptoms]))

            # 3. Bước 2: Tính toán Hybrid Score để đưa ra kết luận
            symptom_ids = [s['id'] for s in extracted_symptoms]
            results = engine.hybrid_score(user_input, symptom_ids)

            # 4. Bước 3: Hiển thị kết quả cho người dùng
            if results:
                top_result = results[0]
                print(f"\n🤖 Bot gợi ý: Bạn nên đăng ký khám tại **{top_result['specialty_name']}**")
                print(f"   (Chẩn đoán sơ bộ khả năng cao nhất: {top_result['disease_name']})")
                
                # Hiển thị thêm các lựa chọn phụ nếu điểm số gần bằng nhau
                if len(results) > 1 and results[1]['hybrid_score'] > 0.4:
                    print(f"   (Lựa chọn khác: {results[1]['disease_name']})")
            else:
                print("\n🤖 Bot: Hệ thống chưa tìm thấy bệnh lý tương ứng. Vui lòng gặp lễ tân trực tiếp.")

        except Exception as e:
            print(f"❌ Có lỗi xảy ra trong quá trình xử lý: {e}")

    # Đóng kết nối khi thoát
    engine.close()

if __name__ == "__main__":
    main()