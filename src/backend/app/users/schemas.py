# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.common.constants import UserRole


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: UserRole


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=10, max_length=128)
    role: UserRole | None = None
    is_active: bool | None = Field(default=None, serialization_alias="isActive")

    @model_validator(mode="after")
    def require_change(self) -> "UserUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one user field must be provided")
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
    is_active: bool = Field(serialization_alias="isActive")


class UserListResponse(BaseModel):
    data: list[UserResponse]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")
