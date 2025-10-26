import uuid
from rq import get_current_job
from app.services.hls_service import package_to_hls, upload_hls_dir
from app.services.minio_service import ensure_bucket
from app.core.db import SessionLocal
from app.domain.models import Video

def package_and_upload_video(file_bytes: bytes, filename: str):
    """Background RQ task: package MP4 → HLS → upload → update DB."""
    job = get_current_job()
    db = SessionLocal()
    try:
        ensure_bucket()
        pkg = package_to_hls(file_bytes, filename)
        video_id = uuid.uuid4().hex[:16]
        upload_hls_dir(pkg["out_dir"], video_id)
        v = Video(video_id=video_id, filename=filename, status="ready", meta=pkg["meta"])
        db.add(v); db.commit()
        return {"video_id": video_id, "status": "ready"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()