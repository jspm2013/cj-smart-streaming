from minio import Minio
import os
from app.core.settings import settings

def _client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )

def ensure_bucket():
    c = _client()
    if not c.bucket_exists(settings.MINIO_BUCKET):
        c.make_bucket(settings.MINIO_BUCKET)

def upload_dir(local_dir: str, remote_prefix: str):
    c = _client()
    ensure_bucket()
    for root, _, files in os.walk(local_dir):
        for fn in files:
            local_path = os.path.join(root, fn)
            rel = os.path.relpath(local_path, local_dir).replace("\\", "/")
            remote_path = f"{remote_prefix}/{rel}"
            c.fput_object(settings.MINIO_BUCKET, remote_path, local_path)

def get_object_stream(path: str):
    c = _client()
    return c.get_object(settings.MINIO_BUCKET, path)