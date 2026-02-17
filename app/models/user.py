from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.database import Base
from typing import TYPE_CHECKING
import uuid

# What: Only import Post for type hints, not at runtime
# Why: Breaks circular import (user.py ↔ post.py)
# How: TYPE_CHECKING is False at runtime, True for IDE/type checkers
if TYPE_CHECKING:
    from app.models.post import Post

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(length=320), 
        unique=True, 
        index=True, 
        nullable=False
    )
    
    # What: Use string "Post" instead of direct Post class
    # Why: SQLAlchemy resolves string references lazily (after all models loaded)
    # How: "Post" in quotes = forward reference
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="user",
        cascade="all, delete-orphan"
    )