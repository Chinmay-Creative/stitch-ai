FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
  libgl1 libglib2.0-0 libgomp1 \
  && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p uploads outputs feedback ml/training ml/models demo_images
EXPOSE 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
