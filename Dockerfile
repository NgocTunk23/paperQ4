# Sử dụng Python 3.9 để CityFlow hoạt động ổn định nhất
FROM python:3.9-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các công cụ hệ thống cần thiết để biên dịch CityFlow C++
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Sao chép và cài đặt các thư viện Python thông thường từ requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =====================================================================
# VỊ TRÍ SỬA LỖI: CÀI ĐẶT CITYFLOW TRỰC TIẾP TỪ GITHUB
# =====================================================================
# Thay thế lệnh cũ bằng lệnh cài thẳng từ link repository chính thức
RUN pip install --no-cache-dir git+https://github.com/cityflow-project/CityFlow.git

# Sao chép toàn bộ mã nguồn của bạn vào trong container
COPY . .

# Đảm bảo log Python in ra terminal lập tức để tiện theo dõi
ENV PYTHONUNBUFFERED=1

# Mặc định khởi động file runner để điều phối toàn bộ hệ thống
CMD ["python", "runner.py"]