
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from app.models.post import FileType

#  Schema for creating a new post
# Validates incoming data when user uploads
# Only needs caption (optional), file comes separately
class PostCreate(BaseModel):
    caption: str | None = Field(
        None,
        max_length=2000,
        description="Post caption (optional)"
    )
    
    #  Example for API documentation
    # Shows developers how to use the API
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "caption": "Beautiful sunset at the beach! 🌅"
                }
            ]
        }
    }

#  Schema for API responses (what user gets back)
#  Includes all post details + author info
#  Combines post data with user email and ownership flag
class PostResponse(BaseModel):
    id: uuid.UUID
    caption: str | None
    url: str
    file_type: FileType
    created_at: datetime
    user_id: uuid.UUID
    
    #  Additional fields from relationships
    #  Frontend needs to show who posted it
    user_email: str  # From user.email
    is_owner: bool   # Is current user the creator?
    
    #  Enable ORM mode
    #  Allows Pydantic to read from SQLAlchemy models
    #  Can do PostResponse.model_validate(post_from_db)
    model_config = {
        "from_attributes": True
    }

#  Simplified schema for feed listing
#  Feed doesn't need all details, keeps response smaller
#  Same as PostResponse but could be customized later
class PostList(PostResponse):
    pass