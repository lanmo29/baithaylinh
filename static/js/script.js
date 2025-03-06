document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('file-upload');
    const resultDiv = document.getElementById('result');
    const previewDiv = document.getElementById('preview');
    const loadingDiv = document.getElementById('loading');
    const recognizeBtn = document.getElementById('recognize-btn');

    if (fileInput.files.length === 0) {
        resultDiv.innerHTML = '<p class="text-red-500">Vui lòng chọn ảnh</p>';
        return;
    }

    // Preview image
    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = function(e) {
        previewDiv.innerHTML = `<img src="${e.target.result}" alt="Preview" class="preview-image">`;
    };
    reader.readAsDataURL(file);

    // Show loading spinner
    loadingDiv.classList.remove('hidden');
    recognizeBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const startTime = performance.now();

    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const endTime = performance.now();
        const processingTime = ((endTime - startTime) / 1000).toFixed(2);

        loadingDiv.classList.add('hidden');
        recognizeBtn.disabled = false;

        if (data.success) {
            const confidence = data.confidence ? ` (Độ tin cậy: ${data.confidence.toFixed(1)}%)` : '';
            resultDiv.innerHTML = `
                <div class="result-success p-4 rounded-lg">
                    <p class="text-lg font-semibold">Biển Số: ${data.license_plate || 'Không rõ'}</p>
                    <p class="text-sm text-green-700">Thành công${confidence} - Thời gian xử lý: ${processingTime}s</p>
                    <div class="mt-4 space-x-2">
                        <button id="download-pdf" class="bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600">Tải PDF</button>
                        <input id="email-input" type="email" placeholder="Nhập email" class="p-2 border rounded-lg">
                        <button id="send-email" class="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600">Gửi Email</button>
                    </div>
                </div>`;

            // Download PDF
            document.getElementById('download-pdf').addEventListener('click', () => {
                fetch('/download_pdf', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ plate: data.license_plate, confidence: data.confidence, filename: file.name })
                })
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `result_${file.name}.pdf`;
                    a.click();
                });
            });

            // Send email
            document.getElementById('send-email').addEventListener('click', () => {
                const email = document.getElementById('email-input').value;
                if (!email) {
                    alert('Vui lòng nhập email');
                    return;
                }
                fetch('/send_email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ plate: data.license_plate, confidence: data.confidence, email: email })
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        alert('Email đã được gửi thành công!');
                    } else {
                        alert('Lỗi gửi email: ' + result.error);
                    }
                });
            });
        } else {
            resultDiv.innerHTML = `
                <div class="result-error p-4 rounded-lg">
                    <p class="text-lg font-semibold">Lỗi: ${data.error || 'Không thể nhận dạng'}</p>
                    <p class="text-sm text-red-700">${data.debug || ''} - Thời gian xử lý: ${processingTime}s</p>
                </div>`;
        }
    })
    .catch(error => {
        loadingDiv.classList.add('hidden');
        recognizeBtn.disabled = false;
        resultDiv.innerHTML = `
            <div class="result-error p-4 rounded-lg">
                <p class="text-lg font-semibold">Lỗi xử lý: Vui lòng thử lại</p>
                <p class="text-sm text-red-700">Chi tiết: ${error.message}</p>
            </div>`;
        console.error('Lỗi:', error);
    });
});

// Reset button
document.getElementById('reset-btn').addEventListener('click', function() {
    const fileInput = document.getElementById('file-upload');
    const resultDiv = document.getElementById('result');
    const previewDiv = document.getElementById('preview');
    const recognizeBtn = document.getElementById('recognize-btn');

    fileInput.value = '';
    resultDiv.innerHTML = '';
    previewDiv.innerHTML = '';
    recognizeBtn.disabled = true;
});

// Enable/disable recognize button
document.getElementById('file-upload').addEventListener('change', function() {
    const recognizeBtn = document.getElementById('recognize-btn');
    recognizeBtn.disabled = this.files.length === 0;
});

// History button
document.getElementById('history-btn').addEventListener('click', function() {
    const modal = document.getElementById('history-modal');
    const content = document.getElementById('history-content');
    fetch('/static/history.json')
        .then(response => response.json())
        .then(data => {
            content.innerHTML = data.length > 0 ?
                data.map(item => `
                    <div class="p-2 border-b">
                        <p><strong>Thời gian:</strong> ${item.timestamp}</p>
                        <p><strong>Biển số:</strong> ${item.plate}</p>
                        <p><strong>Độ tin cậy:</strong> ${item.confidence}%</p>
                        <img src="/uploads/${item.image}" alt="History Image" class="w-32 h-auto mt-2">
                    </div>
                `).join('') : '<p>Chưa có lịch sử nhận diện.</p>';
            modal.classList.remove('hidden');
        });
});

// Close history modal
document.getElementById('close-history').addEventListener('click', function() {
    document.getElementById('history-modal').classList.add('hidden');
});