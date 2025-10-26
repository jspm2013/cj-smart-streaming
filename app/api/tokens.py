import time, jwt
from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.db import get_db
from app.core.settings import settings
from app.core.auth import verify_password
from app.domain.models import ClientApp
from app.domain.schemas import TokenOut

router = APIRouter(tags=["Tokens"])

class TokenRequest(BaseModel):
    video_id: str                 # token is constrained to this video
    origin: str                   # e.g. "https://client-site.com"

@router.post("/token", response_model=TokenOut)
def issue_token(
    req: TokenRequest,
    x_app_key: str = Header(None),
    x_app_name: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Per-domain-key issuance:
    - Client partner backend calls this endpoint (NOT from the browser)
      with its X-App-Name / X-App-Key and the domain it will serve from.
    - We mint a short-lived JWT that embeds that domain in the 'orig' claim.
    - The browser only ever sees this JWT; no app keys are exposed client-side.
    """
    if not x_app_name or not x_app_key:
        raise HTTPException(401, "Missing app credentials")

    app = (
        db.query(ClientApp)
        .filter(ClientApp.name == x_app_name, ClientApp.active == True)  # noqa: E712
        .first()
    )
    if not app or not verify_password(x_app_key, app.api_key_hash):
        raise HTTPException(401, "Invalid app credentials")

    # Basic origin sanity (very light; full validation can be added upstream)
    origin = req.origin.strip()
    if not (origin.startswith("https://") or origin.startswith("http://")):
        raise HTTPException(400, "origin must start with http:// or https://")

    now = int(time.time())
    exp = now + settings.TOKEN_TTL_SECONDS
    payload = {
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "exp": exp,
        "vid": req.video_id,   # constrain to video
        "orig": origin,        # constrain to this exact origin
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return {"token": token, "expires_in": settings.TOKEN_TTL_SECONDS}