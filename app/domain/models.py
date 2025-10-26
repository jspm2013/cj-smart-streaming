from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.core.db import Base

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True)
    video_id = Column(String(40), unique=True, index=True)  # hex id
    filename = Column(String(512))
    status = Column(String(32), default="ready")            # ready | processing | failed
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class ClientApp(Base):
    __tablename__ = "client_apps"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, index=True)
    api_key_hash = Column(String(255))                      # bcrypt hash of API key
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())