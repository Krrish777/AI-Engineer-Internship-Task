from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from ..utils.config_loader import load_app_config, get_api_config, get_model_config, get_database_config

# Load YAML configuration
_yaml_config = load_app_config()

class Config(BaseSettings):
    """Application configuration settings loaded from YAML and environment."""
    
    # App Configuration
    APP_NAME: str = _yaml_config.get("app", {}).get("name", "Memory Personality Engine")
    APP_VERSION: str = _yaml_config.get("app", {}).get("version", "0.0.1")
    DEBUG: bool = _yaml_config.get("app", {}).get("debug", False)
    
    # AI Model Configuration
    GEMINI_API_KEY: str = ""  # Will be loaded from env
    GEMINI_MODEL: str = _yaml_config.get("models", {}).get("gemini", {}).get("model", "gemini-2.0-flash")
    
    EMBEDDING_MODEL: str = _yaml_config.get("models", {}).get("embedding", {}).get("model", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = _yaml_config.get("models", {}).get("embedding", {}).get("dimension", 1536)
    
    # Database Configuration
    MEMORY_DB_PATH: str = _yaml_config.get("databases", {}).get("memory", {}).get("path", "./data/memory.db")
    VECTOR_DB_PATH: str = _yaml_config.get("databases", {}).get("vector", {}).get("path", "./data/qdrant")
    
    # API Configuration
    API_HOST: str = _yaml_config.get("api", {}).get("host", "0.0.0.0")
    API_PORT: int = _yaml_config.get("api", {}).get("port", 8000)
    CORS_ORIGINS: List[str] = _yaml_config.get("api", {}).get("cors_origins", ["http://localhost:3000", "http://localhost:5173"])
    
    model_config = SettingsConfigDict(
        env_file=_yaml_config.get("environment", {}).get("env_file", ".env"),
        env_file_encoding=_yaml_config.get("environment", {}).get("env_file_encoding", "utf-8"),
        case_sensitive=_yaml_config.get("environment", {}).get("case_sensitive", True)
    )

config = Config()