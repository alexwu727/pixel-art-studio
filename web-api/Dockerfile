FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MINIO_ENDPOINT=minio:9090
ENV MINIO_ACCESS_KEY=test
ENV MINIO_SECRET_KEY=testtest
ENV MINIO_BUCKET=pixel-art
ENV MINIO_USE_SSL=false
ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=pixelart
ENV POSTGRES_USER=pixelart
ENV POSTGRES_PASSWORD=pixelart

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
