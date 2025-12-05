"""
AgentOS Entry Point.

This module serves as the main entry point for the Memory Personality Engine.
It configures AgentOS with:
- A personality-driven conversation agent
- Memory extraction capabilities
- Response transformation pipeline
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from agno.agent import Agent
from agno.models.google import Gemini
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb
from agno.tools import Toolkit

from src.core.config import config
from src.core.logging import CustomLogger
from src.personality.engine import PersonalityEngine
from src.pipeline.transformer import ResponseTransformer

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

gemini_key = os.environ.get("GEMINI_API_KEY", "")
if gemini_key and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = gemini_key

logger_instance = CustomLogger("main")
logger = logger_instance.get_logger()


DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "agentos_memory.db"
DEFAULT_MODEL = config.GEMINI_MODEL
DEFAULT_PERSONALITY = "calm_mentor"
class PersonalityToolkit(Toolkit):
    """Custom toolkit for personality-driven responses."""

    def __init__(
        self,
        personality_engine: PersonalityEngine,
        response_transformer: ResponseTransformer,
    ) -> None:
        super().__init__(name="personality_tools")
        self._personality_engine = personality_engine
        self._response_transformer = response_transformer
        
        # Register tools
        self.register(self.switch_personality)
        self.register(self.get_current_personality)
        self.register(self.list_personalities)
        self.register(self.get_personality_info)
        self.register(self.get_response_style_guide)

    def switch_personality(self, personality_name: str) -> str:
        """
        Switch the active personality. After switching, you MUST adopt the new 
        personality's communication style for ALL subsequent responses.

        Args:
            personality_name: Name of the personality to switch to
                (calm_mentor, witty_friend, therapist)

        Returns:
            Detailed instructions on how to respond with the new personality.
        """
        available = self._personality_engine.get_available_personalities()
        if personality_name not in available:
            return (
                f"Personality '{personality_name}' not found. "
                f"Available: {', '.join(available)}"
            )

        self._personality_engine.switch_personality(personality_name)
        logger.info(f"Switched personality to: {personality_name}")
        
        # Get the new personality's style guide
        style = self._personality_engine.get_style_context()
        personality = self._personality_engine.active_personality
        
        return (
            f"PERSONALITY SWITCHED TO: {personality_name}\n\n"
            f"YOU ARE NOW: {personality.description}\n\n"
            f"YOUR NEW COMMUNICATION STYLE:\n"
            f"- Primary tone: {style.get('tone', {}).get('primary', 'friendly')}\n"
            f"- Secondary tone: {style.get('tone', {}).get('secondary', 'supportive')}\n"
            f"- Formality: {style.get('tone', {}).get('formality', 'moderate')}\n"
            f"- Warmth: {style.get('tone', {}).get('warmth', 'warm')}\n\n"
            f"STYLE RULES TO FOLLOW:\n"
            f"{chr(10).join('- ' + rule for rule in style.get('style_rules', []))}\n\n"
            f"IMPORTANT: From now on, respond ONLY in this personality style. "
            f"Do NOT revert to calm_mentor unless explicitly asked to switch."
        )

    def get_current_personality(self) -> str:
        """
        Get the current active personality name and style guide.

        Returns:
            Current personality name with style instructions.
        """
        personality = self._personality_engine.active_personality
        style = self._personality_engine.get_style_context()
        
        return (
            f"CURRENT PERSONALITY: {personality.name}\n"
            f"Description: {personality.description}\n"
            f"Tone: {style.get('tone', {}).get('primary', 'N/A')}\n"
            f"You should respond in this style for all messages."
        )

    def get_response_style_guide(self) -> str:
        """
        Get detailed style guide for current personality. Call this before 
        responding to ensure you use the correct communication style.

        Returns:
            Complete style guide for current personality.
        """
        personality = self._personality_engine.active_personality
        style = self._personality_engine.get_style_context()
        
        return (
            f"ACTIVE PERSONALITY: {personality.name}\n"
            f"DESCRIPTION: {personality.description}\n\n"
            f"TONE:\n"
            f"- Primary: {style.get('tone', {}).get('primary', 'friendly')}\n"
            f"- Secondary: {style.get('tone', {}).get('secondary', 'supportive')}\n"
            f"- Formality: {style.get('tone', {}).get('formality', 'moderate')}\n"
            f"- Warmth: {style.get('tone', {}).get('warmth', 'warm')}\n\n"
            f"STYLE RULES:\n"
            f"{chr(10).join('- ' + rule for rule in style.get('style_rules', []))}\n\n"
            f"RESPOND IN THIS STYLE."
        )

    def list_personalities(self) -> str:
        """
        List all available personalities.

        Returns:
            Comma-separated list of available personality names.
        """
        available = self._personality_engine.get_available_personalities()
        return f"Available personalities: {', '.join(available)}"

    def get_personality_info(self, personality_name: Optional[str] = None) -> str:
        """
        Get detailed information about a personality.

        Args:
            personality_name: Name of personality to get info about.
                Defaults to active personality.

        Returns:
            Description of the personality's traits and style.
        """
        name = personality_name or self._personality_engine.active_personality.name
        
        if name not in self._personality_engine.get_available_personalities():
            return f"Personality '{name}' not found."
        
        # Get personality config
        original_personality = self._personality_engine.active_personality.name
        if name != original_personality:
            self._personality_engine.switch_personality(name)
        
        personality = self._personality_engine.active_personality
        style = self._personality_engine.get_style_context()
        if name != original_personality:
            self._personality_engine.switch_personality(original_personality)
        return (
            f"Personality: {personality.name}\n"
            f"Description: {personality.description}\n"
            f"Tone: {style.get('tone', {}).get('primary', 'N/A')}\n"
            f"Style Rules: {', '.join(style.get('style_rules', [])[:3])}"
        )

def _create_personality_toolkit(
    personality_engine: PersonalityEngine,
    response_transformer: ResponseTransformer,
) -> PersonalityToolkit:
    """Factory function to create personality toolkit instance."""
    return PersonalityToolkit(
        personality_engine=personality_engine,
        response_transformer=response_transformer,
    )

def create_personality_agent(
    name: str = "PersonalityAgent",
    personality: str = DEFAULT_PERSONALITY,
    db: Optional[SqliteDb] = None,
) -> Agent:
    """
    Create a personality-driven conversation agent.

    Args:
        name: Name of the agent
        personality: Initial personality to use
        db: Optional database for persistence

    Returns:
        Configured Agent instance
    """
    personality_engine = PersonalityEngine(default_personality=personality)
    response_transformer = ResponseTransformer(
        personality_engine=personality_engine,
        llm_model=DEFAULT_MODEL,
    )
    # Create toolkit
    toolkit = _create_personality_toolkit(personality_engine, response_transformer)
    instructions: List[str] = [
        "You are a personality-adaptive AI assistant that can switch between different communication styles.",
        "",
        "MEMORY:",
        "You have persistent memory across sessions. Remember user information like:",
        "- Names, preferences, facts they share about themselves",
        "- Previous conversations and context",
        "- User's emotional patterns and communication style preferences",
        "Always use remembered information to personalize responses.",
        "",
        "AVAILABLE PERSONALITIES:",
        "- calm_mentor: Patient, supportive teacher who guides with wisdom",
        "- witty_friend: Fun, humorous companion who uses jokes and playful banter",  
        "- therapist: Empathetic listener who validates feelings and offers emotional support",
        "",
        "AUTO-DETECTION (IMPORTANT):",
        "Automatically detect user emotional state and switch personality WITHOUT being asked:",
        "",
        "Switch to THERAPIST when user shows:",
        "- Emotional distress, anxiety, stress, overwhelm",
        "- Sadness, grief, loneliness, depression signs",
        "- Relationship problems, personal struggles",
        "- Phrases like: 'I feel...', 'I'm struggling...', 'I'm stressed...', 'I can't cope...'",
        "",
        "Switch to WITTY_FRIEND when user wants:",
        "- Fun, entertainment, jokes, humor",
        "- Casual conversation, banter, playfulness",
        "- Phrases like: 'Tell me a joke', 'I'm bored', 'Make me laugh', 'Something fun'",
        "",
        "Stay as CALM_MENTOR for:",
        "- Learning, education, explanations",
        "- Technical questions, guidance, how-to",
        "- Professional advice, structured help",
        "",
        "CRITICAL RULES:",
        "1. AUTO-SWITCH personality based on detected emotional state - don't wait to be asked",
        "2. When a user explicitly asks to switch, use the switch_personality tool IMMEDIATELY",
        "3. After switching, you MUST adopt the new style for ALL subsequent responses",
        "4. If unsure of current personality, use get_response_style_guide tool",
        "5. NEVER ignore a personality switch - it changes how you communicate",
        "6. Match the tone, humor level, and formality of the active personality",
        "",
        "PERSONALITY BEHAVIORS:",
        "- calm_mentor: Be patient, use teaching analogies, offer structured guidance",
        "- witty_friend: Use humor, casual language, jokes, playful teasing, be fun",
        "- therapist: Be empathetic, validate feelings, ask reflective questions, be gentle",
        "",
        "Remember: Your personality affects HOW you say things, not WHAT information you provide.",
    ]
    agent = Agent(
        name=name,
        model=Gemini(id=DEFAULT_MODEL),
        db=db,
        tools=[toolkit],
        description="A personality-driven AI assistant with customizable communication styles.",
        instructions=instructions,
        add_history_to_context=True,
        enable_user_memories=True,  # Enable automatic memory persistence
        markdown=True,
        debug_mode=config.DEBUG,
    )
    logger.info(f"Created personality agent '{name}' with personality '{personality}'")
    return agent

def setup_agentos() -> AgentOS:
    """
    Set up and configure AgentOS with the personality agent.

    Returns:
        Configured AgentOS instance
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Create database for memory persistence with explicit table names
    db = SqliteDb(
        db_file=str(DB_PATH),
        session_table="agent_sessions",
        memory_table="agent_memories",
    )
    logger.info(f"Initialized SQLite database at: {DB_PATH}")

    # Create the personality agent
    personality_agent = create_personality_agent(
        name="PersonalityAgent",
        personality=DEFAULT_PERSONALITY,
        db=db,
    )

    # Configure AgentOS
    agent_os = AgentOS(
        description="Memory Personality Engine - An AI assistant with customizable personality styles",
        agents=[personality_agent],
    )
    logger.info("AgentOS configured with PersonalityAgent")
    return agent_os


agent_os = setup_agentos()
app = agent_os.get_app()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

if __name__ == "__main__":
    logger.info("Starting Memory Personality Engine via AgentOS")
    logger.info(f"API Host: {config.API_HOST}, Port: {config.API_PORT}")
    logger.info(f"Default personality: {DEFAULT_PERSONALITY}")
    logger.info(f"Model: {DEFAULT_MODEL}")
    
    agent_os.serve(
        app="main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
    )