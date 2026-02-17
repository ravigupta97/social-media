from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid
from app.models.post import FileType

# What: Schema for creating a new post
# Why: Validates incoming data when user uploads
# How: Only needs caption (optional), file comes separately
class PostCreate(BaseModel):
    # What: Optional[str] is the Python 3.9 way of saying str | None
    # Why: Caption is not required when uploading
    caption: Optional[str] = Field(
        None,
        max_length=2000,
        description="Post caption (optional)"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "caption": "Beautiful sunset at the beach!"
                }
            ]
        }
    }

# What: Schema for API responses (what user gets back)
# Why: Includes all post details + author info
class PostResponse(BaseModel):
    id: uuid.UUID
    caption: Optional[str]
    url: str
    file_type: FileType
    created_at: datetime
    user_id: uuid.UUID
    user_email: str
    is_owner: bool
    
    model_config = {
        "from_attributes": True
    }

# What: Simplified schema for feed listing
class PostList(PostResponse):
    pass