import redis
from rq import Queue
from fastapi import (
    APIRouter, Request, Depends, UploadFile, Form,
    HTTPException
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.settings import settings
from app.core.auth import require_admin_session, hash_password
from app.domain.models import Video, ClientApp
from app.services.minio_service import ensure_bucket, delete_prefix
from app.services.metrics import REQUEST_COUNTER, ERROR_COUNTER
from app.workers.tasks import package_and_upload_video

templates = Jinja2Templates(directory="web/templates")
router = APIRouter(tags=["Admin"])

# ---------- Redis Queue ----------
redis_conn = redis.from_url(settings.REDIS_URL)
q = Queue("default", connection=redis_conn)

# ---------- Login ----------
@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.ADMIN_USER and password == settings.ADMIN_PASSWORD:
        request.session["is_admin"] = True
        REQUEST_COUNTER.labels(endpoint="/admin/login", method="POST", status="200").inc()
        return RedirectResponse(url="/admin", status_code=303)
    ERROR_COUNTER.labels(endpoint="/admin/login").inc()
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"},
        status_code=401,
    )


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    resp = RedirectResponse(url="/admin/login", status_code=303)
    resp.delete_cookie(settings.SESSION_COOKIE)
    return resp


# ---------- Dashboard ----------
@router.get("", dependencies=[Depends(require_admin_session)])
def admin_index(request: Request, db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.id.desc()).all()
    apps = db.query(ClientApp).order_by(ClientApp.name.asc()).all()
    REQUEST_COUNTER.labels(endpoint="/admin", method="GET", status="200").inc()
    return templates.TemplateResponse(
        "videos.html",
        {"request": request, "videos": videos, "apps": apps, "settings": settings},
    )


# ---------- Upload ----------
@router.get("/upload", dependencies=[Depends(require_admin_session)])
def upload_page(request: Request):
    REQUEST_COUNTER.labels(endpoint="/admin/upload", method="GET", status="200").inc()
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("/upload", dependencies=[Depends(require_admin_session)])
async def upload_video(file: UploadFile, request: Request):
    """
    Uploads file, enqueues packaging task to Redis RQ worker.
    """
    ensure_bucket()
    data = await file.read()
    job = q.enqueue(package_and_upload_video, data, file.filename)
    REQUEST_COUNTER.labels(endpoint="/admin/upload", method="POST", status="202").inc()
    print(f"📦 Enqueued packaging job {job.id} for {file.filename}")
    return RedirectResponse(url="/admin/jobs", status_code=303)


# ---------- Jobs Dashboard ----------
@router.get("/jobs", dependencies=[Depends(require_admin_session)])
def jobs_page(request: Request):
    """
    Displays simple job list (latest 20 jobs from RQ).
    """
    REQUEST_COUNTER.labels(endpoint="/admin/jobs", method="GET", status="200").inc()
    jobs = []
    for j in q.jobs[:20]:
        jobs.append({
            "id": j.id,
            "status": j.get_status(refresh=False),
            "enqueued_at": getattr(j.enqueued_at, "isoformat", lambda: "")(),
            "result": j.result,
        })
    return templates.TemplateResponse(
        "jobs.html", {"request": request, "jobs": jobs}
    )


# ---------- Delete Video ----------
@router.post("/videos/{video_id}/delete", dependencies=[Depends(require_admin_session)])
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """
    Deletes a video record and its associated MinIO files.
    """
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        delete_prefix(video.video_id)  # remove from MinIO
        db.delete(video)
        db.commit()
        REQUEST_COUNTER.labels(endpoint="/admin/videos/delete", method="POST", status="200").inc()
    except Exception as e:
        db.rollback()
        ERROR_COUNTER.labels(endpoint="/admin/videos/delete").inc()
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")

    return RedirectResponse(url="/admin", status_code=303)


# ---------- Client Apps (API key holders) ----------
@router.get("/client-apps", dependencies=[Depends(require_admin_session)])
def client_apps_page(request: Request, db: Session = Depends(get_db)):
    apps = db.query(ClientApp).order_by(ClientApp.name.asc()).all()
    REQUEST_COUNTER.labels(endpoint="/admin/client-apps", method="GET", status="200").inc()
    return templates.TemplateResponse("client-apps.html", {"request": request, "apps": apps})


@router.post("/client-apps", dependencies=[Depends(require_admin_session)])
def create_client_app(name: str = Form(...), api_key: str = Form(...), db: Session = Depends(get_db)):
    if not name or not api_key:
        ERROR_COUNTER.labels(endpoint="/admin/client-apps").inc()
        raise HTTPException(400, "Name and API key required")

    if db.query(ClientApp).filter(ClientApp.name == name).first():
        raise HTTPException(400, "Name already exists")

    row = ClientApp(name=name, api_key_hash=hash_password(api_key), active=True)
    db.add(row)
    db.commit()
    REQUEST_COUNTER.labels(endpoint="/admin/client-apps", method="POST", status="201").inc()
    return RedirectResponse(url="/admin/client-apps", status_code=303)


@router.post("/client-apps/{cid}/toggle", dependencies=[Depends(require_admin_session)])
def toggle_client_app(cid: int, db: Session = Depends(get_db)):
    row = db.query(ClientApp).filter(ClientApp.id == cid).first()
    if row:
        row.active = not row.active
        db.commit()
        REQUEST_COUNTER.labels(endpoint="/admin/client-apps/toggle", method="POST", status="200").inc()
    return RedirectResponse(url="/admin/client-apps", status_code=303)


@router.post("/client-apps/{cid}/delete", dependencies=[Depends(require_admin_session)])
def delete_client_app(cid: int, db: Session = Depends(get_db)):
    db.query(ClientApp).filter(ClientApp.id == cid).delete()
    db.commit()
    REQUEST_COUNTER.labels(endpoint="/admin/client-apps/delete", method="POST", status="200").inc()
    return RedirectResponse(url="/admin/client-apps", status_code=303)