from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from ..enums import MemoryType, MemoryLayer, PreferenceCategory, EmotionType

class BaseMemory(BaseModel):
    """Base memory model - simplified for MVP."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="The actual memory content")
    memory_type: MemoryType = Field(...)
    memory_layer: MemoryLayer = Field(...)
    
    # Essential metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    relevance_score: float = Field(0.0, ge=0.0, le=1.0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    accessed_at: Optional[datetime] = None
    
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    context: Optional[str] = None
    
    
class UserPreference(BaseMemory):
    """User preference memory - simplified."""
    memory_type: MemoryType = Field(default=MemoryType.PREFERENCE)
    memory_layer: MemoryLayer = Field(default=MemoryLayer.USER)
    
    preference_category: PreferenceCategory = Field(...)
    preference_value: str = Field(...)
    intensity: float = Field(..., ge=0.0, le=1.0)
    reinforcement_count: int = Field(1)

class EmotionalPattern(BaseMemory):
    """Emotional pattern memory - simplified."""
    memory_type: MemoryType = Field(default=MemoryType.EMOTION)
    memory_layer: MemoryLayer = Field(default=MemoryLayer.USER)
    
    emotion: EmotionType = Field(...)
    intensity: float = Field(..., ge=0.0, le=1.0)
    triggers: List[str] = Field(default_factory=list)
    
    # Optional compatibility fields
    coping_mechanisms: List[str] = Field(default_factory=list)

class FactualMemory(BaseMemory):
    """Factual memory - simplified."""
    memory_type: MemoryType = Field(default=MemoryType.FACT)
    
    fact_category: str = Field(...)
    verified: bool = Field(default=False)
    
    # Optional compatibility fields
    source_reliability: float = Field(0.8, ge=0.0, le=1.0)
    related_entities: List[str] = Field(default_factory=list)