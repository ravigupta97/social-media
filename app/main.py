
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.auth import fastapi_users, auth_backend
from app.schemas import UserRead, UserCreate
from app.routers import posts
from app.config import settings
import os

# ============================================
# LIFESPAN: Startup and Shutdown Events
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    What: Manages application lifecycle (startup/shutdown)
    Why: Initialize database before accepting requests
    How: Async context manager
    
    Startup: Create database tables
    Shutdown: Cleanup (if needed)
    """
    # What: Startup - Create database tables
    # Why: Ensures all tables exist before app runs
    # How: Uses SQLAlchemy metadata from models
    print("🚀 Starting up...")
    print("📊 Creating database tables...")
    
    async with engine.begin() as conn:
        # What: Create all tables defined in models
        # Why: Auto-migration based on SQLAlchemy models
        # How: Creates tables if they don't exist (won't drop existing)
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully!")
    print(f"📁 Upload directory: {settings.UPLOAD_DIR}")
    
    # What: Ensure upload directory exists
    # Why: First upload will fail if directory missing
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    yield  # What: Application runs here (between startup and shutdown)
    
    # What: Shutdown - Cleanup (runs when app stops)
    print("👋 Shutting down...")

# ============================================
# CREATE FASTAPI APP
# ============================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A photo and video sharing social media backend API",
    version="1.0.0",
    lifespan=lifespan  # What: Attach lifespan events
)

# ============================================
# INCLUDE ROUTERS
# ============================================

# What: Authentication routes (register, login)
# Why: Users need to create accounts and authenticate
# How: FastAPI Users provides these routes automatically
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["Authentication"]
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Authentication"]
)

# What: Posts routes (upload, feed, delete)
# Why: Core functionality of the app
# How: Our custom router from routers/posts.py
app.include_router(
    posts.router,
    tags=["Posts"]
)

# ============================================
# STATIC FILES (Serve uploaded images/videos)
# ============================================

# What: Serve uploaded files via HTTP
# Why: Frontend needs to access /uploads/abc-123.jpg
# How: Mount directory as static files
# Example: GET /uploads/photo.jpg → serves uploads/photo.jpg
app.mount(
    f"/{settings.UPLOAD_DIR}",
    StaticFiles(directory=settings.UPLOAD_DIR),
    name="uploads"
)

# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """
    What: Welcome endpoint
    Why: Quick check if API is running
    How: Simple JSON response
    """
    return {
        "message": "Welcome to FastAPI Social Media API",
        "docs": "/docs",
        "version": "1.0.0"
    }

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    What: Health check endpoint
    Why: Monitoring systems can verify app is running
    How: Returns status
    """
    return {"status": "healthy"}