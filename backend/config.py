"""
Configuration management for WWHD backend
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "W.W.H.D. API"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", env="APP_ENV")
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="CORS_ORIGINS"
    )
    allow_credentials: bool = Field(default=True, env="ALLOW_CREDENTIALS")

    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    model_chat: str = Field(default="gpt-4o-mini", env="MODEL_CHAT")
    model_embed: str = Field(default="text-embedding-3-small", env="MODEL_EMBED")
    enable_openai: bool = Field(default=True, env="ENABLE_OPENAI")
    enable_openrouter: bool = Field(default=False, env="ENABLE_OPENROUTER")

    # Agent Models
    orchestrator_model: str = Field(default="gpt-4o-mini", env="ORCHESTRATOR_MODEL")
    specialist_model: str = Field(default="gpt-4o-mini", env="SPECIALIST_MODEL")
    enable_streaming: bool = Field(default=True, env="ENABLE_STREAMING")

    # Qdrant Configuration
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")

    # Database - fallback to local path if /data doesn't exist
    sqlite_path: str = Field(default="/data/wwhd.db", env="SQLITE_PATH")

    @property
    def database_url(self) -> str:
        """Generate SQLAlchemy database URL"""
        # Fallback to local path if /data directory doesn't exist
        import os
        db_path = self.sqlite_path

        # If /data path is specified but directory doesn't exist, fallback to local
        if db_path.startswith('/data/') and not os.path.exists('/data'):
            db_path = './wwhd.db'
            print(f"Warning: /data directory not found, using fallback path: {db_path}")
        else:
            print(f"Using database path: {db_path}")

        # Ensure parent directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")

        # Use aiosqlite for async support
        return f"sqlite+aiosqlite:///{db_path}"

    # Authentication
    jwt_secret: str = Field(default="change-this-in-production", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiry_hours: int = Field(default=24, env="JWT_EXPIRY_HOURS")

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")

    # Token Limits
    max_tokens_per_response: int = Field(default=2000, env="MAX_TOKENS_PER_RESPONSE")
    max_context_tokens: int = Field(default=4000, env="MAX_CONTEXT_TOKENS")

    # RAG Settings
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    top_k_retrieval: int = Field(default=5, env="TOP_K_RETRIEVAL")
    min_relevance_score: float = Field(default=0.7, env="MIN_RELEVANCE_SCORE")

    # AWS Settings
    aws_default_region: str = Field(default="us-west-2", env="AWS_DEFAULT_REGION")

    class Config:
        env_file = ".env"
        case_sensitive = False

    def validate_api_keys(self) -> bool:
        """Validate that at least one LLM API key is configured"""
        if self.enable_openai and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when ENABLE_OPENAI=true")
        if self.enable_openrouter and not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required when ENABLE_OPENROUTER=true")
        if not self.enable_openai and not self.enable_openrouter:
            raise ValueError("At least one LLM provider must be enabled")
        return True

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.app_env == "development"


# Create a singleton instance
settings = Settings()

# Validate on startup (will raise if invalid)
if os.getenv("APP_ENV") != "test":  # Skip validation in test environment
    try:
        settings.validate_api_keys()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please check your .env file and ensure API keys are set correctly.")
        # Don't exit in development to allow for configuration