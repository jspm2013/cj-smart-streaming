from fastapi import APIRouter, Response
from app.services.metrics import REQUEST_COUNTER, ERROR_COUNTER, BYTES_STREAMED, REGISTRY
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(tags=["Health & Metrics"])

@router.get("/healthz")
def healthz():
    return {"status": "ok"}

@router.get("/readyz")
def readyz():
    # here you could check MinIO, DB, Redis connectivity if desired
    return {"status": "ready"}

@router.get("/metrics")
def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)