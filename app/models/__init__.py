# What: Import Base first so SQLAlchemy knows about it
# Why: Models need Base to be initialized
from app.database import Base

# What: Import models in correct order
# Why: This ensures both models are fully loaded
#      before SQLAlchemy resolves relationships
# How: Import Post first (no dependencies),
#      then User (references Post)
from app.models.post import Post, FileType
from app.models.user import User

__all__ = ["User", "Post", "FileType"]