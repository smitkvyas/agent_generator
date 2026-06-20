FROM python:3.12-slim

WORKDIR /app

# system deps (needed for faiss / sentence-transformers)
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    zlib1g-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8686

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8686", "--reload"]