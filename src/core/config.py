from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Config(BaseSettings):
    """Application configuration settings."""
    
    APP_NAME: str = "Memory Personality Engine"
    APP_VERSION: str = "0.0.1"
    DEBUG: bool = False
    
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    MEMORY_DB_PATH: str = "./data/memory.db"
    VECTOR_DB_PATH: str = "./data/qdrant"
    
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 1536
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
        )
    
    
config = Config()