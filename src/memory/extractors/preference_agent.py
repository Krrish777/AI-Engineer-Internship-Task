"""
User preference extraction agent for capturing likes, dislikes, and behavioral preferences.
This agent focuses on understanding user preferences and behavioral patterns.
"""

from typing import List, Any, Type

from src.core.logging import CustomLogger
from agno.agent import Agent
from pydantic import BaseModel
from .base_classes import BaseExtractor, BaseResultProcessor
from ...models import BaseMemory
from ...models.memory.extraction import PreferenceExtractionOutput

logger_instance = CustomLogger("preference_agent")
logger = logger_instance.get_logger()

class PreferenceResultProcessor(BaseResultProcessor):
    """Processes preference extraction results into structured data."""
    
    def process_results(
        self,
        raw_data: Any,
        user_id: str,
        session_id: str
    ) -> List[BaseMemory]:
        """
        Process preference extraction results.
        """
        return []
    
    def extract_session_summary(self, raw_data: Any) -> str:
        """Extract session summary from preference analysis results."""
        if hasattr(raw_data, 'extraction_notes') and raw_data.extraction_notes:
            return f"User preferences identified: {raw_data.extraction_notes}"
        return "No specific preferences detected"
    
    def extract_key_insights(self, raw_data: Any) -> List[str]:
        """Extract key insights from preference analysis results."""
        insights = []
        if hasattr(raw_data, 'preferences') and raw_data.preferences:
            categories_count = {}
            strong_preferences = []
            
            for pref in raw_data.preferences:
                if hasattr(pref, 'category') and hasattr(pref, 'preference_value'):
                    category = pref.category
                    value = pref.preference_value
                    intensity = getattr(pref, 'intensity', 0)
                    
                    # Count categories
                    categories_count[category] = categories_count.get(category, 0) + 1
                    
                    # Track strong preferences
                    if intensity > 0.7:
                        strong_preferences.append(f"Strong {category} preference: {value}")
                    elif intensity > 0.5:
                        insights.append(f"Moderate {category} preference for {value}")
            
            # Add category insights
            if categories_count:
                top_category = max(categories_count.items(), key=lambda x: x[1])
                insights.append(f"Primary focus on {top_category[0]} preferences ({top_category[1]} items)")
            
            # Add strong preferences
            insights.extend(strong_preferences[:3])  # Top 3 strong preferences
        
        return insights if insights else ["No significant preferences detected"]
    
    def extract_suggested_personality(self, raw_data: Any) -> str:
        """Extract suggested personality style based on preferences."""
        if hasattr(raw_data, 'preferences') and raw_data.preferences:
            categories = []
            communication_prefs = []
            
            for pref in raw_data.preferences:
                if hasattr(pref, 'category') and hasattr(pref, 'preference_value'):
                    category = pref.category.lower()
                    value = pref.preference_value.lower()
                    categories.append(category)
                    
                    if category == 'communication':
                        communication_prefs.append(value)
            
            # Personality suggestions based on preference patterns
            if 'communication' in categories:
                if any(word in ' '.join(communication_prefs) for word in ['casual', 'friendly', 'informal']):
                    return 'witty_friend'
                elif any(word in ' '.join(communication_prefs) for word in ['professional', 'formal', 'business']):
                    return 'professional'
                elif any(word in ' '.join(communication_prefs) for word in ['supportive', 'caring', 'understanding']):
                    return 'empathetic'
            
            if 'learning' in categories or 'technology' in categories:
                return 'analytical'
            elif 'entertainment' in categories or 'hobbies' in categories:
                return 'witty_friend'
            elif 'work' in categories:
                return 'professional'
        
        return "balanced"

