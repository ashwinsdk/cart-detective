"""Application configuration for Cart Detective."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///data/cart_detective.db"

    # LLM Settings
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_API_KEY: str = ""

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Search & Discovery
    SEARXNG_URL: str = "http://localhost:8080"
    BRAVE_SEARCH_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""

    # Fetcher & Cache
    HTTP_CACHE_DIR: str = "data/cache/http"
    HTTP_TIMEOUT_SECONDS: float = 15.0
    MAX_RETRIES_PER_DOMAIN: int = 3
    RATE_LIMIT_DELAY_SECONDS: float = 1.0
    USER_AGENT: str = "CartDetective/0.1.0 (Autonomous Research Agent; +https://github.com/ashwinsdk/cart-detective)"


settings = Settings()
