from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.core.db import engine, Base
from app.core.settings import settings
from app.api import router as api_router

# ---------- Setup Logging ----------
setup_logging()

# ---------- Create App ----------
app = FastAPI(title="#Codejobs HLS Streamer")

# ---------- Global CORS (allow all origins) ----------
# This only affects browser security model, not your JWT authorization.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ✅ allow any origin
    allow_credentials=True,       # needed if you later use cookies/sessions
    allow_methods=["*"],          # allow all HTTP verbs
    allow_headers=["*"],          # allow any headers (Authorization, etc.)
)

# ---------- Session Middleware ----------
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie=settings.SESSION_COOKIE,
    https_only=settings.SESSION_COOKIE_SECURE,
)

# ---------- Routers ----------
app.include_router(api_router)

# ---------- Static + Templates ----------
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

# ---------- Startup ----------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)