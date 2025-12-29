import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from models.auth import User
from routers import auth, database, query, admin, chatbot, saved_query
from mcp_server import mcp
from services.audit_service import AuditService
from services.security import get_current_user, has_role, create_initial_admin_user


app = FastAPI(
    title="MCP No-Code DB Tool",
    description="API for a no-code database query tool with LLM integration.",
    version="1.0.0",
)

# Allows the frontend to communicate with the backend
origins = [
    "http://localhost:5173",  # Default Vite dev server port
    "http://localhost:5174",  # Alternative Vite port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:3000",  # Default Create React App port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
    """Initializes services and creates the first admin user if none exist."""
    # AuditService.initialize() # Disabling to prevent lock hangs
    create_initial_admin_user()


app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(
    database.router,
    prefix="/api",
    tags=["Database Schema"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    query.router,
    prefix="/api",
    tags=["Query Execution"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Administration"],
    dependencies=[Depends(has_role("admin"))],
)
app.include_router(
    chatbot.router,
    prefix="/api/chatbot",
    tags=["Chatbot"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    saved_query.router,
    prefix="/api",
    tags=["Saved Queries"],
    dependencies=[Depends(get_current_user)],
)
app.mount("/api/mcp", mcp.sse_app())


@app.get("/health", tags=["Health"])
def health_check():
    """Simple health check endpoint to confirm the API is running."""
    return {"status": "ok"}


@app.get("/api/me", response_model=User, tags=["Users"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Fetches the profile of the currently authenticated user."""
    return current_user
