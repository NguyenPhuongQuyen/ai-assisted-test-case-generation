from pydantic import BaseModel, ConfigDict, Field


class RequirementCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    module_id: int = Field(gt=0)
    content: str = Field(min_length=20, max_length=50_000)
    acceptance_criteria: str | None = Field(default=None, max_length=20_000)


class RequirementResponse(BaseModel):
    id: int
    module_id: int
    content: str
    acceptance_criteria: str | None
