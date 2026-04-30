"""
ADAM DNA Tool - Application Configuration
Centralized settings management using Pydantic Settings.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Application
    APP_NAME: str = "ADAM DNA Tool"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # AI Model Providers
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: Optional[str] = None  # For Azure OpenAI compatibility

    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    # Default AI provider: openai | anthropic | azure_openai
    AI_PROVIDER: str = "openai"

    # File Storage
    UPLOAD_DIR: str = "/tmp/adam-dna-uploads"
    OUTPUT_DIR: str = "/tmp/adam-dna-output"
    MAX_UPLOAD_SIZE_MB: int = 100

    # ADAM Configuration
    ADAM_DOCS_PATH: str = "/app/adam-docs"  # Mounted ADAM book content
    DNA_TOOL_PATH: str = "/app/dna-tool"   # Mounted DNA Deployment Tool

    # Session
    SESSION_TTL_HOURS: int = 72
    SECRET_KEY: str = "change-me-in-production-use-secrets-manager"

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
