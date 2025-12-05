from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime

from ..enums import MemoryType, MemoryLayer
from .core import UserPreference, EmotionalPattern, FactualMemory

class MemorySearchFilter(BaseModel):
    """Search filters for memory retrieval."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    memory_layers: Optional[List[MemoryLayer]] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    confidence_min: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class MemorySearchResult(BaseModel):
    """Search result for memory retrieval."""
    memory: Union[UserPreference, EmotionalPattern, FactualMemory] = Field(...)
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    retrieval_context: Optional[str] = None
