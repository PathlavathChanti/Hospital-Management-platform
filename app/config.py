import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "Hospital Management Platform"
    LOG_LEVEL: str = "INFO"

    # Database
    POSTGRES_USER: str = "hospital_user"
    POSTGRES_PASSWORD: str = "hospital_pass"
    POSTGRES_SERVER: str = "db"
    POSTGRES_DB: str = "hospital_db"
    DATABASE_URL: str = ""

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()
