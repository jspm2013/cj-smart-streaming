from fastapi import Request, HTTPException, status
from passlib.context import CryptContext
from app.core.settings import settings
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        # Hash the plain input first (same as hash_password does)
        digest = hashlib.sha512(plain.encode()).hexdigest()
        return pwd_context.verify(digest, hashed)
    except Exception:
        return False

def hash_password(plain: str) -> str:
    """
    Hashes arbitrary-length secrets safely for bcrypt by
    first reducing them to a fixed 512-bit hex digest.
    This avoids the 72-byte bcrypt limit.
    """
    digest = hashlib.sha512(plain.encode()).hexdigest()
    return pwd_context.hash(digest)

def require_admin_session(request: Request):
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")