"""
Memory extraction module.

This module provides specialized agents for extracting different types
of memories from conversations following mem0 patterns with Agno integration.
"""

from .base_classes import BaseExtractor, BaseAgentManager, BaseResultProcessor

__all__ = [
    "BaseExtractor",
    "BaseAgentManager", 
    "BaseResultProcessor"
]
