# Source assistance: OpenAI ChatGPT, 2026-08-23 (AI-05).

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.common.constants import ErrorCode, UserRole
from app.common.exceptions import AppError
from app.common.security import decode_access_token


class CurrentUser(BaseModel):
    """Authenticated user identity propagated across application features."""

    id: int
    role: UserRole


bearer_scheme = HTTPBearer(auto_error=False)

CredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


async def get_current_user(
    credentials: CredentialsDep,
) -> CurrentUser:
    """Verify the Bearer JWT at the server boundary (SE-05, SE-07)."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            ErrorCode.UNAUTHORIZED,
            "Bạn chưa cung cấp Bearer token.",
            401,
        )

    try:
        user_id, role = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise AppError(
            ErrorCode.UNAUTHORIZED,
            "Token không hợp lệ hoặc đã hết hạn.",
            401,
        ) from exc

    return CurrentUser(id=user_id, role=role)
