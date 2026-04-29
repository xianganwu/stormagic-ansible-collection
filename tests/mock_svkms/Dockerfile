FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /certs && \
    openssl req -x509 -newkey rsa:2048 \
    -keyout /certs/server.key -out /certs/server.crt \
    -days 365 -nodes \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

EXPOSE 1443

CMD ["python", "app.py"]
