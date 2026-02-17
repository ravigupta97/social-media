
from pydantic_settings import BaseSettings, SettingsConfigDict

#  Application configuration class
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    
    # Application
    DEBUG: bool = True
    PROJECT_NAME: str = "FastAPI SOCIAL MEDIA APP"
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov"}
    
    # Configure where to load settings from
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

#  Create single instance of settings
settings = Settings()