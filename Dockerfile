FROM python:3.10-slim

WORKDIR /app

# Copy và cài đặt thư viện trước để tối ưu cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code (api.py, sync_real_data.py) và .env vào
COPY . .

# Mở cổng 8000
EXPOSE 8000

# Lệnh chạy API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]