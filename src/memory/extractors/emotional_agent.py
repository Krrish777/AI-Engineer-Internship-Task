"""
Emotional analysis agent for extracting high-level emotional patterns and states.
This agent focuses on understanding the user's emotional landscape.
"""

from typing import List, Any, Type

from src.core.logging import CustomLogger
from agno.agent import Agent
from pydantic import BaseModel
from .base_classes import BaseExtractor, BaseResultProcessor
from ...models import BaseMemory
from ...models.memory.extraction import EmotionExtractionOutput

logger_instance = CustomLogger("emotional_agent")
logger = logger_instance.get_logger()

class EmotionalResultProcessor(BaseResultProcessor):
    """Processes emotional analysis results into structured data."""
    
    def process_results(
        self,
        raw_data: Any,
        user_id: str,
        session_id: str
    ) -> List[BaseMemory]:
        """
        Process emotional analysis results.
        """
        return []
    
    def extract_session_summary(self, raw_data: Any) -> str:
        """Extract session summary from emotional analysis results."""
        if hasattr(raw_data, 'overall_mood') and raw_data.overall_mood:
            return f"Overall emotional state: {raw_data.overall_mood}"
        return "No emotional mood detected"
    
    def extract_key_insights(self, raw_data: Any) -> List[str]:
        """Extract key insights from emotional analysis results."""
        insights = []
        if hasattr(raw_data, 'emotional_patterns') and raw_data.emotional_patterns:
            for pattern in raw_data.emotional_patterns:
                if hasattr(pattern, 'emotion') and hasattr(pattern, 'intensity'):
                    emotion = pattern.emotion
                    intensity = getattr(pattern, 'intensity', 0)
                    if intensity > 0.5:  # High intensity emotions
                        insights.append(f"High {emotion} detected (intensity: {intensity:.2f})")
                    
                    # Add trigger information if available
                    if hasattr(pattern, 'triggers') and pattern.triggers:
                        triggers_str = ", ".join(pattern.triggers)
                        insights.append(f"{emotion.capitalize()} triggered by: {triggers_str}")
        
        return insights if insights else ["No significant emotional patterns detected"]
    
    def extract_suggested_personality(self, raw_data: Any) -> str:
        """Extract suggested personality style from emotional analysis results."""
        if hasattr(raw_data, 'emotional_patterns') and raw_data.emotional_patterns:
            # Analyze emotional patterns to suggest personality
            emotions = []
            high_intensity_emotions = []
            
            for pattern in raw_data.emotional_patterns:
                if hasattr(pattern, 'emotion'):
                    emotion = pattern.emotion.lower()
                    emotions.append(emotion)
                    
                    # Track high intensity emotions
                    if hasattr(pattern, 'intensity') and pattern.intensity > 0.6:
                        high_intensity_emotions.append(emotion)
            
            # Personality suggestions based on emotional patterns
            if any(emotion in ['anxiety', 'stress', 'overwhelmed'] for emotion in emotions):
                return 'calm_mentor'  # Supportive for stress
            elif any(emotion in ['sadness', 'disappointment', 'grief'] for emotion in emotions):
                return 'empathetic'   # Empathetic for sadness
            elif any(emotion in ['anger', 'frustration'] for emotion in emotions):
                return 'therapist_style'  # Professional for anger
            elif any(emotion in ['joy', 'excitement', 'happiness'] for emotion in emotions):
                return 'witty_friend'  # Fun for positive emotions
            elif any(emotion in ['curiosity', 'interest'] for emotion in emotions):
                return 'analytical'   # Analytical for curiosity
        
        return "balanced"
    
