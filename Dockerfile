# Sử dụng Python phiên bản gọn nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container (main.py và runner.py)
COPY . .

# Đảm bảo log của Python in ra terminal của Docker ngay lập tức (không bị buffer)
ENV PYTHONUNBUFFERED=1

# Chạy file runner để duy trì vòng lặp liên tục
CMD ["python", "runner.py"]