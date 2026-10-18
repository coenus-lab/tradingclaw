import base64
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from hashlib import sha256
from hmac import HMAC

from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.entities import User

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_token(subject: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode({"sub": subject, "exp": exp}, settings.jwt_secret, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token") from exc
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or inactive user")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin access required")
    return current_user


@lru_cache
def get_fernet() -> Fernet:
    return Fernet(settings.encryption_key.encode())


def encrypt_secret(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    return get_fernet().decrypt(value.encode()).decode()


def kraken_authent(endpoint_path: str, post_body: str, nonce: str, api_secret: str) -> str:
    msg = (post_body + nonce + endpoint_path).encode()
    digest = sha256(msg).digest()
    signature = HMAC(base64.b64decode(api_secret), digest, sha256).digest()
    return base64.b64encode(signature).decode()
