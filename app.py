from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from werkzeug.utils import secure_filename
from utils.plate_recognition import process_license_plate_image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)

# Thư mục lưu trữ tải lên
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
HISTORY_FILE = os.path.join(STATIC_FOLDER, 'history.json')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_to_history(result, filename):
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f) if f.read().strip() else []  # Xử lý file trống
        else:
            history = []
    except json.JSONDecodeError:
        history = []  # Nếu file không hợp lệ, khởi tạo lại mảng rỗng

    history.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'plate': result['plate'],
        'confidence': result['score'],
        'image': filename
    })
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

def create_pdf(result, filename):
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f'result_{filename}.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Kết Quả Nhận Diện Biển Số Xe")
    c.drawString(100, 730, f"Biển số: {result['plate']}")
    c.drawString(100, 710, f"Độ tin cậy: {result['score']}%")
    c.drawString(100, 690, f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawImage(os.path.join(app.config['UPLOAD_FOLDER'], filename), 100, 500, width=200, height=150)
    c.save()
    return pdf_path

def send_email(result, email_to):
    email_from = "daoquyjuly@gmail.com"  # Thay bằng email Gmail thực của bạn
    password = "xadkfmejwbpfitqc"   # Thay bằng Mật khẩu ứng dụng (App Password) của bạn
    subject = "Kết Quả Nhận Diện Biển Số Xe"
    body = f"""
    Kết quả nhận diện:
    Biển số: {result['plate']}
    Độ tin cậy: {result['score']}%
    Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_from, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'Không có file được tải lên'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Không có file nào được chọn'})

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            result = process_license_plate_image(filepath, "99fae25675ea6e301e2f8e1be30c01faf97db359")
            if result:
                save_to_history(result, filename)  # Lưu vào lịch sử
                return jsonify({
                    'license_plate': result['plate'],
                    'confidence': result['score'],
                    'success': True
                })
            else:
                return jsonify({
                    'error': 'Không thể nhận dạng biển số',
                    'success': False,
                    'debug': 'Kiểm tra log server để biết chi tiết'
                })

    return render_template('index.html')

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    data = request.get_json()
    result = {'plate': data['plate'], 'score': data['confidence']}
    filename = data['filename']
    pdf_path = create_pdf(result, filename)
    return send_file(pdf_path, as_attachment=True)

@app.route('/send_email', methods=['POST'])
def send_email_result():
    data = request.get_json()
    result = {'plate': data['plate'], 'score': data['confidence']}
    email_to = data['email']
    success = send_email(result, email_to)
    if success:
        return jsonify({'success': True, 'message': 'Email đã được gửi'})
    else:
        return jsonify({'success': False, 'error': 'Lỗi gửi email'})

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f:
            json.dump([], f)
    app.run(debug=True, host='0.0.0.0', port=5000)















