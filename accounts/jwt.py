import jwt
import uuid
from datetime import datetime, timezone
from django.conf import settings

def _now():
    return datetime.now(timezone.utc)

def create_access_token(user_id: int):
    iat = _now()
    exp = iat + settings.JWT_ACCESS_TTL
    payload = {"sub": str(user_id), "typ": "access", "iat": int(iat.timestamp()), "exp": int(exp.timestamp())}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def create_refresh_token(user_id: int, jti: uuid.UUID | None = None):
    iat = _now()
    exp = iat + settings.JWT_REFRESH_TTL
    jti = jti or uuid.uuid4()
    payload = {"sub": str(user_id), "typ": "refresh", "jti": str(jti), "iat": int(iat.timestamp()), "exp": int(exp.timestamp())}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti, exp

def decode_token(token: str, expected_typ: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise ValueError("TOKEN_INVALID")

    if payload.get("typ") != expected_typ:
        raise ValueError("WRONG_TOKEN_TYPE")
    return payload
