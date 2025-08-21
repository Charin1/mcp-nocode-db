from fastapi import APIRouter, Depends
from typing import List
from services.audit_service import AuditService, AuditLogEntry

router = APIRouter()


@router.get("/audit", response_model=List[AuditLogEntry])
async def get_audit_logs(limit: int = 100):
    """
    Retrieves audit logs. Only accessible by users with the 'admin' role.
    """
    logs = AuditService.get_logs(limit)
    return logs
