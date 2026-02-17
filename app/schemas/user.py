
import uuid
from fastapi_users import schemas

# What: Schema for user registration
# Why: Validates email and password when signing up
# How: Inherits from FastAPI Users base schema
class UserRead(schemas.BaseUser[uuid.UUID]):
    """
     Schema returned when reading user info
     API responses showing user profile
     Only includes safe fields (no password!)
    """
    pass

class UserCreate(schemas.BaseUserCreate):
    """
     Schema for user registration
     Validates new account creation
     Requires email and password
    """
    pass

class UserUpdate(schemas.BaseUserUpdate):
    """
     Schema for updating user info
     Allows changing email or password
     All fields optional
    """
    pass