class PreferenceExtractor(BaseExtractor):
    """
    User preference extraction agent that captures likes, dislikes, and behavioral preferences.
    
    This agent focuses on:
    - Communication style preferences
    - Food, entertainment, and hobby preferences
    - Work and lifestyle preferences
    - Learning and technology preferences
    """
    
    def __init__(self, model, db):
        super().__init__(model, db, "extractor")  # Uses extractor.yaml config
        self.processor = PreferenceResultProcessor()
        logger.info("PreferenceExtractor initialized")
        
    def _setup_agent(self) -> None:
        """Set up the Agno agent with enhanced preference analysis configuration."""
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
                "num_history_runs": 4,  # Preferences benefit from history trends
                "session_state": self._get_preference_session_state(),
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
        """Return the Pydantic schema for preference extraction output."""
        return PreferenceExtractionOutput
    
    def _get_categories_key(self) -> str:
        """Return the config key for preference categories."""
        return "preference_categories"
    
    def _get_preference_session_state(self) -> dict:
        """Return preference-specific session state schema."""
        base_state = self._get_session_state_schema()
        preference_state = {
            "preference_trends": {},
            "intensity_changes": {},
            "new_preferences_discovered": [],
            "preference_conflicts": [],
            "strong_preferences": [],
            "communication_style_evolving": False,
            "lifestyle_changes_detected": False
        }
        return {**base_state, **preference_state}
    
    def extract(
        self,
        conversation_text: str,
        user_id: str,
        session_id: str
    ) -> List[BaseMemory]:
        """Extract user preferences

        Args:
            conversation_text (str): Formatted conversation text
            user_id (str): User identifier
            session_id (str): Session identifier

        Returns:
            Empty list (analysis doesn't create memory objects)
        """
        logger.info(f"Starting preference extraction for user: {user_id}, session: {session_id}")
        return self.processor.process_results(None, user_id, session_id)
    
    async def analyze_conversation(
        self,
        conversation_text: str,
        user_id: str,
        session_id: str
    ) -> dict:
        """
        Analyze conversation and extract user preferences.
        
        Args:
            conversation_text: Formatted conversation text
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary with preference analysis results
        """
        try:
            logger.info(f"Analyzing conversation for user preferences: user {user_id}")
            
            raw_result = await self.run_extraction(conversation_text)
            
            if raw_result is None:
                logger.warning("Preference analysis returned no results")
                return self._create_fallback_analysis()
            
            analysis_data = {
                "session_summary": self.processor.extract_session_summary(raw_result),
                "key_insights": self.processor.extract_key_insights(raw_result),
                "suggested_personality": self.processor.extract_suggested_personality(raw_result),
                "user_id": user_id,
                "session_id": session_id
            }
            
            # Add preferences if available
            if hasattr(raw_result, 'preferences'):
                analysis_data['preferences'] = [
                    {
                        'category': getattr(pref, 'category', 'unknown'),
                        'preference_value': getattr(pref, 'preference_value', 'unknown'),
                        'intensity': getattr(pref, 'intensity', 0.0),
                        'confidence': getattr(pref, 'confidence', 0.0),
                        'evidence': getattr(pref, 'evidence', [])
                    }
                    for pref in raw_result.preferences
                ]
            
            # Add extraction notes if available
            if hasattr(raw_result, 'extraction_notes'):
                analysis_data['extraction_notes'] = raw_result.extraction_notes
            
            logger.info(f"Preference analysis completed for user {user_id}")
            return analysis_data
        
        except Exception as e:
            logger.error(f"Error during preference analysis for user {user_id}: {e}")
            return self._create_fallback_analysis()
        
    def _create_fallback_analysis(self) -> dict:
        """Create a fallback analysis result in case of errors."""
        return {
            "session_summary": "Preference analysis unavailable",
            "key_insights": ["Analysis could not be completed"],
            "suggested_personality": "balanced",
            "preferences": [],
            "extraction_notes": "Error during extraction",
            "user_id": "",
            "session_id": ""
        }
        
    def _prepare_prompt(self, conversation_text: str) -> str:
        """Prepare analysis prompt with template variables."""
        template = self.config.get("template", "Extract user preferences from this conversation:\n\n{conversation_text}")
        categories = self.config.get("preference_categories", ["communication", "food", "entertainment", "work", "lifestyle"])
        intensity_levels = self.config.get("intensity_levels", ["strong", "moderate", "mild"])
        
        # Prepare template variables to avoid naming conflicts
        template_vars = {
            "conversation_text": conversation_text,
            "categories": ", ".join(categories),
            "intensity_levels": ", ".join(intensity_levels)
        }
        
        return template.format(**template_vars)
