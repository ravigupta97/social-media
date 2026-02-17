from sqlalchemy import String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from typing import TYPE_CHECKING
import uuid
import enum

# What: Only import User for type hints, not at runtime
# Why: Breaks circular import
# How: TYPE_CHECKING guard
if TYPE_CHECKING:
    from app.models.user import User

class FileType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    caption: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType),
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # What: String "User" = forward reference
    # Why: SQLAlchemy resolves this after ALL models are loaded
    # How: No direct import needed at runtime
    user: Mapped["User"] = relationship(
        "User",
        back_populates="posts"
    )