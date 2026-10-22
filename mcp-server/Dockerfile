FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MCP_PORT=8001
ENV MINIO_ENDPOINT=minio:9000
ENV MINIO_ACCESS_KEY=pixelart
ENV MINIO_SECRET_KEY=pixelart123
ENV MINIO_BUCKET=pixel-art
ENV MINIO_USE_SSL=false
ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=pixelart
ENV POSTGRES_USER=pixelart
ENV POSTGRES_PASSWORD=pixelart

EXPOSE 8001

CMD ["python", "server.py"]
