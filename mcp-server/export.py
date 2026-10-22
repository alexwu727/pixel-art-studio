from __future__ import annotations
import io
import os
import uuid
from datetime import datetime, timezone

import boto3
import imageio
import psycopg2
from PIL import Image

from canvas import CanvasState


def _s3_client():
    endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
    use_ssl = os.environ.get("MINIO_USE_SSL", "false").lower() == "true"
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if use_ssl else 'http'}://{endpoint}",
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", "pixelart"),
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", "pixelart123"),
    )


def _ensure_bucket(s3, bucket: str) -> None:
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception:
        s3.create_bucket(Bucket=bucket)


def _upload(data: bytes, path: str, content_type: str) -> str:
    bucket = os.environ.get("MINIO_BUCKET", "pixel-art")
    s3 = _s3_client()
    _ensure_bucket(s3, bucket)
    s3.put_object(Bucket=bucket, Key=path, Body=data, ContentType=content_type)
    endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
    use_ssl = os.environ.get("MINIO_USE_SSL", "false").lower() == "true"
    return f"{'https' if use_ssl else 'http'}://{endpoint}/{bucket}/{path}"


def _db_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "pixelart"),
        user=os.environ.get("POSTGRES_USER", "pixelart"),
        password=os.environ.get("POSTGRES_PASSWORD", "pixelart"),
    )


def _upsert_sprite(
    path: str,
    canvas: CanvasState,
    file_type: str,
    tags: list[str],
    created_by: str = "agent",
) -> None:
    name = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    folder = path.rsplit("/", 1)[0] if "/" in path else ""
    frame_count = len(canvas.frames) if file_type == "gif" else 1
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sprites
                    (id, path, name, folder, file_type, width, height,
                     palette, frame_count, tags, created_by, created_at, updated_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (path) DO UPDATE SET
                    name        = EXCLUDED.name,
                    file_type   = EXCLUDED.file_type,
                    width       = EXCLUDED.width,
                    height      = EXCLUDED.height,
                    palette     = EXCLUDED.palette,
                    frame_count = EXCLUDED.frame_count,
                    tags        = EXCLUDED.tags,
                    updated_at  = EXCLUDED.updated_at
                """,
                (
                    str(uuid.uuid4()), path, name, folder, file_type,
                    canvas.width, canvas.height, canvas.palette_name,
                    frame_count, tags, created_by,
                    datetime.now(timezone.utc), datetime.now(timezone.utc),
                ),
            )


def export_png(canvas: CanvasState, path: str, scale: int = 8, tags: list[str] | None = None) -> str:
    img: Image.Image = canvas.to_image(scale)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    url = _upload(buf.getvalue(), path, "image/png")
    _upsert_sprite(path, canvas, "png", tags or [])
    return url


def export_gif(
    canvas: CanvasState,
    path: str,
    frame_delay_ms: int = 150,
    scale: int = 8,
    tags: list[str] | None = None,
) -> str:
    if not canvas.frames:
        raise ValueError("No frames to export. Call add_frame at least once.")
    import numpy as np
    images = canvas.frames_to_images(scale)
    buf = io.BytesIO()
    imageio.mimsave(buf, [np.array(img) for img in images], format="GIF", duration=frame_delay_ms / 1000)
    url = _upload(buf.getvalue(), path, "image/gif")
    _upsert_sprite(path, canvas, "gif", tags or [])
    return url
