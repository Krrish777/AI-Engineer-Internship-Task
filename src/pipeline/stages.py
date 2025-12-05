"""
Pipeline stages module.

Defines the Stage protocol and concrete stage implementations
for the response transformation pipeline.
"""

import time
from typing import Any, Dict, List, Protocol, runtime_checkable
from agno.agent import Agent

from src.core.logging import CustomLogger
from src.personality.engine import PersonalityEngine
from src.pipeline.context import MemoryItem, PipelineContext, ValidationResult, WeightedMemory

logger_instance = CustomLogger("pipeline_stages")
logger = logger_instance.get_logger()


@runtime_checkable
class PipelineStage(Protocol):
    """Protocol for pipeline stages."""

    @property
    def name(self) -> str:
        """Stage name for logging and tracking."""
        ...

    def process(self, context: PipelineContext) -> PipelineContext:
        """
        Process the context and return updated context.

        Args:
            context: Current pipeline context

        Returns:
            Updated pipeline context
        """
        ...


class MemoryWeightingStage:
    """
    Stage that applies personality-specific weights to memory context.

    Uses PersonalityEngine to weight different memory types
    according to the active personality configuration.
    """

    def __init__(self, personality_engine: PersonalityEngine) -> None:
        """
        Initialize the memory weighting stage.

        Args:
            personality_engine: Engine for applying personality weights
        """
        self._personality_engine = personality_engine

    @property
    def name(self) -> str:
        """Stage name."""
        return "memory_weighting"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Apply personality weights to memory context."""
        start_time = time.time()

        weighted = self._apply_weights(context.raw_memory_context)

        # Update metadata
        elapsed = time.time() - start_time
        metadata = context.metadata
        metadata.stages_completed.append(self.name)
        metadata.stage_timings[self.name] = elapsed
        metadata.personality_name = self._personality_engine.active_personality_name

        logger.info(
            f"Memory weighting completed in {elapsed:.3f}s for personality: "
            f"{metadata.personality_name}"
        )

        return context.with_weighted_memory(weighted).with_metadata(metadata)

    def _apply_weights(self, raw_memory: Dict[str, Any]) -> WeightedMemory:
        """Convert raw memory to weighted memory items."""
        weights = self._personality_engine.get_active_weights()

        factual_items = self._extract_memory_items(
            raw_memory.get("factual", {}), weights.factual
        )
        preference_items = self._extract_memory_items(
            raw_memory.get("preferences", {}), weights.preferences
        )
        emotional_items = self._extract_memory_items(
            raw_memory.get("emotional_patterns", {}), weights.emotional_patterns
        )

        return WeightedMemory(
            factual=factual_items,
            preferences=preference_items,
            emotional_patterns=emotional_items,
            weights=weights,
        )

    def _extract_memory_items(
        self, memories: Dict[str, Any], weight: float
    ) -> List[MemoryItem]:
        """Extract and weight memory items from raw memory dict."""
        items = []
        for _key, value in memories.items():
            if isinstance(value, dict):
                content = value.get("content", "")
                confidence = value.get("confidence", 0.5)
            else:
                content = str(value)
                confidence = 0.5

            if content:
                items.append(
                    MemoryItem(content=content, confidence=confidence, weight_applied=weight)
                )

        return items


class BaseResponseStage:
    """
    Stage that generates factual base response using weighted memory.

    Makes an LLM call with the memory context to produce
    a factually-grounded response before style transformation.
    """

    def __init__(self, agent: Agent, prompt_template: str) -> None:
        """
        Initialize the base response stage.

        Args:
            agent: Agno agent for LLM calls
            prompt_template: Template for base response generation
        """
        self._agent = agent
        self._prompt_template = prompt_template

    @property
    def name(self) -> str:
        """Stage name."""
        return "base_response"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Generate base response using weighted memory context."""
        start_time = time.time()

        if context.weighted_memory is None:
            raise ValueError("Memory weighting stage must run before base response stage")

        prompt = self._build_prompt(context)
        response = self._agent.run(prompt)
        base_response = str(response.content) if response and response.content else ""

        elapsed = time.time() - start_time
        metadata = context.metadata
        metadata.stages_completed.append(self.name)
        metadata.stage_timings[self.name] = elapsed

        logger.info(f"Base response generated in {elapsed:.3f}s")

        return context.with_base_response(base_response).with_metadata(metadata)

    def _build_prompt(self, context: PipelineContext) -> str:
        """Build the prompt for base response generation."""
        if context.weighted_memory is None:
            raise ValueError("Weighted memory must be set before building prompt")
        memory_format = context.weighted_memory.to_prompt_format()

        return self._prompt_template.format(
            user_message=context.user_message,
            **memory_format,
        )


