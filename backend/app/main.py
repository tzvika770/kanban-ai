import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure database directory exists
Path("data").mkdir(exist_ok=True)

# Import and initialize database
from .database import init_db, get_db
from . import models
from .routes import auth, kanban, ai

# Initialize DB on startup
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Server starting...")
    yield
    # Shutdown
    print("🛑 Server stopping...")


# Create FastAPI app
app = FastAPI(
    title="PM Backend",
    description="Project Management API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local development (all origins allowed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(kanban.router)
app.include_router(ai.router)


# Health check endpoint
@app.get("/api/health")
def health():
    """Health check endpoint - no auth required"""
    return {
        "status": "ok",
        "service": "pm-backend",
        "version": "0.1.0",
    }


# Static files serving (after all routes, so /api/* takes precedence)
# This will be populated in Part 3 after frontend build
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
