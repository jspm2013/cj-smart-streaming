from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text
import redis

from app.core.db import engine
from app.core.settings import settings
from app.services.minio_service import _client
from app.services.metrics import REQUEST_COUNTER, ERROR_COUNTER, BYTES_STREAMED, REGISTRY

router = APIRouter(tags=["Health & Metrics"])


@router.get("/healthz")
def healthz():
    """Simple liveness check (no dependencies)."""
    return {"status": "ok"}


@router.get("/readyz")
def readyz():
    """
    Readiness probe — verifies connections to DB, Redis, and MinIO.
    Returns detailed component status + overall ready flag.
    """
    results = {"database": False, "redis": False, "minio": False}
    errors = {}

    # --- DB Check ---
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        results["database"] = True
    except Exception as e:
        errors["database"] = str(e)

    # --- Redis Check ---
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        results["redis"] = True
    except Exception as e:
        errors["redis"] = str(e)

    # --- MinIO Check ---
    try:
        c = _client()
        # Lightweight call to ensure connectivity
        c.list_buckets()
        results["minio"] = True
    except Exception as e:
        errors["minio"] = str(e)

    # --- Aggregate status ---
    all_ok = all(results.values())
    status_code = 200 if all_ok else 503
    overall = "ready" if all_ok else "degraded"

    return Response(
        content=str({
            "status": overall,
            "components": results,
            "errors": errors
        }),
        media_type="application/json",
        status_code=status_code
    )


@router.get("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)