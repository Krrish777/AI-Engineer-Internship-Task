"""
Pipeline module for response transformation.

This module provides the response transformation pipeline that:
1. Weights memory context based on personality
2. Generates factual base responses
3. Transforms responses with personality style
4. Validates against guardrails
"""

from src.pipeline.context import MemoryItem
from src.pipeline.context import PipelineContext
from src.pipeline.context import PipelineMetadata
from src.pipeline.context import TransformedResponse
from src.pipeline.context import ValidationResult
from src.pipeline.context import WeightedMemory
from src.pipeline.prompt_loader import get_base_response_prompt
from src.pipeline.prompt_loader import get_style_transformation_prompt
from src.pipeline.prompt_loader import get_validation_prompt
from src.pipeline.prompt_loader import load_pipeline_prompts
from src.pipeline.stages import BaseResponseStage
from src.pipeline.stages import MemoryWeightingStage
from src.pipeline.stages import PipelineStage
from src.pipeline.stages import StyleTransformationStage
from src.pipeline.stages import ValidationStage
from src.pipeline.transformer import ResponseTransformer

__all__ = [
    # Main transformer
    "ResponseTransformer",
    # Context types
    "PipelineContext",
    "PipelineMetadata",
    "TransformedResponse",
    "ValidationResult",
    "WeightedMemory",
    "MemoryItem",
    # Stages
    "PipelineStage",
    "MemoryWeightingStage",
    "BaseResponseStage",
    "StyleTransformationStage",
    "ValidationStage",
    # Prompt loaders
    "load_pipeline_prompts",
    "get_base_response_prompt",
    "get_style_transformation_prompt",
    "get_validation_prompt",
]
