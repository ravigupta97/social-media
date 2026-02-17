
import uuid
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from app.models.user import User
from app.auth.user_db import get_user_db
from app.config import settings

# What: Secret key for JWT signing
# Why: Ensures tokens can't be forged
# How: Uses SECRET_KEY from .env
SECRET = settings.SECRET_KEY

# What: User Manager class
# Why: Handles all user operations (register, login, forgot password, etc.)
# How: Inherits from FastAPI Users base manager
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    # What: Configuration
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET
    
    # What: Hook that runs after successful registration
    # Why: You can send welcome email, log event, etc.
    # How: Override this method
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
        # TODO: Send welcome email here
    
    #  Hook for forgot password
    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")
        # TODO: Send password reset email here
    
    #  Hook after email verification request
    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")
        # TODO: Send verification email here

#  Dependency to get UserManager instance
#  FastAPI injects this into routes
#  Creates new manager for each request
async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)