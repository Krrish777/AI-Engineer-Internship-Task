"""
Prompt loader for pipeline templates.

Loads prompt templates from YAML configuration files.
"""

from pathlib import Path
from typing import Any
from typing import Dict

import yaml

from src.core.logging import CustomLogger

logger_instance = CustomLogger("prompt_loader")
logger = logger_instance.get_logger()


def _get_prompts_dir() -> Path:
    """Get the prompts configuration directory."""
    return Path(__file__).parent.parent / "config" / "prompts"


def load_pipeline_prompts() -> Dict[str, Any]:
    """
    Load pipeline prompt templates from YAML config.

    Returns:
        Dictionary containing all pipeline prompts

    Raises:
        FileNotFoundError: If prompts file not found
        ValueError: If YAML is invalid
    """
    prompts_file = _get_prompts_dir() / "pipeline_prompts.yaml"

    if not prompts_file.exists():
        logger.error(f"Pipeline prompts file not found: {prompts_file}")
        raise FileNotFoundError(f"Pipeline prompts not found: {prompts_file}")

    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config or "prompts" not in config:
            raise ValueError("Invalid pipeline prompts structure")

        logger.info("Loaded pipeline prompts")
        return config["prompts"]

    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in pipeline prompts: {e}")
        raise ValueError("Invalid YAML in pipeline prompts") from e


def get_base_response_prompt() -> str:
    """
    Get the base response generation prompt template.

    Returns:
        Prompt template string
    """
    prompts = load_pipeline_prompts()
    return prompts.get("base_response", {}).get("template", "")


def get_style_transformation_prompt() -> str:
    """
    Get the style transformation prompt template.

    Returns:
        Prompt template string
    """
    prompts = load_pipeline_prompts()
    return prompts.get("style_transformation", {}).get("template", "")


def get_validation_prompt() -> str:
    """
    Get the validation prompt template.

    Returns:
        Prompt template string
    """
    prompts = load_pipeline_prompts()
    return prompts.get("validation", {}).get("template", "")
