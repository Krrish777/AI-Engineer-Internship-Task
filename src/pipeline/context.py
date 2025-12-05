"""
Pipeline context module.

Defines the data structures that flow through the transformation pipeline.
"""

from dataclasses import dataclass,field
from typing import Any, Dict, List, Optional
from src.personality.models import MemoryWeights


@dataclass(frozen=True)
class MemoryItem:
    """A single memory item with content and confidence."""

    content: str
    confidence: float
    weight_applied: float = 1.0

    @property
    def effective_score(self) -> float:
        """Calculate effective score based on confidence and weight."""
        return self.confidence * self.weight_applied


@dataclass
class WeightedMemory:
    """Memory context with personality weights applied."""

    factual: List[MemoryItem] = field(default_factory=list)
    preferences: List[MemoryItem] = field(default_factory=list)
    emotional_patterns: List[MemoryItem] = field(default_factory=list)
    weights: Optional[MemoryWeights] = None

    def to_prompt_format(self) -> Dict[str, str]:
        """Format memories for prompt insertion."""

        def format_items(items: List[MemoryItem]) -> str:
            if not items:
                return "No relevant memories available."
            formatted = []
            for item in sorted(items, key=lambda x: x.effective_score, reverse=True):
                formatted.append(
                    f"- {item.content} (confidence: {item.confidence:.2f})"
                )
            return "\n".join(formatted)

        return {
            "factual_memories": format_items(self.factual),
            "preference_memories": format_items(self.preferences),
            "emotional_memories": format_items(self.emotional_patterns),
            "factual_weight": str(self.weights.factual if self.weights else 1.0),
            "preferences_weight": str(self.weights.preferences if self.weights else 1.0),
            "emotional_weight": str(
                self.weights.emotional_patterns if self.weights else 1.0
            ),
        }


@dataclass
class ValidationResult:
    """Result of response validation against guardrails."""

    valid: bool
    violations: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class PipelineMetadata:
    """Metadata about pipeline execution."""

    personality_name: str
    stages_completed: List[str] = field(default_factory=list)
    stage_timings: Dict[str, float] = field(default_factory=dict)
    validation_result: Optional[ValidationResult] = None


@dataclass
class PipelineContext:
    """
    Immutable context that flows through pipeline stages.

    Each stage reads from this context and returns a new context
    with updated fields, preserving immutability.
    """

    # Input
    user_message: str
    raw_memory_context: Dict[str, Any] = field(default_factory=dict)

    # After MemoryWeightingStage
    weighted_memory: Optional[WeightedMemory] = None

    # After BaseResponseStage
    base_response: Optional[str] = None

    # After StyleTransformationStage
    styled_response: Optional[str] = None

    # Metadata
    metadata: PipelineMetadata = field(
        default_factory=lambda: PipelineMetadata(personality_name="")
    )

    def with_weighted_memory(self, weighted: WeightedMemory) -> "PipelineContext":
        """Return new context with weighted memory set."""
        return PipelineContext(
            user_message=self.user_message,
            raw_memory_context=self.raw_memory_context,
            weighted_memory=weighted,
            base_response=self.base_response,
            styled_response=self.styled_response,
            metadata=self.metadata,
        )

    def with_base_response(self, response: str) -> "PipelineContext":
        """Return new context with base response set."""
        return PipelineContext(
            user_message=self.user_message,
            raw_memory_context=self.raw_memory_context,
            weighted_memory=self.weighted_memory,
            base_response=response,
            styled_response=self.styled_response,
            metadata=self.metadata,
        )

    def with_styled_response(self, response: str) -> "PipelineContext":
        """Return new context with styled response set."""
        return PipelineContext(
            user_message=self.user_message,
            raw_memory_context=self.raw_memory_context,
            weighted_memory=self.weighted_memory,
            base_response=self.base_response,
            styled_response=response,
            metadata=self.metadata,
        )

    def with_metadata(self, metadata: PipelineMetadata) -> "PipelineContext":
        """Return new context with updated metadata."""
        return PipelineContext(
            user_message=self.user_message,
            raw_memory_context=self.raw_memory_context,
            weighted_memory=self.weighted_memory,
            base_response=self.base_response,
            styled_response=self.styled_response,
            metadata=metadata,
        )


@dataclass(frozen=True)
class TransformedResponse:
    """Final output of the transformation pipeline."""

    user_message: str
    base_response: str
    styled_response: str
    personality_name: str
    validation: ValidationResult
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if the response passed validation."""
        return self.validation.valid

    @property
    def final_response(self) -> str:
        """Get the final response to return to user."""
        return self.styled_response
