FROM python:3.9-slim-bullseye

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SUMO_HOME=/usr/share/sumo

# Cài đặt các thư viện hệ thống và SUMO
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    procps \
    sumo \
    sumo-tools \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt các gói Python và CityFlow
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git+https://github.com/cityflow-project/CityFlow.git && \
    pip install sumolib

# Tải converter.py của CityFlow
RUN wget -O converter.py https://raw.githubusercontent.com/cityflow-project/CityFlow/master/tools/converter/converter.py

# Copy toàn bộ source code
COPY . .

EXPOSE 8000

# Chạy pipeline tổng hợp (Sinh A, Z và chạy CityFlow) thay vì chỉ runner.py
CMD ["python", "run_pipeline.py"]FROM python:3.9-slim-bullseye

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SUMO_HOME=/usr/share/sumo

# Cài đặt các thư viện hệ thống và SUMO
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    procps \
    sumo \
    sumo-tools \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt các gói Python và CityFlow
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git+https://github.com/cityflow-project/CityFlow.git && \
    pip install sumolib

# Tải converter.py của CityFlow
RUN wget -O converter.py https://raw.githubusercontent.com/cityflow-project/CityFlow/master/tools/converter/converter.py

# Copy toàn bộ source code
COPY . .

EXPOSE 8000

# Chạy pipeline tổng hợp (Sinh A, Z và chạy CityFlow) thay vì chỉ runner.py
CMD ["python", "run_pipeline.py"]