class EmotionalExtractor(BaseExtractor):
    """
    Emotional analysis agent that extracts high-level emotional patterns and states.
    
    This agent focuses on:
    - Session summaries
    - Emotional pattern identification
    - Communication style analysis
    - Personality recommendation
    """
    
    def __init__(self, model, db):
        super().__init__(model, db, "emotional")
        self.processor = EmotionalResultProcessor()
        logger.info("EmotionalExtractor initialized")
        
    def _setup_agent(self) -> None:
        """Set up the Agno agent with enhanced emotional analysis configuration."""
        agent_config = {
            "model": self.model,
            "db": self.db,
            "output_schema": self._get_output_schema(),
            "instructions": self._get_enhanced_instructions(),
            "markdown": False
        }
        
        # Add enhanced context features if enabled
        if self.enable_enhanced_context:
            agent_config.update({
                "add_session_summary_to_context": True,
                "enable_session_summaries": True,
                "add_history_to_context": True,
                "num_history_runs": 3,
                "session_state": self._get_emotional_session_state(),
                "add_session_state_to_context": True,
                "enable_agentic_state": True
            })
            
            # Add knowledge base if available
            if self.knowledge:
                agent_config.update({
                    "knowledge": self.knowledge,
                    "search_knowledge": True,
                    "enable_agentic_knowledge_filters": True
                })
        
        self.agent = Agent(**agent_config)
        
    def _get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic schema for emotional analysis output."""
        return EmotionExtractionOutput
    
    def _get_categories_key(self) -> str:
        return "emotions"
    
    def _get_emotional_session_state(self) -> dict:
        """Return emotional-specific session state schema."""
        base_state = self._get_session_state_schema()
        emotional_state = {
            "current_mood_trend": "neutral",
            "dominant_emotions": [],
            "stress_indicators": [],
            "emotional_stability": 0.5,
            "personality_suggestions": [],
            "trigger_patterns": []
        }
        return {**base_state, **emotional_state}
    
    def extract(
        self,
        conversation_text: str,
        user_id: str,
        session_id: str
    ) -> List[BaseMemory]:
        """Extract emotional analysis

        Args:
            conversation_text (str): Formatted conversation text
            user_id (str): User identifier
            session_id (str): Session identifier

        Returns:
            Empty list (analysis doesn't create memory objects)
        """
        logger.info(f"Starting emotional extraction for user: {user_id}, session: {session_id}")
        return self.processor.process_results(None, user_id, session_id)
    
    async def analyze_conversation(
        self,
        conversation_text: str,
        user_id: str,
        session_id: str
    ) -> dict:
        """
        Analyze conversation and return structured insights.
        
        Args:
            conversation_text: Formatted conversation text
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Analyzing conversation for emotional insights: user {user_id}")
            
            raw_result = await self.run_extraction(conversation_text)
            
            if raw_result is None:
                logger.warning("Emotional analysis returned no results")
                return self._create_fallback_analysis()
            
            analysis_data = {
                "session_summary": self.processor.extract_session_summary(raw_result),
                "key_insights": self.processor.extract_key_insights(raw_result),
                "suggested_personality": self.processor.extract_suggested_personality(raw_result),
                "user_id": user_id,
                "session_id": session_id
            }
            
            # Add emotional patterns if available
            if hasattr(raw_result, 'emotional_patterns'):
                analysis_data['emotional_patterns'] = [
                    {
                        'emotion': getattr(pattern, 'emotion', 'unknown'),
                        'intensity': getattr(pattern, 'intensity', 0.0),
                        'triggers': getattr(pattern, 'triggers', []),
                        'confidence': getattr(pattern, 'confidence', 0.0)
                    }
                    for pattern in raw_result.emotional_patterns
                ]
            
            # Add overall mood if available
            if hasattr(raw_result, 'overall_mood'):
                analysis_data['overall_mood'] = raw_result.overall_mood
            
            logger.info(f"Emotional analysis completed for user {user_id}")
            return analysis_data
        
        except Exception as e:
            logger.error(f"Error during emotional analysis for user {user_id}: {e}")
            return self._create_fallback_analysis()
        
    def _create_fallback_analysis(self) -> dict:
        """Create a fallback analysis result in case of errors."""
        return {
            "session_summary": "Emotional analysis unavailable",
            "key_insights": ["Analysis could not be completed"],
            "suggested_personality": "balanced",
            "emotional_patterns": [],
            "overall_mood": "unknown",
            "user_id": "",
            "session_id": ""
        }
        
    def _prepare_prompt(self, conversation_text: str) -> str:
        """Prepare analysis prompt with template variables."""
        template = self.config.get("template", "Analyze the emotional content of the following conversation:\n\n{conversation_text}")
        dimensions = self.config.get("analysis_dimensions", ["emotional_states", "communication_style", "personality_recommendation"])
        
        return template.format(
            conversation_text=conversation_text,
            dimensions=", ".join(dimensions),
            **self.config
        )