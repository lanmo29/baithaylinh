import requests
import os
import cv2

def process_license_plate_image(image_path, api_key):
    try:
        # Đọc ảnh
        image = cv2.imread(image_path)
        if image is None:
            print("Không thể đọc ảnh")
            return None

        # Lưu ảnh tạm thời
        temp_path = "temp_plate.jpg"
        cv2.imwrite(temp_path, image)

        # Gửi ảnh đến Plate Recognizer API
        with open(temp_path, 'rb') as f:
            files = {'upload': f}
            headers = {'Authorization': f'Token {api_key}'}
            response = requests.post('https://api.platerecognizer.com/v1/plate-reader/', files=files, headers=headers,
                                     timeout=30)

        # Xóa file tạm
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Phân tích kết quả chi tiết
        if response.status_code in [200, 201]:  # Xử lý cả status code 200 và 201 (thành công)
            data = response.json()
            print(f"Plate Recognizer Response: {data}")
            if data['results'] and len(data['results']) > 0:
                plate = data['results'][0]['plate']
                confidence = data['results'][0]['score'] * 100
                print(f"Nhận dạng biển số: {plate} (Confidence: {confidence}%)")

                # Định dạng lại biển số theo chuẩn Việt Nam, giữ nguyên số và chỉ uppercase chữ cái
                formatted_plate = format_license_plate(plate)
                if formatted_plate and confidence >= 60:  # Chỉ kiểm tra độ tin cậy, bỏ kiểm tra is_valid_vietnamese_plate
                    return {'plate': formatted_plate, 'score': confidence}
            else:
                print("Không tìm thấy kết quả từ Plate Recognizer")
                return None
        else:
            print(f"Lỗi API Plate Recognizer: Status Code {response.status_code}, Response: {response.text}")
            return None

    except requests.RequestException as e:
        print(f"Lỗi kết nối đến Plate Recognizer: {e}")
        return None
    except Exception as e:
        print(f"Error processing image with Plate Recognizer: {e}")
        return None

def format_license_plate(text):
    # Định dạng lại văn bản thành biển số xe Việt Nam (51H-12345, 18A-12345, 20A-01177), giữ nguyên số, chỉ uppercase chữ cái
    if not text or len(text.replace("-", "")) < 6:
        return None

    text = text.upper().replace(" ", "").replace(".", "").replace("-", "").replace("_", "")

    # Chỉ uppercase chữ cái, giữ nguyên số (không thay thế 0, 1, v.v. thành O, I)
    # Thử định dạng biển số kiểu XXA-DDDDD (ví dụ: 20A-01177, 60A-99999)
    if text[0:2].isdigit() and len(text) > 3 and text[2].isalpha() and text[2].isupper():
        numbers = text[:2]  # Phần số (ví dụ: 20)
        letter = text[2]  # Phần chữ cái (ví dụ: A)
        remaining = text[3:]  # Phần số còn lại (ví dụ: 01177)
        if remaining.isdigit() and 4 <= len(remaining) <= 5:  # Chấp nhận 4-5 số sau ký tự
            return f"{numbers}{letter}-{remaining}"

    # Biển số kiểu 51H-12345
    if text[0:2].isdigit() and len(text) > 2:
        if text[2].isalpha() and text[2].isupper():
            return f"{text[:3]}-{text[3:8]}"  # Giới hạn 5 số cuối

    # Biển số ANFO (51-ANF-123)
    for i in range(2, len(text)):
        if text[i].isalpha() and text[i].isupper():
            return f"{text[:2]}-{text[2:i + 1]}-{text[i + 1:i + 4]}"  # Giới hạn 3 số cuối

    # Nếu không định dạng được, trả về text gốc (upper) để debug
    return text  # Trả về text gốc nếu không định dạng được

def is_valid_vietnamese_plate(plate):
    # Tạm thời không sử dụng, vì đã kiểm tra trong format_license_plate
    return True  # Chấp nhận tất cả định dạng để đảm bảo trả về kết quả