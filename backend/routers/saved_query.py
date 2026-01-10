from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List
from models.auth import User
from services.security import get_current_user
from services.audit_service import AuditService, SavedQueryEntry
from db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/saved-queries", response_model=None)
async def save_query(
    name: str = Body(...),
    db_id: str = Body(...),
    natural_query: str = Body(None),
    raw_query: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    audit_service = AuditService(db)
    try:
        await audit_service.save_query(
            username=current_user.username,
            db_id=db_id,
            name=name,
            natural_query=natural_query,
            raw_query=raw_query
        )
        return {"message": "Query saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save query: {e}")

@router.get("/saved-queries", response_model=List[SavedQueryEntry])
async def get_saved_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    audit_service = AuditService(db)
    try:
        return await audit_service.get_saved_queries(username=current_user.username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch saved queries: {e}")

@router.delete("/saved-queries/{query_id}")
async def delete_saved_query(
    query_id: int, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    audit_service = AuditService(db)
    try:
        await audit_service.delete_saved_query(query_id=query_id, username=current_user.username)
        return {"message": "Query deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete query: {e}")
