import os
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def create_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.utcnow()
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
    }
    secret_key = os.getenv("JWT_SECRET", "change-me-in-local-dev")
    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, str]:
    secret_key = os.getenv("JWT_SECRET", "change-me-in-local-dev")
    try:
        return jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise exc
