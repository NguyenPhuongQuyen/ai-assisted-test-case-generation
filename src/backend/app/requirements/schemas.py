from pydantic import BaseModel, ConfigDict, Field, model_validator


class RequirementCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    module_id: int = Field(gt=0)
    content: str = Field(min_length=20, max_length=50_000)
    acceptance_criteria: str | None = Field(default=None, max_length=20_000)


class RequirementUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    lock_version: int = Field(ge=1)
    content: str | None = Field(default=None, min_length=20, max_length=50_000)
    acceptance_criteria: str | None = Field(default=None, max_length=20_000)

    @model_validator(mode="after")
    def require_mutable_field(self) -> "RequirementUpdate":
        if not (self.model_fields_set - {"lock_version"}):
            raise ValueError("At least one mutable field is required")
        return self


class RequirementResponse(BaseModel):
    id: int
    module_id: int
    content: str
    acceptance_criteria: str | None
    lock_version: int


class RequirementListResponse(BaseModel):
    data: list[RequirementResponse]
    page: int
    page_size: int
    total: int
