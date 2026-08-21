# Source assistance: OpenAI ChatGPT, 2026-08-21 (AI-05).

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.constants import TestCaseStatus

TagText = Annotated[str, Field(min_length=1, max_length=50)]


class ModuleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=150)
    parent_id: int | None = Field(default=None, ge=1)


class ModuleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=150)
    parent_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def reject_explicit_null_name(self) -> "ModuleUpdateRequest":
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    created_by: int
    created_at: datetime


class ModuleListResponse(BaseModel):
    data: list[ModuleResponse]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")


class TestCaseTagUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tags: list[TagText] = Field(default_factory=list, max_length=10)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for raw_tag in tags:
            tag = raw_tag.strip().lower()
            if not tag or tag in seen:
                continue
            normalized.append(tag)
            seen.add(tag)
        return normalized


class TestCaseTagResponse(BaseModel):
    id: int
    module_id: int
    tags: list[str]


class ModuleCoverageResponse(BaseModel):
    module_id: int = Field(serialization_alias="moduleId")
    total_requirements: int = Field(serialization_alias="totalRequirements")
    covered_requirements: int = Field(serialization_alias="coveredRequirements")
    requirement_coverage_percent: float = Field(serialization_alias="requirementCoveragePercent")
    total_test_cases: int = Field(serialization_alias="totalTestCases")
    approved_test_cases: int = Field(serialization_alias="approvedTestCases")
    status_counts: dict[TestCaseStatus, int] = Field(serialization_alias="statusCounts")
