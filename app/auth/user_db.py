
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.database import get_async_session
import uuid

# What: Dependency to get user database accessor
# Why: Provides CRUD operations for User model
# How: FastAPI Users + SQLAlchemy integration
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """
    What: Creates a database accessor for User operations
    Why: UserManager uses this to read/write users
    How: Wraps AsyncSession with FastAPI Users adapter
    """
    yield SQLAlchemyUserDatabase(session, User)