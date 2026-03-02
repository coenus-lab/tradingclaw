import base64
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from hmac import HMAC
from typing import Optional

from cryptography.fernet import Fernet
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_token(subject: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode({"sub": subject, "exp": exp}, settings.jwt_secret, algorithm="HS256")


def get_fernet() -> Fernet:
    if settings.encryption_key:
        key = settings.encryption_key.encode()
    else:
        key = Fernet.generate_key()
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    return get_fernet().decrypt(value.encode()).decode()


def kraken_authent(endpoint_path: str, post_body: str, nonce: str, api_secret: str) -> str:
    msg = (post_body + nonce + endpoint_path).encode()
    digest = sha256(msg).digest()
    signature = HMAC(base64.b64decode(api_secret), digest, sha256).digest()
    return base64.b64encode(signature).decode()
