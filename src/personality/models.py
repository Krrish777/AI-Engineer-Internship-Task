"""
Personality data models.

Defines Pydantic models for personality configuration validation
and structured data handling.
"""

from typing import Dict
from typing import List
from typing import Optional
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class MemoryWeights(BaseModel):
    """Memory type weights for personality-specific context prioritization."""
    
    factual: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0,
        description="Weight for factual memories"
    )
    preferences: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0,
        description="Weight for preference memories"
    )
    emotional_patterns: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0,
        description="Weight for emotional pattern memories"
    )


class ToneConfig(BaseModel):
    """Tone configuration for personality."""
    
    primary: str = Field(..., description="Primary tone characteristic")
    secondary: str = Field(default="neutral", description="Secondary tone characteristic")
    formality: str = Field(default="moderate", description="Formality level")
    warmth: str = Field(default="moderate", description="Warmth level")


class ResponsePatterns(BaseModel):
    """Response pattern templates for personality consistency."""
    
    opening: List[str] = Field(default_factory=list, description="Opening phrase patterns")
    transitions: List[str] = Field(default_factory=list, description="Transition phrase patterns")
    closing: List[str] = Field(default_factory=list, description="Closing phrase patterns")


class PersonalityConfig(BaseModel):
    """Complete personality configuration model."""
    
    name: str = Field(..., description="Unique personality identifier")
    description: str = Field(default="", description="Human-readable personality description")
    
    tone: ToneConfig = Field(..., description="Tone configuration")
    style_rules: List[str] = Field(default_factory=list, description="Style guidelines")
    memory_weights: MemoryWeights = Field(
        default_factory=MemoryWeights,
        description="Memory type weights"
    )
    response_patterns: ResponsePatterns = Field(
        default_factory=ResponsePatterns,
        description="Response pattern templates"
    )
    guardrails: List[str] = Field(default_factory=list, description="Behavioral constraints")
    forbidden: List[str] = Field(default_factory=list, description="Forbidden behaviors")
    context_priorities: List[str] = Field(
        default_factory=list,
        description="Priority context elements"
    )
    safety_protocols: List[str] = Field(
        default_factory=list,
        description="Safety-related protocols"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate personality name is lowercase with underscores only."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Personality name must be alphanumeric with underscores only")
        return v.lower()


class WeightedMemoryContext(BaseModel):
    """Memory context with personality-specific weights applied."""
    
    factual: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    emotional_patterns: Dict[str, Any] = Field(default_factory=dict)
    weights_applied: MemoryWeights = Field(default_factory=MemoryWeights)
    
    def get_priority_context(self) -> Dict[str, Any]:
        """Get context ordered by weight priority."""
        weighted_items = [
            ("factual", self.factual, self.weights_applied.factual),
            ("preferences", self.preferences, self.weights_applied.preferences),
            ("emotional_patterns", self.emotional_patterns, self.weights_applied.emotional_patterns),
        ]
        sorted_items = sorted(weighted_items, key=lambda x: x[2], reverse=True)
        return {item[0]: item[1] for item in sorted_items if item[2] > 0}


class PersonalitySwitchEvent(BaseModel):
    """Event record for personality switches."""
    
    from_personality: Optional[str] = Field(None, description="Previous personality")
    to_personality: str = Field(..., description="New personality")
    trigger: str = Field(default="user_request", description="What triggered the switch")
    timestamp: str = Field(..., description="ISO timestamp of switch")


class PersonalityState(BaseModel):
    """Current state of the personality engine."""
    
    active_personality: str = Field(..., description="Currently active personality name")
    available_personalities: List[str] = Field(default_factory=list)
    switch_history: List[PersonalitySwitchEvent] = Field(default_factory=list)
    user_preference: Optional[str] = Field(
        None, 
        description="User's explicitly preferred personality"
    )
