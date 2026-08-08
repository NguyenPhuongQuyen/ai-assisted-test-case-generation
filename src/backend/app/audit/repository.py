from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog


class AuditLogRepository:
    """Append-only repository; no update/delete method is exposed (SE-16)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entry: AuditLog) -> AuditLog:
        self._session.add(entry)
        await self._session.flush()
        return entry
