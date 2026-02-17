import uuid
from fastapi_users import FastAPIUsers
from app.models.user import User
from app.auth.user_manager import get_user_manager
from app.auth.auth_backend import auth_backend

# What: Main FastAPI Users instance
# Why: Provides all authentication functionality
# How: Combines User model, manager, and auth backend
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# What: Dependency to get current logged-in user
# Why: Protect routes - only authenticated users can access
# How: Checks JWT token, returns User object or 401 error
current_active_user = fastapi_users.current_user(active=True)