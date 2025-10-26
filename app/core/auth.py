from fastapi import Request, HTTPException, status
from passlib.context import CryptContext
import hashlib

# Explicit bcrypt setup; pre-load backend once at import
pwd_context = CryptContext(
    schemes=["bcrypt"],
    bcrypt__rounds=12,
    deprecated="auto",
)

# Warm-up: run one harmless hash to initialize backend safely
_pwd_warmup = pwd_context.hash("init")

def _normalize_secret(secret: str) -> str:
    """
    Pre-hash arbitrary-length secrets to a fixed-size SHA-256 hex digest (64 chars).
    This ensures bcrypt input <= 72 bytes and prevents encoding issues.
    """
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()

def hash_password(plain: str) -> str:
    """
    Hashes secrets of any length safely by pre-hashing with SHA-256 before bcrypt.
    """
    normalized = _normalize_secret(plain)
    return pwd_context.hash(normalized)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies a secret by pre-hashing with SHA-256 and comparing with bcrypt hash.
    """
    try:
        normalized = _normalize_secret(plain)
        return pwd_context.verify(normalized, hashed)
    except Exception:
        return False

def require_admin_session(request: Request):
    if not request.session.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )