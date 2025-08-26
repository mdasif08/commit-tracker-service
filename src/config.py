from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings for Commit Tracker Service."""

    # Application settings
    APP_NAME: str = "Commit Tracker Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8001, env="PORT")

    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/commit_tracker",
        env="DATABASE_URL",
    )

    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS",
    )

    # Git settings
    GIT_REPO_PATH: str = Field(default=".", env="GIT_REPO_PATH")

    # Webhook settings
    WEBHOOK_SECRET: str = Field(default="your-webhook-secret", env="WEBHOOK_SECRET")

    # Authentication settings
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production", env="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")

    # Monitoring settings
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # External service URLs (for future integration)
    GITHUB_WEBHOOK_SERVICE_URL: str = Field(
        default="http://localhost:8000", env="GITHUB_WEBHOOK_SERVICE_URL"
    )
    AI_ANALYSIS_SERVICE_URL: str = Field(
        default="http://localhost:8002", env="AI_ANALYSIS_SERVICE_URL"
    )
    COACHING_SERVICE_URL: str = Field(
        default="http://localhost:8003", env="COACHING_SERVICE_URL"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
