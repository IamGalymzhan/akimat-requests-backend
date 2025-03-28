from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "Akimat Requests API"
    VERSION: str = "1.0.0"
    API_STR: str = "/api"
    
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @property
    def get_database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # NCANode Settings
    NCANODE_API_ENDPOINT: str = "http://localhost:14579"
    NCANODE_VERIFY_OCSP: bool = True
    NCANODE_VERIFY_CRL: bool = True
    
    # File uploads
    UPLOADS_DIR: str = str(Path(os.getcwd()) / "uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 