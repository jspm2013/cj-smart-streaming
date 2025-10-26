from pydantic import BaseModel
from typing import Dict

class VideoOut(BaseModel):
    video_id: str
    filename: str
    status: str
    meta: Dict | None = None

class TokenOut(BaseModel):
    token: str
    expires_in: int