
import uuid
from fastapi import Depends
from fastapi_users import FastAPIUsers
import app
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


# In your route:
@app.get("/protected")
async def protected_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}"}

# What happens:
# 1. User sends request with JWT token
# 2. current_active_user dependency:
#    - Extracts token from header
#    - Verifies signature
#    - Loads user from database
# 3. If valid: user object passed to function
#    If invalid: Returns 401 Unauthorized