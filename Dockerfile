FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo zlib1g libwebp7 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# DATA_DIR is mounted as a persistent volume in production (see fly.toml).
ENV DATA_DIR=/data
ENV UPLOAD_DIR=/data/photos
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "gunicorn --workers=2 --threads=2 --timeout=60 --bind=0.0.0.0:${PORT} app:app"]
