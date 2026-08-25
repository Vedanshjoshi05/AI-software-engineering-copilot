"""
Centralized application configuration.

All environment variables are declared here and validated at startup via
Pydantic. This mirrors the environment variables previously read ad-hoc
throughout the Node/Express backend (process.env.*).
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    APP_NAME: str = "AI Software Engineering Copilot API"
    ENV: str = Field(default="development", alias="NODE_ENV")
    PORT: int = 8000
    LOG_LEVEL: str = "info"

    # CORS - comma separated list of allowed origins, "*" allowed for dev
    CORS_ORIGINS: str = "*"

    # ------------------------------------------------------------------
    # MongoDB
    # ------------------------------------------------------------------
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "ai_copilot"

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL_SECONDS: int = 3600

    # ------------------------------------------------------------------
    # Qdrant
    # ------------------------------------------------------------------
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "code_chunks"

    # ------------------------------------------------------------------
    # Auth / JWT
    # ------------------------------------------------------------------
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_IN: str = "7d"  # e.g. "7d", "12h", "3600" (seconds)

    # ------------------------------------------------------------------
    # GitHub
    # ------------------------------------------------------------------
    GITHUB_TOKEN: str | None = None
    GITHUB_API_BASE_URL: str = "https://api.github.com"
    MAX_FILE_SIZE_BYTES: int = 200 * 1024
    MAX_FILES_PER_INDEX: int = 25

    # ------------------------------------------------------------------
    # LLM / Embeddings
    # ------------------------------------------------------------------
    LLM_API_KEY: str
    LLM_PROVIDER: str = "gemini"
    LLM_GENERATION_MODELS: str = (
        "gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite"
    )

    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 200

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------
    INDEXING_TIMEOUT_MINUTES: int = 15
    EMBEDDING_DELAY_MS: int = 150

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("LLM_API_KEY", "EMBEDDING_API_KEY", mode="before")
    @classmethod
    def _fallback_embedding_key(cls, v, info):
        # If EMBEDDING_API_KEY is not provided, fall back to LLM_API_KEY,
        # matching the original app which used a single Gemini client for both.
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    @property
    def generation_models_list(self) -> list[str]:
        return [m.strip() for m in self.LLM_GENERATION_MODELS.split(",") if m.strip()]

    @property
    def jwt_expires_seconds(self) -> int:
        """Parse JWT_EXPIRES_IN like '7d', '12h', '30m', '3600' into seconds."""
        value = self.JWT_EXPIRES_IN.strip().lower()
        try:
            if value.endswith("d"):
                return int(value[:-1]) * 86400
            if value.endswith("h"):
                return int(value[:-1]) * 3600
            if value.endswith("m"):
                return int(value[:-1]) * 60
            if value.endswith("s"):
                return int(value[:-1])
            return int(value)
        except ValueError:
            return 7 * 86400

    @property
    def effective_embedding_api_key(self) -> str:
        return self.EMBEDDING_API_KEY or self.LLM_API_KEY


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance. Raises a clear error if required vars are missing."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