class StyleTransformationStage:
    """
    Stage that transforms base response with personality style.

    Uses the PersonalityEngine to get style rules and makes
    an LLM call to apply the personality transformation.
    """

    def __init__(
        self,
        agent: Agent,
        personality_engine: PersonalityEngine,
        prompt_template: str,
    ) -> None:
        """
        Initialize the style transformation stage.

        Args:
            agent: Agno agent for LLM calls
            personality_engine: Engine for getting style context
            prompt_template: Template for style transformation
        """
        self._agent = agent
        self._personality_engine = personality_engine
        self._prompt_template = prompt_template

    @property
    def name(self) -> str:
        """Stage name."""
        return "style_transformation"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Transform base response with personality style."""
        start_time = time.time()

        if context.base_response is None:
            raise ValueError(
                "Base response stage must run before style transformation stage"
            )

        prompt = self._build_prompt(context)
        response = self._agent.run(prompt)
        styled_response = str(response.content) if response and response.content else (context.base_response or "")

        elapsed = time.time() - start_time
        metadata = context.metadata
        metadata.stages_completed.append(self.name)
        metadata.stage_timings[self.name] = elapsed

        logger.info(
            f"Style transformation completed in {elapsed:.3f}s "
            f"for personality: {self._personality_engine.active_personality_name}"
        )

        return context.with_styled_response(styled_response).with_metadata(metadata)

    def _build_prompt(self, context: PipelineContext) -> str:
        """Build the prompt for style transformation."""
        style_context = self._personality_engine.get_style_context()

        return self._prompt_template.format(
            base_response=context.base_response,
            personality_name=self._personality_engine.active_personality_name,
            tone_primary=style_context.get("tone", {}).get("primary", "neutral"),
            tone_secondary=style_context.get("tone", {}).get("secondary", ""),
            tone_formality=style_context.get("tone", {}).get("formality", "casual"),
            tone_warmth=style_context.get("tone", {}).get("warmth", "moderate"),
            style_rules=self._format_list(style_context.get("style_rules", [])),
            opening_patterns=self._format_list(
                style_context.get("response_patterns", {}).get("opening", [])
            ),
            transition_patterns=self._format_list(
                style_context.get("response_patterns", {}).get("transitions", [])
            ),
            closing_patterns=self._format_list(
                style_context.get("response_patterns", {}).get("closing", [])
            ),
            guardrails=self._format_list(style_context.get("guardrails", [])),
            forbidden=self._format_list(style_context.get("forbidden", [])),
        )

    def _format_list(self, items: List[str]) -> str:
        """Format a list as bullet points."""
        if not items:
            return "None specified"
        return "\n".join(f"- {item}" for item in items)


class ValidationStage:
    """
    Stage that validates the styled response against guardrails.

    Uses PersonalityEngine to check for guardrail violations
    and forbidden patterns in the final response.
    """

    def __init__(self, personality_engine: PersonalityEngine) -> None:
        """
        Initialize the validation stage.

        Args:
            personality_engine: Engine for validation rules
        """
        self._personality_engine = personality_engine

    @property
    def name(self) -> str:
        """Stage name."""
        return "validation"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Validate the styled response against guardrails."""
        start_time = time.time()

        if context.styled_response is None:
            raise ValueError(
                "Style transformation stage must run before validation stage"
            )

        validation_result = self._validate(context.styled_response)

        elapsed = time.time() - start_time
        metadata = context.metadata
        metadata.stages_completed.append(self.name)
        metadata.stage_timings[self.name] = elapsed
        metadata.validation_result = validation_result

        if validation_result.valid:
            logger.info(f"Response validation passed in {elapsed:.3f}s")
        else:
            logger.warning(
                f"Response validation found {len(validation_result.violations)} "
                f"violations in {elapsed:.3f}s"
            )

        return context.with_metadata(metadata)

    def _validate(self, response: str) -> ValidationResult:
        """Validate response against personality guardrails."""
        result = self._personality_engine.validate_response(response)

        return ValidationResult(
            valid=result.get("valid", True),
            violations=result.get("violations", []),
            suggestions=result.get("suggestions", []),
        )
