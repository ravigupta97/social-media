from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.auth import fastapi_users, auth_backend
from app.schemas import UserRead, UserCreate
from app.routers import posts
from app.config import settings
import os

# ============================================
# LIFESPAN
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")
    print("📊 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    print("👋 Shutting down...")


# ============================================
# OPENAPI DESCRIPTION (Swagger + ReDoc)
# ============================================

API_DESCRIPTION = """
## Overview

A production-grade REST API for a photo and video sharing social media platform.
Built with **FastAPI**, **PostgreSQL**, and **JWT authentication**.

---

## Architecture

```
Client
  │
  ├── POST /auth/register       → Create account
  ├── POST /auth/jwt/login      → Get JWT token
  │
  ├── [Protected - Bearer JWT]
  │     ├── POST /upload        → Upload photo/video
  │     ├── GET  /feed          → Browse all posts
  │     ├── GET  /post/{id}     → Get single post
  │     └── DELETE /post/{id}   → Delete own post
  │
  └── Static: /uploads/{file}  → Serve media files
```

---

## Authentication Flow

This API uses **JWT Bearer Token** authentication.

**Step 1 — Register:**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Step 2 — Login (get token):**
```http
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```
> ⚠️ Login uses `application/x-www-form-urlencoded`, not JSON. The field is named `username` but accepts your email.

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Step 3 — Use token in requests:**
```http
Authorization: Bearer <your_access_token>
```

> Tokens expire after **1 hour**. Login again to get a new token.

---

## Testing This API (Step-by-Step)

Follow this exact sequence to test all features:

### 1. Register a user
`POST /auth/register` → Provide email + password → Note the returned `id`

### 2. Login
`POST /auth/jwt/login` → Use email as `username` → Copy the `access_token`

### 3. Authorize (Swagger UI only)
Click the **Authorize 🔓** button at the top-right → Paste your token → Click **Authorize**

### 4. Upload a post
`POST /upload` → Attach an image/video file → Optionally add a caption → Note the returned post `id`

### 5. View the feed
`GET /feed` → Returns all posts newest-first, with `is_owner: true` for your posts

### 6. Get a single post
`GET /post/{id}` → Paste the post `id` from step 4

### 7. Delete your post
`DELETE /post/{id}` → Paste your post `id` → Returns 204 No Content on success

### 8. Test authorization
Login as a **different user** → Try to delete the first user's post → Expect `403 Forbidden`

---

## Data Models

### User
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Auto-generated unique identifier |
| email | string | Unique, validated email address |
| is_active | boolean | Account status (default: true) |
| is_verified | boolean | Email verification status |

### Post
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Auto-generated unique identifier |
| caption | string \\| null | Optional post description (max 2000 chars) |
| url | string | Relative path to the stored media file |
| file_type | enum | `image` or `video` |
| created_at | datetime | UTC timestamp of creation |
| user_id | UUID | Foreign key to the owning user |
| user_email | string | Denormalized author email (read-only) |
| is_owner | boolean | True if the requesting user created this post |

---

## Supported File Types

| Category | Extensions | Max Size |
|----------|-----------|----------|
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` | 10 MB |
| Videos | `.mp4`, `.mov`, `.avi`, `.mkv` | 10 MB |

---

## Error Reference

| Status | Meaning | Common Cause |
|--------|---------|--------------|
| 400 | Bad Request | Unsupported file type or invalid input |
| 401 | Unauthorized | Missing or expired JWT token |
| 403 | Forbidden | Attempting to delete another user's post |
| 404 | Not Found | Post ID does not exist |
| 413 | Payload Too Large | File exceeds 10 MB limit |
| 422 | Unprocessable Entity | Request body failed validation |
| 500 | Internal Server Error | File system or database error |

---

## Notes

- All `id` fields are **UUID v4** — copy them exactly including hyphens.
- The `url` field in post responses is a relative path. Prepend your base URL to access the file:  
  `http://localhost:8000` + `/uploads/abc123.jpg`
- Feed results are ordered **newest first** and support `limit` / `offset` for pagination.
- Deleting a post removes both the **database record** and the **file from disk**.
"""

# ============================================
# CREATE FASTAPI APP
# ============================================

app = FastAPI(
    title="Social Media Backend API",
    description=API_DESCRIPTION,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": (
                "Register new accounts and authenticate with JWT tokens. "
                "**Login uses `application/x-www-form-urlencoded` (not JSON).** "
                "The `username` field accepts your email address."
            ),
        },
        {
            "name": "Posts",
            "description": (
                "Create, retrieve, and delete photo/video posts. "
                "All endpoints require a valid Bearer token in the `Authorization` header. "
                "File uploads use `multipart/form-data`."
            ),
        },
        {
            "name": "Health",
            "description": "Server status and availability check.",
        },
    ],
    lifespan=lifespan,
)

# What: Override the OpenAPI security scheme
# Why: Forces Swagger UI to show a token paste box instead of email/password fields
# How: Replaces FastAPI Users' OAuth2 scheme with HTTPBearer
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        contact=app.contact,
        license_info=app.license_info,
        tags=app.openapi_tags,
        routes=app.routes,
    )

    # What: Replace OAuth2 with HTTPBearer in security schemes
    # Why: Swagger UI shows a simple token input box instead of username/password
    # How: Overwrite the securitySchemes section of the OpenAPI schema
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "Paste your JWT access token here.\n\n"
                "Get a token by calling **POST /auth/jwt/login** first.\n\n"
                "Example: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`"
            )
        }
    }

    # What: Apply HTTPBearer to all protected routes
    # Why: Swagger UI shows the lock icon only on authenticated endpoints
    # How: Set security requirement on every path operation
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "security" in operation:
                operation["security"] = [{"HTTPBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ============================================
# INCLUDE ROUTERS
# ============================================

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

app.include_router(
    posts.router,
    tags=["Posts"]
)

# ============================================
# STATIC FILES
# ============================================

app.mount(
    f"/{settings.UPLOAD_DIR}",
    StaticFiles(directory=settings.UPLOAD_DIR),
    name="uploads"
)

# ============================================
# ROOT & HEALTH
# ============================================

@app.get("/", tags=["Health"], summary="Welcome", include_in_schema=False)
async def root():
    return {
        "message": "Social Media Backend API",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "1.0.0"
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    responses={
        200: {
            "description": "Server is running",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        }
    }
)
async def health_check():
    """Returns server health status. Use this to verify the API is reachable."""
    return {"status": "healthy"}