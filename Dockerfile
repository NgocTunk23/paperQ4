FROM python:3.9-slim-bullseye

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SUMO_HOME=/usr/share/sumo

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

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git+https://github.com/cityflow-project/CityFlow.git && \
    pip install sumolib

RUN wget -O converter.py https://raw.githubusercontent.com/cityflow-project/CityFlow/master/tools/converter/converter.py

COPY . .

EXPOSE 8000

CMD ["python", "runner.py", "--scenario", "scenarios/area_all.json"]