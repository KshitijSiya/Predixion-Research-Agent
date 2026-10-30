import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings loaded from environment or .env file.
    """
    # Primary LLM Provider (Groq)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_FALLBACK_MODEL: str = "qwen/qwen3.8-27b"
    
    # Optional External Providers
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Search Engine
    SEARCH_BACKEND: str = "duckduckgo"
    MAX_SEARCH_RESULTS: int = 5
    
    # Scraper & Sanitization
    SCRAPE_TIMEOUT_SECONDS: int = 8
    MAX_CONTENT_TOKENS_PER_PAGE: int = 2500
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
