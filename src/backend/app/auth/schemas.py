from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.auth_context import CurrentUser as CurrentUser
from app.common.constants import AUTH_SCHEME_BEARER
from app.users.schemas import UserResponse


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = AUTH_SCHEME_BEARER
    user: UserResponse
