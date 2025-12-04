"""Models package for the AI companion system."""

from .enums import (
    ConfidenceLevel, MemoryLayer, MemoryType, 
    PreferenceCategory, EmotionType
)
from .memory import (
    BaseMemory, UserPreference, EmotionalPattern, FactualMemory,
    PreferenceItem, PreferenceExtractionOutput,
    EmotionItem, EmotionExtractionOutput,
    FactItem, FactExtractionOutput,
    ConversationAnalysisOutput, MemoryExtractionOutput,
    MemorySearchFilter, MemorySearchResult,
    MemoryOperationResult, MemoryLayerSummary, UserMemoryProfile
)

__all__ = [
    # Enums
    "ConfidenceLevel", "MemoryLayer", "MemoryType",
    "PreferenceCategory", "EmotionType",
    # Memory models
    "BaseMemory", "UserPreference", "EmotionalPattern", "FactualMemory",
    # Extraction models
    "PreferenceItem", "PreferenceExtractionOutput",
    "EmotionItem", "EmotionExtractionOutput",
    "FactItem", "FactExtractionOutput",
    "ConversationAnalysisOutput", "MemoryExtractionOutput",
    # Search models
    "MemorySearchFilter", "MemorySearchResult",
    # Operations models
    "MemoryOperationResult", "MemoryLayerSummary", "UserMemoryProfile"
]
