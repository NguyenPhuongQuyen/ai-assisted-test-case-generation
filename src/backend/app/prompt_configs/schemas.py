# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PromptConfigCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    system_prompt: str = Field(min_length=20, max_length=4000)
    user_prompt_template: str = Field(min_length=20, max_length=8000)
    model_name: str = Field(min_length=1, max_length=100)
    schema_version: str = Field(min_length=1, max_length=50)
    max_output_tokens: int = Field(default=4000, ge=256, le=16000)

    @model_validator(mode="after")
    def validate_template_placeholders(self) -> "PromptConfigCreateRequest":
        required = {"{requirement_text}", "{acceptance_criteria}"}
        missing = [placeholder for placeholder in required if placeholder not in self.user_prompt_template]
        if missing:
            raise ValueError("user_prompt_template must include requirement_text and acceptance_criteria placeholders")
        try:
            self.user_prompt_template.format(requirement_text="REQ", acceptance_criteria="AC")
        except (KeyError, ValueError) as exc:
            raise ValueError("user_prompt_template contains invalid or unsupported placeholders") from exc
        return self


class PromptConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_number: int = Field(serialization_alias="versionNumber")
    name: str
    system_prompt: str = Field(serialization_alias="systemPrompt")
    user_prompt_template: str = Field(serialization_alias="userPromptTemplate")
    model_name: str = Field(serialization_alias="modelName")
    schema_version: str = Field(serialization_alias="schemaVersion")
    max_output_tokens: int = Field(serialization_alias="maxOutputTokens")
    is_active: bool = Field(serialization_alias="isActive")
    created_by: int | None = Field(serialization_alias="createdBy")
    created_at: datetime = Field(serialization_alias="createdAt")


class PromptConfigListResponse(BaseModel):
    data: list[PromptConfigResponse]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")
