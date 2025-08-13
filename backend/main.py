import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from models.auth import User
from routers import auth, database, query, admin
from services.audit_service import AuditService
from services.security import get_current_user, has_role, create_initial_admin_user

# Load environment variables from .env file at the very start

app = FastAPI(
    title="MCP No-Code DB Tool",
    description="API for a no-code database query tool with LLM integration.",
    version="1.0.0",
)

# CORS Middleware Setup - Allows the frontend to communicate with the backend
origins = [
    "http://localhost:5173",  # Default Vite dev server port
    "http://localhost:3000",  # Default Create React App port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initializes services and creates the first admin user if none exist."""
    AuditService.initialize()
    create_initial_admin_user()
    print("--- Application startup complete. Audit service initialized. ---")


# Include all the modular routers
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


@app.get("/health", tags=["Health"])
def health_check():
    """Simple health check endpoint to confirm the API is running."""
    return {"status": "ok"}


@app.get("/api/me", response_model=User, tags=["Users"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Fetches the profile of the currently authenticated user."""
    return current_user