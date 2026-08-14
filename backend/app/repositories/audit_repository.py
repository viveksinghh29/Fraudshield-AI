"""AuditRepository — append-only writes plus filtered reads for the admin audit trail."""

import uuid
from typing import Any

from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def log(
        self,
        *,
        action: str,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Convenience wrapper over `create()` with audit-log-specific kwarg
        names, so services write `audit_repo.log(action="LOGIN", ...)`
        rather than remembering the raw column names.
        """
        return await self.create(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            log_metadata=metadata,
        )
