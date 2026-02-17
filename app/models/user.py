
from app.models.post import Post
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.database import Base
import uuid

#  User table model
#      - id (UUID)
#      - email
#      - hashed_password
#      - is_active, is_superuser, is_verified
class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    
    #  Override email to make it unique and indexed
    email: Mapped[str] = mapped_column(
        String(length=320), 
        unique=True, 
        index=True, 
        nullable=False
    )
    
    #  Relationship to Post model
    #  One user can have many posts (one-to-many)
    #  SQLAlchemy automatically manages this link
    # back_populates: Creates reverse relationship (post.user)
    # cascade: When user deleted, delete all their posts too
    posts: Mapped[list["Post"]] = relationship(
        "Post", 
        back_populates="user",
        cascade="all, delete-orphan"
    )