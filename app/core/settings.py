import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- Admin Auth ---
    ADMIN_USER: str = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme")
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "please-change")
    SESSION_COOKIE: str = os.getenv("SESSION_COOKIE", "admin_session")
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./stream.db")

    # --- Redis Queue ---
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # --- MinIO (internal/private) ---
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "videos")

    # --- HLS packaging ---
    HLS_SEGMENT_SECONDS: int = int(os.getenv("HLS_SEGMENT_SECONDS", "4"))
    HLS_VARIANTS: str = os.getenv(
        "HLS_VARIANTS",
        "426x240_400k,640x360_800k,842x480_1200k,1280x720_2500k"
    )

    # --- JWT for streaming (per-domain tokens) ---
    JWT_SECRET: str = os.getenv("JWT_SECRET", "please-change-me")
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "minio-hls-streamer")
    JWT_AUDIENCE: str = os.getenv("JWT_AUDIENCE", "video-stream")
    TOKEN_TTL_SECONDS: int = int(os.getenv("TOKEN_TTL_SECONDS", "900"))

    # --- Cache headers ---
    CACHE_MAX_AGE: int = int(os.getenv("CACHE_MAX_AGE", "60"))

settings = Settings()