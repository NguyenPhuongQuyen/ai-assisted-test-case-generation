from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.constants import UserRole


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: UserRole


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
