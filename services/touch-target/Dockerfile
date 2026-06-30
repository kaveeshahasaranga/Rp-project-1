FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y wget gnupg curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps chromium
COPY . .
EXPOSE 8002
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8002", "-t", "120", "app:app"]
