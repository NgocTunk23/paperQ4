# Sử dụng Python 3.9 để CityFlow hoạt động ổn định nhất
FROM python:3.9-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các công cụ hệ thống, wget, và SUMO
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    sumo \
    sumo-tools \
    && rm -rf /var/lib/apt/lists/*

# BỔ SUNG DÒNG NÀY: Thiết lập biến môi trường bắt buộc cho SUMO
ENV SUMO_HOME=/usr/share/sumo

# Sao chép và cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt CityFlow và thư viện sumolib (bắt buộc cho converter)
RUN pip install --no-cache-dir git+https://github.com/cityflow-project/CityFlow.git
RUN pip install --no-cache-dir sumolib

# Tải công cụ chuyển đổi định dạng chuẩn trực tiếp từ CityFlow Github
RUN wget -O converter.py https://raw.githubusercontent.com/cityflow-project/CityFlow/master/tools/converter/converter.py

# Sao chép toàn bộ mã nguồn của bạn vào trong container
COPY . .

# Đảm bảo log Python in ra terminal lập tức để tiện theo dõi
ENV PYTHONUNBUFFERED=1

# Mặc định khởi động file runner để điều phối toàn bộ hệ thống
CMD ["python", "runner.py"]