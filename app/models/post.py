
from app.models.user import User
from sqlalchemy import String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
import uuid
import enum

# Enum for file types
class FileType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"

#  Post table model
# Stores all photos/videos shared by users
# SQLAlchemy model with relationships to User
class Post(Base):
    __tablename__ = "posts"
    
    #  Primary key (unique ID for each post)
    #  UUID is globally unique (better than 1, 2, 3...)
    #  Auto-generates UUID when post created
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    
    #  User's caption/description
    #  Allow long text (Text type has no length limit)
    #  nullable=True means caption is optional
    caption: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    #  Path to the uploaded file
    #  We need to know where the file is stored
    #  String with max length 500 characters
    url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    #  Image or Video?
    #  Frontend needs to know whether to use <img> or <video> tag
    #  Enum restricts to only valid values
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType),
        nullable=False
    )
    
    #  Timestamp when post was created
    #  Sort feed chronologically (newest first)
    #  Auto-sets to current time when post created
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    #  Foreign key linking to User table
    #  Track who created this post
    #  References users.id column
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    #  Relationship back to User model
    #  Easy access to post owner (post.user.email)
    #  SQLAlchemy manages the join automatically
    user: Mapped["User"] = relationship(
        "User",
        back_populates="posts"
    )