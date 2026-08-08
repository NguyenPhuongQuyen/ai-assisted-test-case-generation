from enum import StrEnum

AUTH_SCHEME_BEARER = "bearer"


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


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AuditAction(StrEnum):
    GENERATE_TEST_CASES = "generate_test_cases"


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
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
