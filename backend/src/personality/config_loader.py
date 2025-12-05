"""
Personality configuration loader.

Handles loading personality definitions from YAML configuration files.
"""

from pathlib import Path
from typing import Dict
from typing import Any
from typing import List

import yaml

from src.core.logging import CustomLogger

logger_instance = CustomLogger("personality_config")
logger = logger_instance.get_logger()


def _get_personalities_dir() -> Path:
    """Get the personalities configuration directory."""
    return Path(__file__).resolve().parents[1] / "config" / "personalities"


def load_personality_config(personality_name: str) -> Dict[str, Any]:
    """
    Load a specific personality configuration from YAML.
    
    Args:
        personality_name: Name of the personality to load (without .yaml extension)
        
    Returns:
        Dictionary containing personality configuration
        
    Raises:
        FileNotFoundError: If personality config file doesn't exist
        ValueError: If config file is invalid
    """
    personalities_dir = _get_personalities_dir()
    config_file = personalities_dir / f"{personality_name}.yaml"
    
    if not config_file.exists():
        logger.error(f"Personality config not found: {config_file}")
        raise FileNotFoundError(f"Personality configuration not found: {personality_name}")
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
            
        if not raw_config or "personality" not in raw_config:
            raise ValueError(f"Invalid personality config structure in {personality_name}")
            
        logger.info(f"Loaded personality config: {personality_name}")
        return raw_config["personality"]
        
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {personality_name}: {e}")
        raise ValueError(f"Invalid YAML in personality config: {personality_name}") from e


def load_all_personalities() -> Dict[str, Dict[str, Any]]:
    """
    Load all personality configurations from the personalities directory.
    
    Returns:
        Dictionary mapping personality names to their configurations
    """
    personalities_dir = _get_personalities_dir()
    all_personalities = {}
    
    if not personalities_dir.exists():
        logger.warning("Personalities directory not found: %s", personalities_dir)
        return all_personalities
    
    for yaml_file in personalities_dir.glob("*.yaml"):
        personality_name = yaml_file.stem
        try:
            all_personalities[personality_name] = load_personality_config(personality_name)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Failed to load personality {personality_name}: {e}")
            continue
    
    logger.info(f"Loaded {len(all_personalities)} personalities: {list(all_personalities.keys())}")
    return all_personalities


def get_available_personalities() -> List[str]:
    """
    Get list of available personality names.
    
    Returns:
        List of personality names that can be loaded
    """
    personalities_dir = _get_personalities_dir()
    
    if not personalities_dir.exists():
        return []
    
    return [f.stem for f in personalities_dir.glob("*.yaml")]


def validate_personality_config(config: Dict[str, Any]) -> bool:
    """
    Validate a personality configuration has required fields.
    
    Args:
        config: Personality configuration dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["name", "tone", "memory_weights"]
    
    for field in required_fields:
        if field not in config:
            logger.warning("Missing required field in personality config: %s", field)
            return False
    
    # Validate memory weights
    weights = config.get("memory_weights", {})
    weight_fields = ["factual", "preferences", "emotional_patterns"]
    
    for weight_field in weight_fields:
        if weight_field not in weights:
            logger.warning("Missing memory weight field: %s", weight_field)
            return False
        
        weight_value = weights[weight_field]
        if not isinstance(weight_value, (int, float)) or not 0 <= weight_value <= 1:
            logger.warning("Invalid weight value for %s: %s", weight_field, weight_value)
            return False
    
    return True


def get_default_personality() -> str:
    """
    Get the default personality name.
    
    Returns:
        Name of the default personality (calm_mentor)
    """
    return "calm_mentor"
