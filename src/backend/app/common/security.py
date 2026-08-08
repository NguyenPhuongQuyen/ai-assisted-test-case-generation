from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.common.config import get_settings
from app.common.constants import UserRole

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt cost 12; SE-02 requires bcrypt cost >= 10."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int, role: UserRole) -> str:
    """Create a short-lived JWT containing only non-sensitive identity and role claims."""
    expire_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "role": role.value, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> tuple[int, UserRole]:
    """Validate JWT signature/expiry and return user identity and role."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"]), UserRole(payload["role"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise ValueError("invalid access token") from exc
