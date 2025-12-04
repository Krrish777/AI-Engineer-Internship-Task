"""
Factual information extraction agent for capturing verifiable facts and personal information.
This agent focuses on extracting concrete, factual data from conversations.
"""

from typing import List, Any, Type

from src.core.logging import CustomLogger
from agno.agent import Agent
from pydantic import BaseModel
from .base_classes import BaseExtractor, BaseResultProcessor
from ...models import BaseMemory
from ...models.memory.extraction import FactExtractionOutput

logger_instance = CustomLogger("factual_agent")
logger = logger_instance.get_logger()

class FactualResultProcessor(BaseResultProcessor):
    """Processes factual extraction results into structured data."""
    
    def process_results(
        self,
        raw_data: Any,
        user_id: str,
        session_id: str
    ) -> List[BaseMemory]:
        """
        Process factual extraction results.
        """
        return []
    
    def extract_session_summary(self, raw_data: Any) -> str:
        """Extract session summary from factual analysis results."""
        if hasattr(raw_data, 'extraction_notes') and raw_data.extraction_notes:
            return f"Factual information extracted: {raw_data.extraction_notes}"
        return "No factual information extracted"
    
    def extract_key_insights(self, raw_data: Any) -> List[str]:
        """Extract key insights from factual analysis results."""
        insights = []
        if hasattr(raw_data, 'facts') and raw_data.facts:
            for fact in raw_data.facts:
                if hasattr(fact, 'content') and hasattr(fact, 'category'):
                    content = fact.content
                    category = fact.category
                    confidence = getattr(fact, 'confidence', 0)
                    
                    if confidence > 0.7:  # High confidence facts
                        insights.append(f"High-confidence {category}: {content[:50]}...")
                    elif confidence > 0.5:
                        insights.append(f"Verified {category} information found")
        
        return insights if insights else ["No significant factual information detected"]
    
    def extract_suggested_personality(self, raw_data: Any) -> str:
        """Extract suggested personality style based on factual content."""
        if hasattr(raw_data, 'facts') and raw_data.facts:
            categories = []
            professional_indicators = 0
            personal_indicators = 0
            
            for fact in raw_data.facts:
                if hasattr(fact, 'category'):
                    category = fact.category.lower()
                    categories.append(category)
                    
                    if category in ['professional', 'work', 'career', 'skills']:
                        professional_indicators += 1
                    elif category in ['personal_info', 'relationships', 'hobbies', 'goals']:
                        personal_indicators += 1
            
            # Personality suggestions based on fact types
            if professional_indicators > personal_indicators:
                return 'professional'  # More work-focused
            elif 'goals' in categories or 'achievements' in categories:
                return 'supportive'    # Achievement-oriented
            elif 'relationships' in categories:
                return 'empathetic'    # Relationship-focused
            elif 'knowledge' in categories:
                return 'analytical'    # Knowledge-focused
        
        return "balanced"

class FactualExtractor(BaseExtractor):
    """
    Factual information extraction agent that captures verifiable facts and personal information.
    
    This agent focuses on:
    - Personal information and background
    - Professional details and skills
    - Goals and achievements
    - Verifiable facts and knowledge
    """
    
    def __init__(self, model, db):
        super().__init__(model, db, "factual")
        self.processor = FactualResultProcessor()
        logger.info("FactualExtractor initialized")
        
    def _setup_agent(self) -> None:
        """Set up the Agno agent with enhanced factual analysis configuration."""
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
                "num_history_runs": 5,  # Facts benefit from more history
                "session_state": self._get_factual_session_state(),
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
        """Return the Pydantic schema for factual extraction output."""
        return FactExtractionOutput
    
    def _get_categories_key(self) -> str:
        """Return the config key for fact categories."""
        return "fact_categories"
    
    def _get_factual_session_state(self) -> dict:
        """Return factual-specific session state schema."""
        base_state = self._get_session_state_schema()
        factual_state = {
            "verified_facts_count": 0,
            "reliability_threshold": 0.8,
            "professional_info_complete": False,
            "personal_info_complete": False,
            "fact_categories_covered": [],
            "conflicting_facts": [],
            "high_confidence_facts": []
        }
        return {**base_state, **factual_state}
    
    def extract(
        self,
        conversation_text: str,
        user_id: str,
        session_id: str
    ) -> List[BaseMemory]:
        """Extract factual information

        Args:
            conversation_text (str): Formatted conversation text
            user_id (str): User identifier
            session_id (str): Session identifier

        Returns:
            Empty list (analysis doesn't create memory objects)
        """
        logger.info(f"Starting factual extraction for user: {user_id}, session: {session_id}")
        return self.processor.process_results(None, user_id, session_id)
    
    async def analyze_conversation(
        self,
        conversation_text: str,
        user_id: str,
        session_id: str
    ) -> dict:
        """
        Analyze conversation and extract factual information.
        
        Args:
            conversation_text: Formatted conversation text
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary with factual analysis results
        """
        try:
            logger.info(f"Analyzing conversation for factual information: user {user_id}")
            
            raw_result = await self.run_extraction(conversation_text)
            
            if raw_result is None:
                logger.warning("Factual analysis returned no results")
                return self._create_fallback_analysis()
            
            analysis_data = {
                "session_summary": self.processor.extract_session_summary(raw_result),
                "key_insights": self.processor.extract_key_insights(raw_result),
                "suggested_personality": self.processor.extract_suggested_personality(raw_result),
                "user_id": user_id,
                "session_id": session_id
            }
            
            # Add factual information if available
            if hasattr(raw_result, 'facts'):
                analysis_data['facts'] = [
                    {
                        'content': getattr(fact, 'content', 'unknown'),
                        'category': getattr(fact, 'category', 'general'),
                        'confidence': getattr(fact, 'confidence', 0.0),
                        'evidence': getattr(fact, 'evidence', [])
                    }
                    for fact in raw_result.facts
                ]
            
            # Add extraction notes if available
            if hasattr(raw_result, 'extraction_notes'):
                analysis_data['extraction_notes'] = raw_result.extraction_notes
            
            logger.info(f"Factual analysis completed for user {user_id}")
            return analysis_data
        
        except Exception as e:
            logger.error(f"Error during factual analysis for user {user_id}: {e}")
            return self._create_fallback_analysis()
        
    def _create_fallback_analysis(self) -> dict:
        """Create a fallback analysis result in case of errors."""
        return {
            "session_summary": "Factual analysis unavailable",
            "key_insights": ["Analysis could not be completed"],
            "suggested_personality": "balanced",
            "facts": [],
            "extraction_notes": "Error during extraction",
            "user_id": "",
            "session_id": ""
        }
        
    def _prepare_prompt(self, conversation_text: str) -> str:
        """Prepare analysis prompt with template variables."""
        template = self.config.get("template", "Extract factual information from this conversation:\n\n{conversation_text}")
        categories = self.config.get("fact_categories", ["personal_info", "professional", "goals", "experiences"])
        reliability_levels = self.config.get("reliability_levels", ["verified", "likely", "claimed"])
        
        # Prepare template variables to avoid naming conflicts
        template_vars = {
            "conversation_text": conversation_text,
            "categories": ", ".join(categories),
            "reliability_levels": ", ".join(reliability_levels)
        }
        
        return template.format(**template_vars)
