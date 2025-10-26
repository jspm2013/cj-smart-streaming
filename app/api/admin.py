import uuid, secrets
from fastapi import APIRouter, Request, Depends, UploadFile, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.settings import settings
from app.core.auth import require_admin_session, hash_password, verify_password, SESSION_COOKIE
from app.domain.models import Video, ClientApp
from app.services.hls_service import package_to_hls, upload_hls_dir
from app.services.minio_service import ensure_bucket

templates = Jinja2Templates(directory="web/templates")
router = APIRouter(tags=["Admin"])

# ---------- Login ----------
@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.ADMIN_USER and password == settings.ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    resp = RedirectResponse(url="/admin/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp

# ---------- Dashboard ----------
@router.get("", dependencies=[Depends(require_admin_session)])
def admin_index(request: Request, db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.id.desc()).all()
    apps = db.query(ClientApp).order_by(ClientApp.name.asc()).all()
    return templates.TemplateResponse("videos.html", {"request": request, "videos": videos, "apps": apps, "settings": settings})

# ---------- Upload ----------
@router.get("/upload", dependencies=[Depends(require_admin_session)])
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload", dependencies=[Depends(require_admin_session)])
async def upload_video(file: UploadFile, db: Session = Depends(get_db)):
    data = await file.read()
    ensure_bucket()
    pkg = package_to_hls(data, file.filename or "video.mp4")
    video_id = uuid.uuid4().hex[:16]
    upload_hls_dir(pkg["out_dir"], video_id)
    v = Video(video_id=video_id, filename=file.filename, status="ready", meta=pkg["meta"])
    db.add(v); db.commit()
    return RedirectResponse(url="/admin", status_code=303)

# ---------- Client Apps (API key holders) ----------
@router.get("/client-apps", dependencies=[Depends(require_admin_session)])
def client_apps_page(request: Request, db: Session = Depends(get_db)):
    apps = db.query(ClientApp).order_by(ClientApp.name.asc()).all()
    return templates.TemplateResponse("client-apps.html", {"request": request, "apps": apps})

@router.post("/client-apps", dependencies=[Depends(require_admin_session)])
def create_client_app(name: str = Form(...), api_key: str = Form(...), db: Session = Depends(get_db)):
    if not name or not api_key:
        raise HTTPException(400, "Name and API key required")
    if db.query(ClientApp).filter(ClientApp.name == name).first():
        raise HTTPException(400, "Name exists")
    row = ClientApp(name=name, api_key_hash=hash_password(api_key), active=True)
    db.add(row); db.commit()
    return RedirectResponse(url="/admin/client-apps", status_code=303)

@router.post("/client-apps/{cid}/toggle", dependencies=[Depends(require_admin_session)])
def toggle_client_app(cid: int, db: Session = Depends(get_db)):
    row = db.query(ClientApp).filter(ClientApp.id == cid).first()
    if row: row.active = not row.active; db.commit()
    return RedirectResponse(url="/admin/client-apps", status_code=303)

@router.post("/client-apps/{cid}/delete", dependencies=[Depends(require_admin_session)])
def delete_client_app(cid: int, db: Session = Depends(get_db)):
    db.query(ClientApp).filter(ClientApp.id == cid).delete()
    db.commit()
    return RedirectResponse(url="/admin/client-apps", status_code=303)