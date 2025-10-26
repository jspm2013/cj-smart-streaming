from fastapi import Request, HTTPException, status
from passlib.context import CryptContext
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _normalize_secret(secret: str) -> bytes:
    """
    Reduce arbitrarily long secrets to a fixed-size 32-byte digest (SHA-256 binary).
    This ensures bcrypt input <= 72 bytes while keeping strong entropy.
    """
    return hashlib.sha256(secret.encode()).digest()

def verify_password(plain: str, hashed: str) -> bool:
    try:
        normalized = _normalize_secret(plain)
        return pwd_context.verify(normalized, hashed)
    except Exception:
        return False

def hash_password(plain: str) -> str:
    """
    Hashes secrets of any length safely by pre-hashing with SHA-256 before bcrypt.
    """
    normalized = _normalize_secret(plain)
    return pwd_context.hash(normalized)

def require_admin_session(request: Request):
    if not request.session.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )