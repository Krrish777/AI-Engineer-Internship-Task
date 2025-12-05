"""
Personality Engine Module.

This module provides the personality layer for the AI companion system.
Personalities are post-processing transformers that style responses
without altering reasoning or facts.

Key components:
- PersonalityEngine: Main engine for loading and applying personalities
- PersonalityConfig: Configuration model for personality definitions
- MemoryWeightApplicator: Applies personality-specific memory weights
"""

from .engine import PersonalityEngine
from .models import PersonalityConfig
from .models import MemoryWeights
from .config_loader import load_personality_config
from .config_loader import load_all_personalities

__all__ = [
    "PersonalityEngine",
    "PersonalityConfig",
    "MemoryWeights",
    "load_personality_config",
    "load_all_personalities",
]
