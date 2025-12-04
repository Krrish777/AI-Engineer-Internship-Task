"""
Abstract base classes for memory extraction agents.
This module defines the common interface and shared functionality
for all memory extraction agents following mem0 patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Type
from datetime import datetime
from src.core.logging import CustomLogger
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.vectordb.lancedb import LanceDb
from pydantic import BaseModel

from ...models import BaseMemory, MemoryExtractionOutput
from ...utils.config_loader import load_prompt_config

logger_instance = CustomLogger("memory_extractors")
logger = logger_instance.get_logger()


class BaseExtractor(ABC):
    """
    Abstract base class for all memory extractors.
    
    Defines the common interface that all extractors must implement
    and provides shared utility methods.
    """
    
    def __init__(self, model: Gemini, db: SqliteDb, config_name: str, enable_enhanced_context: bool = True):
        self.model = model
        self.db = db
        self.config_name = config_name
        self.config = load_prompt_config(config_name)
        self.enable_enhanced_context = enable_enhanced_context
        self.agent: Agent
        self.knowledge: Optional[Knowledge] = None
        
        # Initialize knowledge base for enhanced context
        if enable_enhanced_context:
            self._setup_knowledge_base()
        
        # Initialize the agent
        self._setup_agent()
        
        logger.info(f"{self.__class__.__name__} initialized with config: {config_name}")
    
    def _setup_knowledge_base(self) -> None:
        """Set up knowledge base for enhanced context retrieval."""
        try:
            # Create Gemini embedder to use the same model family
            embedder = GeminiEmbedder(
                api_key=self.model.api_key  # Use the same API key
            )
            
            vector_db = LanceDb(
                table_name=f"memories_{self.config_name}",
                uri="data/knowledge",
                embedder=embedder
            )
            self.knowledge = Knowledge(
                name=f"{self.config_name.title()} Memory Base",
                description=f"Knowledge base for {self.config_name} memory extraction",
                vector_db=vector_db
            )
            logger.info(f"Knowledge base initialized for {self.config_name} with Gemini embedder")
        except Exception as e:
            logger.warning(f"Failed to initialize knowledge base: {e}")
            self.knowledge = None
    
    @abstractmethod
    def _setup_agent(self) -> None:
        """Set up the Agno agent with appropriate configuration."""
        pass
    
    @abstractmethod
    def _get_output_schema(self) -> Type[BaseModel]:
        """Return the Pydantic schema for structured output."""
        pass
    
    @abstractmethod
    def extract(
        self, 
        conversation_text: str, 
        user_id: str, 
        session_id: str
    ) -> List[BaseMemory]:
        """
        Extract memories from conversation text.
        
        Args:
            conversation_text: Formatted conversation text
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            List of extracted memory objects
        """
        pass
    
    def _get_instructions(self) -> List[str]:
        """Get instructions from config with fallback."""
        return self.config.get("instructions", [
            f"You are a {self.config_name} extraction agent.",
            "Extract relevant information from conversations.",
            "Provide confidence scores based on evidence strength."
        ])
    
    def _prepare_prompt(self, conversation_text: str) -> str:
        """Prepare the prompt for the agent."""
        template = self.config.get("template", "Extract information from:\n\n{conversation_text}")
        
        # Replace template variables
        return template.format(
            conversation_text=conversation_text,
            categories=self.config.get(self._get_categories_key(), []),
            **self.config
        )
    
    @abstractmethod
    def _get_categories_key(self) -> str:
        """Return the config key for categories (e.g., 'emotions', 'fact_categories')."""
        pass
    
    def _get_session_state_schema(self) -> Dict[str, Any]:
        """Return initial session state schema for this extractor type."""
        return {
            "extraction_count": 0,
            "confidence_threshold": 0.7,
            "last_extraction_timestamp": None
        }
    
    def _get_enhanced_instructions(self) -> List[str]:
        """Get enhanced instructions that include context awareness."""
        base_instructions = self._get_instructions()
        
        if self.enable_enhanced_context:
            context_instructions = [
                "Use previous session summaries to understand user patterns and evolution over time.",
                "Reference stored memories to avoid redundant extraction and build upon existing knowledge.",
                "Consider session state to adapt extraction based on current conversation flow.",
                "When applicable, use knowledge base filtering to find relevant past insights."
            ]
            return base_instructions + context_instructions
        
        return base_instructions
    
    async def run_extraction(self, conversation_text: str) -> Any:
        """Run the agent extraction with error handling."""
        try:
            prompt = self._prepare_prompt(conversation_text)
            result = await self.agent.arun(prompt)
            return result.content
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__} extraction: {e}")
            return None
    
    async def sync_memories_to_knowledge(self, memories: List[Any], user_id: str, session_id: str) -> None:
        """Sync extracted memories to knowledge base for future context."""
        if not self.knowledge or not memories:
            return
        
        try:
            for memory in memories:
                memory_content = {
                    "content": str(memory),
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "extractor_type": self.config_name,
                        "timestamp": datetime.now().isoformat(),
                        "confidence": getattr(memory, "confidence", 0.8)
                    }
                }
                
                await self.knowledge.add_content_async(memory_content)
            
            logger.info(f"Synced {len(memories)} memories to knowledge base")
        except Exception as e:
            logger.error(f"Failed to sync memories to knowledge base: {e}")


class BaseAgentManager(ABC):
    """
    Abstract base class for managing multiple extraction agents.
    
    Provides orchestration and coordination between different
    specialized extraction agents.
    """
    
    def __init__(self, model: Gemini, db: SqliteDb):
        self.model = model
        self.db = db
        self.agents: Dict[str, BaseExtractor] = {}
        
        # Initialize all agents
        self._setup_agents()
        
        logger.info(f"{self.__class__.__name__} initialized with {len(self.agents)} agents")
    
    @abstractmethod
    def _setup_agents(self) -> None:
        """Set up all specialized extraction agents."""
        pass
    
    @abstractmethod
    async def extract_all(
        self, 
        messages: List[Dict[str, str]], 
        user_id: str, 
        session_id: str,
        agent_id: Optional[str] = None
    ) -> MemoryExtractionOutput:
        """
        Extract all types of memories from a conversation.
        
        Args:
            messages: List of conversation messages
            user_id: User identifier
            session_id: Session identifier
            agent_id: Optional agent identifier
            
        Returns:
            Complete memory extraction output
        """
        pass
    
    def _prepare_conversation_text(self, messages: List[Dict[str, str]]) -> str:
        """Prepare conversation text for analysis."""
        conversation_lines = []
        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", "")
            conversation_lines.append(f"[{i+1}] {role.upper()}: {content}")
        
        return "\n".join(conversation_lines)
    
    def _calculate_overall_confidence(self, memories: List[List[BaseMemory]]) -> float:
        """Calculate overall confidence score from all extracted memories."""
        all_confidences = []
        for memory_list in memories:
            all_confidences.extend([m.confidence for m in memory_list])
        
        return sum(all_confidences) / len(all_confidences) if all_confidences else 0.0


class BaseResultProcessor(ABC):
    """
    Abstract base class for processing extraction results.
    
    Converts raw agent outputs into structured memory objects.
    """
    
    @abstractmethod
    def process_results(
        self, 
        raw_data: Any, 
        user_id: str, 
        session_id: str
    ) -> List[BaseMemory]:
        """
        Process raw extraction data into memory objects.
        
        Args:
            raw_data: Raw output from agent
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            List of processed memory objects
        """
        pass
    
    def _safe_getattr(self, obj: Any, attr: str, default: Any = None) -> Any:
        """Safely get attribute with fallback."""
        return getattr(obj, attr, default) if hasattr(obj, attr) else default
    
    def _create_base_memory_data(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Create base data common to all memory types."""
        return {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
