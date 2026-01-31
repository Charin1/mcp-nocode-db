from fastapi import APIRouter, HTTPException, Depends
from models.query import QueryRequest, GeneratedQuery, QueryResult
from models.auth import User
from services.security import get_current_user, has_role
from services.db_manager import DbManager
from services.llm_service import LLMService
from services.audit_service import AuditService
from db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/query/generate", response_model=GeneratedQuery)
async def generate_query_from_nl(
    request: QueryRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Takes a natural language query and returns a generated raw query (SQL, Mongo JSON, etc.)
    without executing it.
    """
    db_manager = DbManager()
    llm_service = LLMService()
    audit_service = AuditService(db)

    try:
        schema_for_prompt = await db_manager.get_schema_for_prompt(request.db_id)
        db_engine = db_manager.get_db_engine(request.db_id)

        generated_query = await llm_service.generate_query(
            provider=request.model_provider,
            natural_language_query=request.natural_language_query,
            schema=schema_for_prompt,
            engine=db_engine,
        )

        await audit_service.log(
            username=current_user.username,
            db_id=request.db_id,
            natural_query=request.natural_language_query,
            generated_query=generated_query.raw_query,
            executed=False,
            success=True if not generated_query.error else False,
        )

        return generated_query

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await audit_service.log(
            username=current_user.username,
            db_id=request.db_id,
            natural_query=request.natural_language_query,
            executed=False,
            success=False,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to generate query: {e}")


@router.post("/query/execute", response_model=QueryResult)
async def execute_raw_query(
    request: QueryRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a raw query against the specified database.
    Includes safety checks for mutations.
    """
    db_manager = DbManager()
    audit_service = AuditService(db)

    # Multi-DB Logic: Parse real DB_ID if scope is ALL
    real_db_id = request.db_id
    final_query = request.raw_query.strip()

    # Multi-DB Logic: Check for DB_ID: <id> prefix regardless of request.db_id
    # This allows LLM to route to a different DB than the one selected in UI (if in 'All' scope)
    import re
    match = re.match(r"^DB_ID:\s*([a-zA-Z0-9_-]+)\s*\n?", final_query, re.IGNORECASE)
    
    if match:
        real_db_id = match.group(1).strip()
        final_query = final_query[match.end():].strip()
    elif request.db_id == "ALL":
         # Fallback error if we expected routing but got none and db_id is still ALL
         raise HTTPException(
            status_code=400, 
            detail="Multi-Database Execution Error: Could not identify target database. Query must start with 'DB_ID: <id>'."
        )

    db_config = db_manager.get_db_config(real_db_id)
    if not db_config:
        raise HTTPException(
            status_code=404, detail=f"Database '{real_db_id}' not found."
        )

    is_mutation = db_manager.is_mutation_query(real_db_id, final_query)

    if is_mutation:
        if not db_config.get("allow_mutations"):
            raise HTTPException(
                status_code=403,
                detail="Mutations are disabled for this database connection in the configuration.",
            )
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Only admins can perform mutation queries.",
            )
        if not request.allow_mutations:
            raise HTTPException(
                status_code=400,
                detail="Mutation query detected, but the 'allow_mutations' confirmation flag was not set.",
            )

    try:
        result = await db_manager.execute_query(real_db_id, final_query)

        await audit_service.log(
            username=current_user.username,
            db_id=real_db_id,
            natural_query=request.natural_language_query,
            generated_query=final_query,
            executed=True,
            success=True,
            rows_returned=result.get("rows_affected", 0),
        )
        return QueryResult(**result, query_executed=final_query)

    except Exception as e:
        await audit_service.log(
            username=current_user.username,
            db_id=real_db_id,
            natural_query=request.natural_language_query,
            generated_query=final_query,
            executed=True,
            success=False,
            error=str(e),
        )
        return QueryResult(error=str(e), query_executed=request.raw_query)
