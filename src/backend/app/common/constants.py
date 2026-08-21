from enum import StrEnum

AUTH_SCHEME_BEARER = "bearer"
AI_GENERATION_QUEUE = "ai-generation"
GENERATION_TASK_NAME = "testcases.generate"
EMBEDDING_DIMENSIONS = 1536


class UserRole(StrEnum):
    QA = "qa"
    MANAGER = "manager"
    ADMIN = "admin"


class TestCaseStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    NEEDS_FIX = "needs_fix"
    APPROVED = "approved"
    EXPORTED = "exported"
    REJECTED = "rejected"


class GenerationJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AuditAction(StrEnum):
    GENERATE_TEST_CASES = "generate_test_cases"
    EDIT_TEST_CASE = "edit_test_case"
    SUBMIT_TEST_CASE_REVIEW = "submit_test_case_review"
    REQUEST_TEST_CASE_FIX = "request_test_case_fix"
    APPROVE_TEST_CASE = "approve_test_case"
    REJECT_TEST_CASE = "reject_test_case"


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN_ROLE = "FORBIDDEN_ROLE"
    FORBIDDEN_RECORD = "FORBIDDEN_RECORD"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    MODULE_NOT_FOUND = "MODULE_NOT_FOUND"
    REQUIREMENT_NOT_FOUND = "REQUIREMENT_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    AI_OUTPUT_INVALID = "AI_OUTPUT_INVALID"
    GENERATION_JOB_NOT_FOUND = "GENERATION_JOB_NOT_FOUND"
    TEST_CASE_NOT_FOUND = "TEST_CASE_NOT_FOUND"
    GENERATION_QUEUE_UNAVAILABLE = "GENERATION_QUEUE_UNAVAILABLE"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
