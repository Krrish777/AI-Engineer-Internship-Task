from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import logging

logger = logging.getLogger(__name__)

def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def _config_dir() -> Path:
    return _project_root() / "config"

def _prompts_dir() -> Path:
    return _config_dir() / "prompts"

def load_app_config() -> Dict[str, Any]:
    """Load main application configuration."""
    config_dir = _config_dir()
    config_file = config_dir / "app_config.yaml"
    
    if not config_file.exists():
        logger.warning(f"App config not found: {config_file}")
        return {}
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading app config: {e}")
        return {}

def load_prompt_config(prompt_type: str) -> Dict[str, Any]:
    """Load specific prompt configuration."""
    prompts_dir = _prompts_dir()
    
    if not prompts_dir.exists():
        logger.warning(f"Prompts directory not found: {prompts_dir}")
        return {}
    
    config_file = prompts_dir / f"{prompt_type}.yaml"
    
    if not config_file.exists():
        logger.warning(f"Prompt config not found: {config_file}")
        return {}
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading {config_file}: {e}")
        return {}

def load_all_prompts() -> Dict[str, Dict[str, Any]]:
    """Load all prompt configurations."""
    prompts_dir = _prompts_dir()
    all_prompts = {}
    
    if not prompts_dir.exists():
        return all_prompts
    
    for yaml_file in prompts_dir.glob("*.yaml"):
        prompt_type = yaml_file.stem
        all_prompts[prompt_type] = load_prompt_config(prompt_type)
    
    return all_prompts

def load_all_configs() -> Dict[str, Any]:
    """Load all configurations (app + prompts)."""
    return {
        "app": load_app_config(),
        "prompts": load_all_prompts()
    }

# Convenience functions for specific config sections
def get_api_config() -> Dict[str, Any]:
    """Get API configuration section."""
    app_config = load_app_config()
    return app_config.get("api", {})

def get_model_config() -> Dict[str, Any]:
    """Get model configuration section."""
    app_config = load_app_config()
    return app_config.get("models", {})

def get_database_config() -> Dict[str, Any]:
    """Get database configuration section."""
    app_config = load_app_config()
    return app_config.get("databases", {})

# Backward compatibility
def load_config(config_file: Optional[Path] = None):
    """Deprecated: Use load_app_config() or load_prompt_config() instead."""
    return load_app_config()