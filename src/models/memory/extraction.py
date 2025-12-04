from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from .core import UserPreference, EmotionalPattern, FactualMemory

class PreferenceItem(BaseModel):
    """Individual preference item for extraction."""
    category: str = Field(...)
    preference_value: str = Field(...)
    intensity: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)

class PreferenceExtractionOutput(BaseModel):
    """Output from preference extraction agent."""
    preferences: List[PreferenceItem] = Field(default_factory=list)
    extraction_notes: str = Field("")

class EmotionItem(BaseModel):
    """Individual emotion pattern for extraction."""
    emotion: str = Field(...)
    intensity: float = Field(..., ge=0.0, le=1.0)
    triggers: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)

class EmotionExtractionOutput(BaseModel):
    """Output from emotion extraction agent."""
    emotional_patterns: List[EmotionItem] = Field(default_factory=list)
    overall_mood: str = Field("")

class FactItem(BaseModel):
    """Individual fact for extraction."""
    content: str = Field(...)
    category: str = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)

class FactExtractionOutput(BaseModel):
    """Output from fact extraction agent."""
    facts: List[FactItem] = Field(default_factory=list)
    extraction_notes: str = Field("")

class ConversationAnalysisOutput(BaseModel):
    """Output from conversation analysis agent."""
    session_summary: str = Field(...)
    key_insights: List[str] = Field(default_factory=list)
    suggested_personality: str = Field("balanced")
    behavioral_patterns: List[str] = Field(default_factory=list)

class MemoryExtractionOutput(BaseModel):
    """Complete memory extraction output from conversations."""
    user_preferences: List[UserPreference] = Field(default_factory=list)
    emotional_patterns: List[EmotionalPattern] = Field(default_factory=list)
    factual_memories: List[FactualMemory] = Field(default_factory=list)
    
    extraction_confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: Optional[int] = None
    source_messages_count: int = Field(...)
    
    session_summary: Optional[str] = None
    key_insights: List[str] = Field(default_factory=list)
    suggested_personality: Optional[str] = None
    
    extracted_at: datetime = Field(default_factory=datetime.now)
