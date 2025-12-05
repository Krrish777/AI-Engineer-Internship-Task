"""
Response transformer module.

Main orchestrator for the response transformation pipeline.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from agno.agent import Agent
from agno.models.google import Gemini

from src.core.logging import CustomLogger
from src.personality.engine import PersonalityEngine
from src.pipeline.context import PipelineContext
from src.pipeline.context import PipelineMetadata
from src.pipeline.context import TransformedResponse
from src.pipeline.context import ValidationResult
from src.pipeline.prompt_loader import get_base_response_prompt
from src.pipeline.prompt_loader import get_style_transformation_prompt
from src.pipeline.stages import BaseResponseStage
from src.pipeline.stages import MemoryWeightingStage
from src.pipeline.stages import PipelineStage
from src.pipeline.stages import StyleTransformationStage
from src.pipeline.stages import ValidationStage

logger_instance = CustomLogger("response_transformer")
logger = logger_instance.get_logger()


class ResponseTransformer:
    """
    Orchestrates the response transformation pipeline.

    Coordinates the flow through:
    1. Memory weighting (apply personality weights)
    2. Base response generation (factual LLM call)
    3. Style transformation (personality LLM call)
    4. Validation (guardrail checks)
    """

    def __init__(
        self,
        personality_engine: PersonalityEngine,
        llm_model: str = "gemini-2.0-flash",
        agent: Optional[Agent] = None,
    ) -> None:
        """
        Initialize the response transformer.

        Args:
            personality_engine: Engine for personality operations
            llm_model: Model ID for LLM calls
            agent: Optional pre-configured agent (for testing)
        """
        self._personality_engine = personality_engine
        self._llm_model = llm_model

        # Create or use provided agent
        self._agent = agent or Agent(model=Gemini(id=llm_model))

        # Load prompt templates
        self._base_response_prompt = get_base_response_prompt()
        self._style_transformation_prompt = get_style_transformation_prompt()

        # Build pipeline stages
        self._stages = self._build_stages()

        logger.info(
            f"ResponseTransformer initialized with {len(self._stages)} stages, "
            f"model: {llm_model}"
        )

    def _build_stages(self) -> List[PipelineStage]:
        """Build the pipeline stages in order."""
        return [
            MemoryWeightingStage(self._personality_engine),
            BaseResponseStage(self._agent, self._base_response_prompt),
            StyleTransformationStage(
                self._agent,
                self._personality_engine,
                self._style_transformation_prompt,
            ),
            ValidationStage(self._personality_engine),
        ]

    def transform(
        self,
        user_message: str,
        memory_context: Dict[str, Any],
        personality_name: Optional[str] = None,
    ) -> TransformedResponse:
        """
        Transform a user message through the full pipeline.

        Args:
            user_message: The user's input message
            memory_context: Retrieved memory context (factual, preferences, emotional)
            personality_name: Optional personality to use (overrides current)

        Returns:
            TransformedResponse with base, styled response and validation
        """
        # Switch personality if requested
        if personality_name:
            self._personality_engine.switch_personality(
                personality_name, trigger="transform_request"
            )

        # Initialize context
        context = PipelineContext(
            user_message=user_message,
            raw_memory_context=memory_context,
            metadata=PipelineMetadata(
                personality_name=self._personality_engine.active_personality_name
            ),
        )

        logger.info(
            f"Starting transformation pipeline for personality: "
            f"{context.metadata.personality_name}"
        )

        # Run through stages
        for stage in self._stages:
            logger.info(f"Running stage: {stage.name}")
            context = stage.process(context)

        # Build final response
        return self._build_response(context)

    def _build_response(self, context: PipelineContext) -> TransformedResponse:
        """Build the final transformed response from context."""
        validation = context.metadata.validation_result or ValidationResult(valid=True)

        return TransformedResponse(
            user_message=context.user_message,
            base_response=context.base_response or "",
            styled_response=context.styled_response or "",
            personality_name=context.metadata.personality_name,
            validation=validation,
            metadata={
                "stages_completed": context.metadata.stages_completed,
                "stage_timings": context.metadata.stage_timings,
            },
        )

    def switch_personality(self, personality_name: str) -> bool:
        """
        Switch the active personality.

        Args:
            personality_name: Name of personality to switch to

        Returns:
            True if switch was successful
        """
        return self._personality_engine.switch_personality(
            personality_name, trigger="user_request"
        )

    def get_available_personalities(self) -> List[str]:
        """Get list of available personality names."""
        return self._personality_engine.get_available_personalities()

    @property
    def active_personality(self) -> str:
        """Get the current active personality name."""
        return self._personality_engine.active_personality_name
