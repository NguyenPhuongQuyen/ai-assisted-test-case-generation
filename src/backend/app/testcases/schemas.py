from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.constants import GenerationJobStatus, Priority, TestCaseStatus

ShortText = Annotated[str, Field(min_length=1, max_length=500)]
TechniqueText = Annotated[str, Field(min_length=1, max_length=100)]


class GeneratedTestCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=3, max_length=300)
    preconditions: list[str] = Field(default_factory=list, max_length=20)
    steps: list[str] = Field(min_length=1, max_length=30)
    expected_result: str = Field(min_length=3, max_length=1000)
    priority: Priority
    test_techniques: list[str] = Field(default_factory=list, max_length=10)
    review_note: str | None = Field(default=None, max_length=1000)


class GeneratedTestCaseBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_cases: list[GeneratedTestCase] = Field(min_length=1, max_length=50)


class GenerationJobResponse(BaseModel):
    id: int
    requirement_id: int
    status: GenerationJobStatus
    error_code: str | None


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requirement_id: int
    module_id: int
    summary: str
    preconditions: list[str]
    steps: list[str]
    expected_result: str
    priority: Priority
    test_techniques: list[str]
    tags: list[str]
    review_note: str | None
    status: TestCaseStatus
    lock_version: int
    created_by: int
    created_at: datetime


class TestCaseListResponse(BaseModel):
    data: list[TestCaseResponse]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")


class TestCaseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    lock_version: int = Field(ge=1)
    summary: str | None = Field(default=None, min_length=3, max_length=300)
    preconditions: list[ShortText] | None = Field(default=None, max_length=20)
    steps: list[ShortText] | None = Field(default=None, min_length=1, max_length=30)
    expected_result: str | None = Field(default=None, min_length=3, max_length=1000)
    priority: Priority | None = None
    test_techniques: list[TechniqueText] | None = Field(default=None, max_length=10)
    review_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def reject_null_for_non_nullable_fields(self) -> "TestCaseUpdateRequest":
        nullable_fields = {"review_note"}
        for field_name in self.model_fields_set - nullable_fields:
            if field_name != "lock_version" and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class ReviewTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lock_version: int = Field(ge=1)


class ReviewDecisionRequest(ReviewTransitionRequest):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    review_note: str | None = Field(default=None, max_length=1000)


class DuplicateCandidateResponse(BaseModel):
    id: int
    requirement_id: int
    summary: str
    status: TestCaseStatus
    priority: Priority
    similarity: float = Field(ge=0.0, le=1.0)


class DuplicateCandidateListResponse(BaseModel):
    data: list[DuplicateCandidateResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(serialization_alias="pageSize", ge=1)
    threshold: float = Field(ge=0.0, le=1.0)
    embedding_model: str = Field(serialization_alias="embeddingModel")
    embedding_dimensions: int = Field(serialization_alias="embeddingDimensions")


class TestCaseVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_number: int = Field(serialization_alias="versionNumber")
    snapshot: dict
    created_by: int = Field(serialization_alias="createdBy")
    created_at: datetime = Field(serialization_alias="createdAt")


class TestCaseVersionListResponse(BaseModel):
    data: list[TestCaseVersionResponse]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")


class TestCaseVersionCompareResponse(BaseModel):
    from_version: int = Field(serialization_alias="fromVersion")
    to_version: int = Field(serialization_alias="toVersion")
    changes: dict[str, dict[str, object]]


class TestCaseVersionRestoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lock_version: int = Field(ge=1)
