from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import GenerationJobStatus, Priority, TestCaseStatus


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
    review_note: str | None
    status: TestCaseStatus
    created_by: int
    created_at: datetime


class TestCaseListResponse(BaseModel):
    data: list[TestCaseResponse]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")
