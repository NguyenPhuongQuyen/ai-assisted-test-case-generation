from dataclasses import dataclass, field

from app.common.constants import ErrorCode


@dataclass(slots=True)
class AppError(Exception):
    """Domain/application error that is converted to the common ER-05 response format."""

    code: ErrorCode
    message: str
    status_code: int
    details: list[dict[str, str]] = field(default_factory=list)
