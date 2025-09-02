from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings for Commit Tracker Service."""

    # Application settings
    APP_NAME: str = "Commit Tracker Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, json_schema_extra={"env": "DEBUG"})

    # Server settings
    HOST: str = Field(default="0.0.0.0", json_schema_extra={"env": "HOST"})
    PORT: int = Field(default=8001, json_schema_extra={"env": "PORT"})

    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/commit_tracker",
        json_schema_extra={"env": "DATABASE_URL"},
    )

    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        json_schema_extra={"env": "ALLOWED_ORIGINS"},
    )

    # Git settings
    GIT_REPO_PATH: str = Field(default=".", json_schema_extra={"env": "GIT_REPO_PATH"})

    # Webhook settings
    WEBHOOK_SECRET: str = Field(default="your-webhook-secret", json_schema_extra={"env": "WEBHOOK_SECRET"})

    # Authentication settings
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production", json_schema_extra={"env": "SECRET_KEY"}
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, json_schema_extra={"env": "ACCESS_TOKEN_EXPIRE_MINUTES"}
    )
    ALGORITHM: str = Field(default="HS256", json_schema_extra={"env": "ALGORITHM"})

    # Monitoring settings
    ENABLE_METRICS: bool = Field(default=True, json_schema_extra={"env": "ENABLE_METRICS"})
    LOG_LEVEL: str = Field(default="INFO", json_schema_extra={"env": "LOG_LEVEL"})

    # External service URLs (for future integration)
    GITHUB_WEBHOOK_SERVICE_URL: str = Field(
        default="http://localhost:8000", json_schema_extra={"env": "GITHUB_WEBHOOK_SERVICE_URL"}
    )
    AI_ANALYSIS_SERVICE_URL: str = Field(
        default="http://localhost:8002", json_schema_extra={"env": "AI_ANALYSIS_SERVICE_URL"}
    )
    COACHING_SERVICE_URL: str = Field(
        default="http://localhost:8003", json_schema_extra={"env": "COACHING_SERVICE_URL"}
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

# Global settings instance
settings = Settings()
