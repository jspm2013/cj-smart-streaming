from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.core.logging import setup_logging
from app.core.db import engine, Base
from app.core.settings import settings
from app.api import router as api_router

setup_logging()

app = FastAPI(title="MinIO HLS Streamer")
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET, session_cookie="admin_session")

app.include_router(api_router)

app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)