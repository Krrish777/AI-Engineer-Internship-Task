"""
Conversation analysis agent for extracting high-level insights and patterns.
This agent analyzes conversations to generate session summaries, identify
behavioral patterns, and suggest appropriate personality styles.
"""

from typing import List, Any, Type
from src.core.logging import CustomLogger
from agno.agent import Agent
from pydantic import BaseModel

from .base_classes import BaseExtractor, BaseResultProcessor
from ...models import BaseMemory
from ...models.memory.extraction import ConversationAnalysisOutput

logger_instance = CustomLogger("analysis_agent")
logger = logger_instance.get_logger()


class AnalysisResultProcessor(BaseResultProcessor):
    """Processes conversation analysis results into structured data."""
    
    def process_results(
        self, 
        raw_data: Any, 
        user_id: str, 
        session_id: str
    ) -> List[BaseMemory]:
        """
        Process analysis results.
        """
        # Analysis results are typically used for orchestration
        # and don't create individual memory objects
        return []
    
    def extract_session_summary(self, raw_data: Any) -> str:
        """Extract session summary from analysis results."""
        if hasattr(raw_data, 'session_summary'):
            return raw_data.session_summary
        return "No summary available"
    
    def extract_key_insights(self, raw_data: Any) -> List[str]:
        """Extract key insights from analysis results."""
        if hasattr(raw_data, 'key_insights'):
            return raw_data.key_insights
        return []
    
    def extract_suggested_personality(self, raw_data: Any) -> str:
        """Extract suggested personality style from analysis results."""
        if hasattr(raw_data, 'suggested_personality'):
            return raw_data.suggested_personality
        
        # Fallback to behavioral patterns if available
        if hasattr(raw_data, 'behavioral_patterns'):
            patterns = raw_data.behavioral_patterns
            if patterns:
                # Simple heuristic based on patterns
                if any('analytical' in str(pattern).lower() for pattern in patterns):
                    return 'analytical'
                elif any('emotional' in str(pattern).lower() for pattern in patterns):
                    return 'empathetic'
                elif any('casual' in str(pattern).lower() for pattern in patterns):
                    return 'witty_friend'
        
        return 'balanced'


class AnalysisAgent(BaseExtractor):
    """
    Conversation analysis agent that extracts high-level insights and patterns.
    
    This agent focuses on:
    - Session summaries
    - Behavioral pattern identification
    - Communication style analysis
    - Personality recommendation
    """
    
    def __init__(self, model, db):
        super().__init__(model, db, "convoanalysis")
        self.processor = AnalysisResultProcessor()
        logger.info("AnalysisAgent initialized for conversation analysis")
    
    def _setup_agent(self) -> None:
        """Set up the Agno agent with enhanced conversation analysis configuration."""
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
                "num_history_runs": 3,  # Analysis benefits from conversation patterns
                "session_state": self._get_analysis_session_state(),
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
        logger.debug("Analysis agent configured with enhanced context features")
    
    def _get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic schema for conversation analysis output."""
        return ConversationAnalysisOutput
    
    def _get_categories_key(self) -> str:
        """Return the config key for analysis dimensions."""
        return "analysis_dimensions"
    
    def _get_analysis_session_state(self) -> dict:
        """Return analysis-specific session state schema."""
        base_state = self._get_session_state_schema()
        analysis_state = {
            "conversation_patterns": [],
            "communication_style_evolution": {},
            "topic_preferences": {},
            "engagement_metrics": {},
            "behavioral_shifts": [],
            "personality_indicators": [],
            "session_quality_score": 0.5
        }
        return {**base_state, **analysis_state}
    
    def extract(
        self, 
        conversation_text: str, 
        user_id: str, 
        session_id: str
    ) -> List[BaseMemory]:
        """
        Extract conversation analysis.
        
        Args:
            conversation_text: Formatted conversation text
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Empty list (analysis doesn't create memory objects)
        """
        logger.info(f"Starting conversation analysis for user {user_id}, session {session_id}")
        
        return self.processor.process_results(None, user_id, session_id)
    
    async def analyze_conversation(
        self, 
        conversation_text: str, 
        user_id: str, 
        session_id: str
    ) -> dict:
        """
        Analyze conversation and return structured insights with enhanced context.
        
        Args:
            conversation_text: Formatted conversation text
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Analyzing conversation patterns for user {user_id}")
            
            # Run the analysis with enhanced context
            raw_result = await self.run_extraction(conversation_text)
            
            if raw_result is None:
                logger.warning("Analysis extraction returned no results")
                return self._create_fallback_analysis()
            
            # Process the results using our specialized processor
            analysis_data = {
                'session_summary': self.processor.extract_session_summary(raw_result),
                'key_insights': self.processor.extract_key_insights(raw_result),
                'suggested_personality': self.processor.extract_suggested_personality(raw_result),
                'user_id': user_id,
                'session_id': session_id
            }
            
            # Add behavioral patterns if available
            if hasattr(raw_result, 'behavioral_patterns'):
                analysis_data['behavioral_patterns'] = raw_result.behavioral_patterns
                
                # Sync behavioral patterns to knowledge base for future context
                if self.enable_enhanced_context:
                    await self.sync_memories_to_knowledge(
                        raw_result.behavioral_patterns, 
                        user_id, 
                        session_id
                    )
            
            # Add communication style if available
            if hasattr(raw_result, 'communication_style'):
                analysis_data['communication_style'] = raw_result.communication_style
            
            logger.info(f"Analysis completed successfully for user {user_id}")
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error during conversation analysis: {e}")
            return self._create_fallback_analysis()
    
    def _create_fallback_analysis(self) -> dict:
        """Create fallback analysis when extraction fails."""
        return {
            'session_summary': 'Unable to generate session summary due to processing error.',
            'key_insights': ['Analysis could not be completed'],
            'suggested_personality': 'balanced',
            'behavioral_patterns': [],
            'communication_style': 'unknown'
        }
    
    def _prepare_prompt(self, conversation_text: str) -> str:
        """Prepare analysis prompt with template variables."""
        template = self.config.get("template", 
                                 "Analyze this conversation for insights and patterns:\n\n{conversation_text}")
        
        # Get analysis dimensions and personality styles from config
        dimensions = self.config.get("analysis_dimensions", [
            "communication_style", "engagement_level", "topic_preferences"
        ])
        personality_styles = self.config.get("personality_styles", [
            "calm_mentor", "witty_friend", "therapist_style", "balanced"
        ])
        
        return template.format(
            conversation_text=conversation_text,
            dimensions=', '.join(dimensions),
            personality_styles=', '.join(personality_styles)
        )
