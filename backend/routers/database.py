from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from services.db_manager import DbManager
from models.database import AppConfig, Schema
from models.auth import User
from services.security import get_current_user

router = APIRouter()


@router.get("/config", response_model=AppConfig)
async def get_app_config():
    """
    Returns the list of configured databases and LLM providers.
    """
    try:
        manager = DbManager()
        return manager.get_app_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{db_id}", response_model=List[Schema])
async def get_database_schema(db_id: str):
    """
    Returns the schema (tables, collections, etc.) for a given database.
    """
    try:
        manager = DbManager()
        schema = await manager.get_schema(db_id)
        return schema
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {e}")


@router.get("/schemas", response_model=Dict[str, Any])
async def get_all_schemas():
    """
    Returns the schema for ALL configured databases.
    """
    try:
        manager = DbManager()
        schemas = await manager.get_all_schemas()
        return schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve all schemas: {e}")


@router.get("/sample_data/{db_id}/{object_name}", response_model=Dict[str, Any])
async def get_sample_data(db_id: str, object_name: str):
    """
    Returns sample data for a specific table, collection, or other DB object.
    """
    try:
        manager = DbManager()
        sample_data = await manager.get_sample_data(db_id, object_name)
        return sample_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve sample data: {e}"
        )
