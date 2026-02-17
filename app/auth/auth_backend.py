from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from app.config import settings

# What: How tokens are transported
# Why: Defines where token goes in HTTP request
# How: Bearer token in Authorization header
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# What: JWT strategy configuration
# Why: Defines how tokens are created and validated
# How: Returns a JWT strategy with our secret key
def get_jwt_strategy() -> JWTStrategy:
    """
    What: Creates JWT strategy for token management
    Why: Configures token lifetime and signing
    How: Uses SECRET_KEY from settings
    
    Parameters:
    - secret: Key to sign tokens (from .env)
    - lifetime_seconds: How long token is valid (1 hour)
    """
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=3600  # 1 hour
    )

# What: Complete authentication backend
# Why: Combines transport + strategy
# How: FastAPI Users uses this for all auth operations
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)