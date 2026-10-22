import os
import boto3
from botocore.client import Config

_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9090")
_ACCESS   = os.getenv("MINIO_ACCESS_KEY", "test")
_SECRET   = os.getenv("MINIO_SECRET_KEY", "testtest")
_BUCKET   = os.getenv("MINIO_BUCKET", "pixel-art")
_USE_SSL  = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

_scheme = "https" if _USE_SSL else "http"

_s3 = boto3.client(
    "s3",
    endpoint_url=f"{_scheme}://{_ENDPOINT}",
    aws_access_key_id=_ACCESS,
    aws_secret_access_key=_SECRET,
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    region_name="us-east-1",
)


def _ensure_bucket() -> None:
    try:
        _s3.head_bucket(Bucket=_BUCKET)
    except Exception:
        _s3.create_bucket(Bucket=_BUCKET)


def upload_file(data: bytes, path: str, content_type: str = "image/png") -> str:
    import io
    _ensure_bucket()
    _s3.upload_fileobj(
        io.BytesIO(data),
        _BUCKET,
        path,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{_scheme}://{_ENDPOINT}/{_BUCKET}/{path}"


def download_file(path: str) -> bytes:
    import io
    buf = io.BytesIO()
    _s3.download_fileobj(_BUCKET, path, buf)
    return buf.getvalue()


def delete_file(path: str):
    _s3.delete_object(Bucket=_BUCKET, Key=path)


def get_presigned_url(path: str, expires: int = 3600) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": _BUCKET, "Key": path},
        ExpiresIn=expires,
    )
