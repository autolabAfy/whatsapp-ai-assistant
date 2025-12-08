"""
Configuration management for WhatsApp AI Assistant
Loads settings from environment variables
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    database_url: str = "postgresql://localhost:5432/whatsapp_ai_assistant"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Green API
    green_api_base_url: str = "https://api.green-api.com"
    green_api_instance_id: Optional[str] = None
    green_api_token: Optional[str] = None

    # Anthropic
    anthropic_api_key: Optional[str] = None

    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"

    # AI Provider Selection
    ai_provider: str = "gemini"  # Options: "anthropic", "gemini", "mock"

    # JWT
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Application
    environment: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    webhook_base_url: str = "http://localhost:8000"

    # Logging
    log_level: str = "INFO"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Rate Limiting
    redis_lock_timeout: int = 30
    webhook_dedup_ttl: int = 300  # 5 minutes

    # Follow-up delays (hours)
    followup_delay_2h: int = 2
    followup_delay_24h: int = 24
    followup_delay_72h: int = 72

    # AI Response
    max_response_length: int = 4096  # WhatsApp limit
    ai_model: str = "claude-3-5-sonnet-20241022"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL"""
    return settings.database_url


def get_redis_url() -> str:
    """Get Redis URL"""
    return settings.redis_url


def get_green_api_config() -> dict:
    """Get Green API configuration"""
    return {
        "base_url": settings.green_api_base_url,
        "instance_id": settings.green_api_instance_id,
        "token": settings.green_api_token,
    }


def get_anthropic_api_key() -> str:
    """Get Anthropic API key"""
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")
    return settings.anthropic_api_key
