# 📸 Social Media Backend API

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)

> A production-grade REST API for a photo and video sharing platform — built with FastAPI, PostgreSQL, async SQLAlchemy, and JWT authentication. Upload media, browse a chronological feed, and manage posts with full ownership enforcement.



## 📚 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation \& Setup](#-installation--setup)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)
- [Running the Server](#-running-the-server)
- [API Endpoints](#-api-endpoints)
- [Authentication Flow](#-authentication-flow)
- [Testing the API](#-testing-the-api)
- [Supported File Types](#-supported-file-types)
- [Error Reference](#-error-reference)

---

## 🗺 Overview

This project is a **backend-only REST API** for a social media platform similar to the early days of Instagram. The focus is entirely on server-side logic — API design, database management, authentication, and file handling. FastAPI's built-in **Swagger UI** at `/docs` serves as the interactive interface for development and testing.

### What it does

A user can register an account, log in to receive a JWT token, and use that token to upload photos or videos with an optional caption. All uploaded posts appear in a shared chronological feed visible to any authenticated user. Each user can delete only their own posts — attempting to delete someone else's returns a `403 Forbidden`. Uploaded files are stored on the local filesystem and served as static assets via the same server.

### How it is structured

The application is organized in layers — each with a single responsibility:

```
HTTP Request
     │
     ▼
 FastAPI Router          ← Receives request, calls dependencies
     │
     ├── JWT Middleware  ← Verifies token, loads current user
     │
     ├── Pydantic Schema ← Validates incoming data types and constraints
     │
     ├── Business Logic  ← File handling, ownership checks
     │
     └── SQLAlchemy ORM  ← Reads/writes PostgreSQL asynchronously
```

All database operations are **fully asynchronous** using `asyncpg` and SQLAlchemy's async session, meaning the server never blocks while waiting for a database response — it handles other requests in the meantime.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Database | PostgreSQL | Production-ready, handles concurrency, supports UUIDs natively |
| Auth library | FastAPI Users | Pre-built JWT + bcrypt — avoids weeks of boilerplate |
| ORM mode | Async SQLAlchemy | Non-blocking DB calls for better performance under load |
| File storage | Local filesystem | Simple, no external service dependency for development |
| IDs | UUID v4 | Globally unique, not guessable (unlike sequential integers) |
| Token expiry | 1 hour | Balances security and user convenience |

---

## ✨ Features

### 👤 User Accounts
- Register with email and password
- Passwords hashed with **bcrypt** before storage — never stored in plaintext
- Login returns a signed **JWT access token** (HS256)
- Token-based stateless authentication — no server-side sessions

### 📤 Media Uploads
- Upload **photos** (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`) and **videos** (`.mp4`, `.mov`, `.avi`, `.mkv`)
- Files renamed to **UUID-based filenames** on save — prevents collisions and hides original names
- File type detected from extension — invalid types rejected before saving
- File size enforced at **10 MB max** — oversized uploads rejected immediately
- Uploaded files served via static file handler at `/uploads/<filename>`

### 📰 Feed
- Chronological feed of all posts — **newest first**
- Each post in the feed includes the author's email and an `is_owner` flag
- Supports **pagination** via `limit` and `offset` query parameters
- Feed is only accessible to authenticated users

### 🔒 Authorization
- Every protected endpoint verifies the JWT token on every request
- Users can only **delete their own posts** — ownership checked server-side
- Attempting to delete another user's post returns `403 Forbidden`
- Expired or tampered tokens return `401 Unauthorized`

### 🗄 Database
- **Auto-migration on startup** — tables created automatically, no manual SQL needed
- `users` and `posts` tables with a **one-to-many relationship**
- Cascade delete — removing a user removes all their posts automatically
- Async queries with **eager loading** to avoid N+1 query problems on the feed

### 📖 Documentation
- Auto-generated **Swagger UI** at `/docs` — test every endpoint interactively in the browser
- **ReDoc** at `/redoc` — clean readable reference for all endpoints and schemas
- Full request/response examples embedded in the docs

---

📌 **Demo:** Open `http://localhost:8000/docs` after setup to explore the full interactive Swagger UI.

---

## ✅ Prerequisites

Make sure the following are installed on your machine before cloning the project.

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.9+ | [python.org](https://www.python.org/downloads/) |
| PostgreSQL | 13+ | [postgresql.org](https://www.postgresql.org/download/windows/) |
| Git | Any | [git-scm.com](https://git-scm.com/) |
| VS Code *(recommended)* | Any | [code.visualstudio.com](https://code.visualstudio.com/) |

**Verify your installations:**

```powershell
python --version
psql --version
git --version
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```powershell
git clone https://github.com/your-username/social-media-api.git
cd social-media-api
```

### 2. Create a Virtual Environment

```powershell
python -m venv venv
```

### 3. Activate the Virtual Environment

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

> ⚠️ If you see an execution policy error, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

You should see `(venv)` appear at the start of your terminal prompt.

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 5. Set Up PostgreSQL Database

Connect to PostgreSQL and create the database:

```powershell
psql -U postgres
```

Inside the PostgreSQL prompt:

```sql
CREATE DATABASE social_media_db;
\l        -- verify it appears in the list
\q        -- exit
```

### 6. Configure Environment Variables

Create a `.env` file in the project root:

```powershell
New-Item -ItemType File -Path ".env"
```

Open it and add the following (see [Environment Variables](#-environment-variables) for details):

```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/social_media_db
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
DEBUG=True
```

> Replace `your_password` with your PostgreSQL password.

### 7. Run the Server

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**

```
🚀 Starting up...
📊 Creating database tables...
✅ Database tables created successfully!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> Database tables are created **automatically** on first run. No manual migrations needed.

### 8. Open the Docs

| Interface | URL | Description |
|-----------|-----|-------------|
| Swagger UI | http://localhost:8000/docs | Interactive — test endpoints directly |
| ReDoc | http://localhost:8000/redoc | Readable reference documentation |
| Health Check | http://localhost:8000/health | Verify the server is running |

---

## 📁 Project Structure

```
social-media-api/
│
├── app/                          # Main application package
│   ├── __init__.py
│   │
│   ├── main.py                   # App entry point — registers routers, lifespan, static files
│   ├── config.py                 # Pydantic settings — loads and validates .env variables
│   ├── database.py               # Async SQLAlchemy engine, session factory, Base class
│   │
│   ├── auth/                     # Authentication layer (FastAPI Users)
│   │   ├── __init__.py
│   │   ├── auth_backend.py       # JWT strategy and Bearer transport configuration
│   │   ├── fastapi_users.py      # FastAPIUsers instance and current_active_user dependency
│   │   ├── user_db.py            # SQLAlchemy user database accessor
│   │   └── user_manager.py       # UserManager — lifecycle hooks (register, forgot password)
│   │
│   ├── models/                   # SQLAlchemy ORM models (database tables)
│   │   ├── __init__.py
│   │   ├── user.py               # User model — extends FastAPI Users base
│   │   └── post.py               # Post model — caption, url, file_type, user_id FK
│   │
│   ├── schemas/                  # Pydantic schemas (request/response validation)
│   │   ├── __init__.py
│   │   ├── user.py               # UserRead, UserCreate, UserUpdate schemas
│   │   └── post.py               # PostCreate, PostResponse, PostList schemas
│   │
│   └── routers/                  # API route handlers
│       ├── __init__.py
│       └── posts.py              # /upload, /feed, /post/{id}, DELETE /post/{id}
│
├── uploads/                      # Uploaded media files (auto-created on first run)
│
├── venv/                         # Virtual environment (not committed)
├── .env                          # Environment variables (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

### What each layer does

| Layer | Folder | Responsibility |
|-------|--------|----------------|
| **Config** | `app/config.py` | Single source of truth for all settings — loaded once at startup |
| **Database** | `app/database.py` | Manages async connection pool to PostgreSQL |
| **Models** | `app/models/` | Define database table structure using Python classes |
| **Schemas** | `app/schemas/` | Validate incoming requests and shape outgoing responses |
| **Auth** | `app/auth/` | Handle registration, login, JWT creation and verification |
| **Routers** | `app/routers/` | Business logic — file handling, database queries, HTTP responses |
| **Main** | `app/main.py` | Wires everything together — routers, lifespan, static files |

---

## 🔑 Environment Variables

All configuration lives in a `.env` file in the project root. The app will **refuse to start** if required variables are missing.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | — | Full async PostgreSQL connection string |
| `SECRET_KEY` | ✅ Yes | — | Secret used to sign JWT tokens — min 32 chars |
| `DEBUG` | No | `True` | Enables SQL query logging in the console |
| `UPLOAD_DIR` | No | `uploads` | Directory where uploaded files are stored |
| `MAX_FILE_SIZE` | No | `10485760` | Max upload size in bytes (default: 10 MB) |

**`DATABASE_URL` format:**

```
postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>
```

**Example:**

```env
DATABASE_URL=postgresql+asyncpg://postgres:mypassword@localhost:5432/social_media_db
```

**Generating a strong `SECRET_KEY`:**

```powershell
# Option 1: Python one-liner
python -c "import secrets; print(secrets.token_hex(32))"

# Option 2: Just use a long random string (min 32 characters)
SECRET_KEY=xK9#mP2@nL5qR8vT1wY4uJ7eH0cB3fA6dM
```

---

## ▶️ Running the Server

```powershell
# Development (auto-reload on code changes)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production (no reload, single worker)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Flags explained:**

| Flag | Purpose |
|------|---------|
| `app.main:app` | Path to the FastAPI instance — `app` folder → `main.py` → `app` variable |
| `--host 0.0.0.0` | Listen on all network interfaces (not just localhost) |
| `--port 8000` | Port number |
| `--reload` | Restart server automatically when code changes — **dev only** |

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | ❌ | Create new account |
| `POST` | `/auth/jwt/login` | ❌ | Get JWT token |
| `POST` | `/upload` | ✅ | Upload photo/video |
| `GET` | `/feed` | ✅ | Get all posts |
| `GET` | `/post/{id}` | ✅ | Get single post |
| `DELETE` | `/post/{id}` | ✅ | Delete own post |
| `GET` | `/health` | ❌ | Server status |

---

## 🔐 Authentication Flow

```
1.  POST /auth/register        → Create account
        ↓
2.  POST /auth/jwt/login        → Receive access_token
        ↓
3.  All protected requests:
    Header: Authorization: Bearer <access_token>
        ↓
4.  Token expires after 1 hour → Repeat from step 2
```

**How it works under the hood:**

- Passwords are hashed with **bcrypt** before storage — never stored in plaintext
- Tokens are signed with **HMAC-SHA256** using your `SECRET_KEY`
- Every protected request verifies the token signature and expiry before executing
- Modifying a token (e.g. to fake a different user ID) invalidates the signature → `401`

---

## 🧪 Testing the API

### Using Swagger UI (Recommended)

**Step 1 — Register**
1. Go to `http://localhost:8000/docs`
2. Open `POST /auth/register` → Try it out
3. Submit with your email and password

**Step 2 — Login**
1. Open `POST /auth/jwt/login` → Try it out
2. Fill `username` (your email) and `password`
3. Copy the `access_token` from the response

**Step 3 — Authorize**
1. Click the **Authorize 🔓** button (top-right of the page)
2. Paste your token into the **HTTPBearer** value field
3. Click **Authorize** → **Close**

**Step 4 — Upload a post**
1. Open `POST /upload` → Try it out
2. Choose a file and optionally add a caption
3. Click Execute — note the post `id` in the response

**Step 5 — View the feed**
1. Open `GET /feed` → Try it out → Execute
2. Your post should appear with `is_owner: true`

**Step 6 — Access the uploaded file**
- Copy the `url` field from the post response
- Visit: `http://localhost:8000` + `/uploads/your-filename.jpg`

**Step 7 — Test authorization**
1. Register a second user and log in as them
2. Re-authorize Swagger with the second user's token
3. Try `DELETE /post/{id}` using the first user's post ID
4. Expect `403 Forbidden` — ownership enforcement working correctly

---

## 📎 Supported File Types

| Type | Extensions | Max Size |
|------|-----------|----------|
| Images | `.jpg` `.jpeg` `.png` `.gif` `.webp` | 10 MB |
| Videos | `.mp4` `.mov` `.avi` `.mkv` | 10 MB |

Uploaded files are renamed to a **UUID-based filename** to prevent collisions and stored in the `uploads/` directory.

---

## ⚠️ Error Reference

| Status | Meaning | Common Cause |
|--------|---------|--------------|
| `400` | Bad Request | Unsupported file extension |
| `401` | Unauthorized | Missing, expired, or invalid token |
| `403` | Forbidden | Attempting to delete another user's post |
| `404` | Not Found | Post ID does not exist |
| `413` | Payload Too Large | File exceeds 10 MB |
| `422` | Unprocessable Entity | Request body failed validation |
| `500` | Internal Server Error | Filesystem or database error |

---

<div align="center">

**Built with FastAPI and PostgreSQL**

[⬆ Back to Top](#-social-media)

</div>
