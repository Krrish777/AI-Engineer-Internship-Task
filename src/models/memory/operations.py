"""Operation models for memory management."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

from ..enums import MemoryLayer, MemoryType


class MemoryOperationResult(BaseModel):
    """Result of a memory operation."""
    success: bool = Field(..., description="Whether operation was successful")
    memory_id: Optional[str] = Field(None, description="ID of affected memory")
    message: str = Field(..., description="Operation result message")
    affected_count: int = Field(0, description="Number of memories affected")


class MemoryLayerSummary(BaseModel):
    """Summary of memories in a specific layer."""
    layer: MemoryLayer = Field(..., description="Memory layer")
    total_memories: int = Field(..., description="Total memories in layer")
    memory_types: Dict[MemoryType, int] = Field(default_factory=dict, description="Count by memory type")
    categories: Dict[str, int] = Field(default_factory=dict, description="Count by category")
    avg_confidence: float = Field(..., description="Average confidence score")
    oldest_memory: Optional[datetime] = Field(None, description="Oldest memory timestamp")
    newest_memory: Optional[datetime] = Field(None, description="Newest memory timestamp")


class UserMemoryProfile(BaseModel):
    """Complete user memory profile."""
    user_id: str = Field(..., description="User identifier")
    layer_summaries: List[MemoryLayerSummary] = Field(..., description="Summary by memory layers")
    total_memories: int = Field(..., description="Total memories across all layers")
    personality_indicators: Dict[str, float] = Field(default_factory=dict, description="Personality trait scores")
    last_interaction: Optional[datetime] = Field(None, description="Last interaction timestamp")
    memory_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall memory quality")
    
    # User insights
    dominant_emotions: List[str] = Field(default_factory=list, description="Most common emotions")
    key_preferences: List[str] = Field(default_factory=list, description="Key preferences")
    behavioral_patterns: List[str] = Field(default_factory=list, description="Identified behavioral patterns")