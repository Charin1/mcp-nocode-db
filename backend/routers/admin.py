from fastapi import APIRouter, Depends
from typing import List
from services.audit_service import AuditService, AuditLogEntry
from db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.security import has_role

router = APIRouter()


@router.get("/audit", response_model=List[AuditLogEntry])
async def get_audit_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
    # Note: depends on has_role('admin') is already on the router inclusion in main.py, so strictly not needed here but good practice.
):
    """
    Retrieves audit logs. Only accessible by users with the 'admin' role.
    """
    audit_service = AuditService(db)
    logs = await audit_service.get_logs(limit)
    return logs
