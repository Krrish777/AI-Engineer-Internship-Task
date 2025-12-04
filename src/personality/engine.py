"""
Personality Engine - Post-processing layer for response styling.

This engine applies personality-specific transformations to base responses
without altering the underlying reasoning or factual content.

Key responsibilities:
- Load and manage personality configurations
- Apply memory weights based on active personality
- Transform response style while preserving accuracy
- Enforce personality guardrails
- Handle personality switching
"""

from typing import Dict
from typing import Any
from typing import Optional
from typing import List
from datetime import datetime

from src.core.logging import CustomLogger
from .models import PersonalityConfig
from .models import MemoryWeights
from .models import WeightedMemoryContext
from .models import PersonalityState
from .models import PersonalitySwitchEvent
from .models import ToneConfig
from .models import ResponsePatterns
from .config_loader import load_all_personalities
from .config_loader import get_default_personality
from .config_loader import validate_personality_config

logger_instance = CustomLogger("personality_engine")
logger = logger_instance.get_logger()


class PersonalityEngine:
    """
    Post-processing engine for personality-based response styling.
    
    This is NOT an agent - it's a stateless transformer that applies
    personality styling to base responses without altering facts or reasoning.
    
    Architecture position:
        Extraction System -> Base Reasoning -> [PersonalityEngine] -> Final Output
    """
    
    def __init__(self, default_personality: Optional[str] = None):
        """
        Initialize the personality engine.
        
        Args:
            default_personality: Name of default personality to use.
                               Falls back to config default if not specified.
        """
        self._personalities: Dict[str, PersonalityConfig] = {}
        self._active_personality_name: str = default_personality or get_default_personality()
        self._state = PersonalityState(
            active_personality=self._active_personality_name,
            available_personalities=[],
            switch_history=[]
        )
        self._user_override: Optional[str] = None
        
        self._load_all_personalities()
        logger.info(
            f"PersonalityEngine initialized with {len(self._personalities)} personalities, active: {self._active_personality_name}"
        )
    
    def _load_all_personalities(self) -> None:
        """Load all available personality configurations."""
        raw_configs = load_all_personalities()
        
        for name, raw_config in raw_configs.items():
            try:
                if validate_personality_config(raw_config):
                    config = self._parse_personality_config(raw_config)
                    self._personalities[name] = config
                    logger.info(f"Loaded personality: {name}")
            except Exception as e:
                logger.warning(f"Failed to parse personality {name}: {e}")
        
        self._state.available_personalities = list(self._personalities.keys())
        
        # Ensure active personality is loaded
        if self._active_personality_name not in self._personalities:
            available = list(self._personalities.keys())
            if available:
                self._active_personality_name = available[0]
                logger.warning(
                    f"Default personality not found, falling back to: {self._active_personality_name}"
                )
            else:
                logger.error("No personalities loaded")
    
    def _parse_personality_config(self, raw_config: Dict[str, Any]) -> PersonalityConfig:
        """Parse raw config dictionary into PersonalityConfig model."""
        tone_data = raw_config.get("tone", {})
        tone = ToneConfig(
            primary=tone_data.get("primary", "neutral"),
            secondary=tone_data.get("secondary", "neutral"),
            formality=tone_data.get("formality", "moderate"),
            warmth=tone_data.get("warmth", "moderate")
        )
        
        weights_data = raw_config.get("memory_weights", {})
        weights = MemoryWeights(
            factual=weights_data.get("factual", 1.0),
            preferences=weights_data.get("preferences", 0.5),
            emotional_patterns=weights_data.get("emotional_patterns", 0.5)
        )
        
        patterns_data = raw_config.get("response_patterns", {})
        patterns = ResponsePatterns(
            opening=patterns_data.get("opening", []),
            transitions=patterns_data.get("transitions", []),
            closing=patterns_data.get("closing", [])
        )
        
        return PersonalityConfig(
            name=raw_config.get("name", "unknown"),
            description=raw_config.get("description", ""),
            tone=tone,
            style_rules=raw_config.get("style_rules", []),
            memory_weights=weights,
            response_patterns=patterns,
            guardrails=raw_config.get("guardrails", []),
            forbidden=raw_config.get("forbidden", []),
            context_priorities=raw_config.get("context_priorities", []),
            safety_protocols=raw_config.get("safety_protocols", [])
        )
    
    @property
    def active_personality(self) -> PersonalityConfig:
        """Get the currently active personality configuration."""
        return self._personalities[self._active_personality_name]
    
    @property
    def active_personality_name(self) -> str:
        """Get the name of the currently active personality."""
        return self._active_personality_name
    
    def get_available_personalities(self) -> List[str]:
        """Get list of available personality names."""
        return list(self._personalities.keys())
    
    def switch_personality(
        self, 
        personality_name: str, 
        trigger: str = "user_request"
    ) -> bool:
        """
        Switch to a different personality.
        
        This does NOT reset memory - only changes the active persona.
        
        Args:
            personality_name: Name of personality to switch to
            trigger: What triggered the switch (user_request, auto_detect, etc.)
            
        Returns:
            True if switch was successful, False otherwise
        """
        if personality_name not in self._personalities:
            logger.warning(f"Attempted to switch to unknown personality: {personality_name}")
            return False
        
        previous = self._active_personality_name
        self._active_personality_name = personality_name
        
        # Record the switch event
        switch_event = PersonalitySwitchEvent(
            from_personality=previous,
            to_personality=personality_name,
            trigger=trigger,
            timestamp=datetime.now().isoformat()
        )
        self._state.switch_history.append(switch_event)
        self._state.active_personality = personality_name
        
        if trigger == "user_request":
            self._user_override = personality_name
        
        logger.info(
            f"Switched personality from {previous} to {personality_name} (trigger: {trigger})"
        )
        return True
    
    def set_user_preference(self, personality_name: Optional[str]) -> None:
        """
        Set user's explicit personality preference.
        
        User preference overrides auto-detection.
        
        Args:
            personality_name: User's preferred personality, or None to clear
        """
        if personality_name and personality_name not in self._personalities:
            logger.warning(f"Invalid user preference personality: {personality_name}")
            return
        
        self._user_override = personality_name
        self._state.user_preference = personality_name
        
        if personality_name:
            self.switch_personality(personality_name, trigger="user_preference")
        
        logger.info(f"User preference set to: {personality_name or 'none'}")
    
    def apply_memory_weights(
        self, 
        memory_context: Dict[str, Any]
    ) -> WeightedMemoryContext:
        """
        Apply personality-specific weights to memory context.
        
        All personalities have access to all memory types,
        but weights determine how much each type influences responses.
        
        Args:
            memory_context: Raw memory context with factual, preferences, emotional_patterns
            
        Returns:
            WeightedMemoryContext with personality-specific weights applied
        """
        weights = self.active_personality.memory_weights
        
        # Extract memory components
        factual = memory_context.get("factual", {})
        preferences = memory_context.get("preferences", {})
        emotional = memory_context.get("emotional_patterns", {})
        
        # Apply weights by scoring/filtering based on weight values
        weighted_factual = self._apply_weight_to_memories(factual, weights.factual)
        weighted_preferences = self._apply_weight_to_memories(preferences, weights.preferences)
        weighted_emotional = self._apply_weight_to_memories(emotional, weights.emotional_patterns)
        
        weighted_context = WeightedMemoryContext(
            factual=weighted_factual,
            preferences=weighted_preferences,
            emotional_patterns=weighted_emotional,
            weights_applied=weights
        )
        
        logger.debug(
            f"Applied memory weights - factual: {weights.factual:.2f}, preferences: {weights.preferences:.2f}, emotional: {weights.emotional_patterns:.2f}"
        )
        
        return weighted_context
    
    def _apply_weight_to_memories(
        self, 
        memories: Dict[str, Any], 
        weight: float
    ) -> Dict[str, Any]:
        """
        Apply weight to a set of memories.
        
        Higher weights mean more of the memory content is included.
        Lower weights filter out lower-confidence items.
        
        Args:
            memories: Dictionary of memory items
            weight: Weight to apply (0.0 to 1.0)
            
        Returns:
            Filtered/weighted memory dictionary
        """
        if weight >= 0.9:
            # High weight: include everything
            return memories
        elif weight >= 0.6:
            # Medium weight: include items with confidence > 0.5
            return {
                k: v for k, v in memories.items()
                if self._get_confidence(v) > 0.5
            }
        elif weight >= 0.3:
            # Low weight: only high-confidence items
            return {
                k: v for k, v in memories.items()
                if self._get_confidence(v) > 0.7
            }
        else:
            # Very low weight: only very high confidence
            return {
                k: v for k, v in memories.items()
                if self._get_confidence(v) > 0.9
            }
    
    def _get_confidence(self, memory_item: Any) -> float:
        """Extract confidence score from memory item."""
        if isinstance(memory_item, dict):
            return memory_item.get("confidence", 0.5)
        if hasattr(memory_item, "confidence"):
            return memory_item.confidence
        return 0.5
    
    def get_style_context(self) -> Dict[str, Any]:
        """
        Get styling context for the active personality.
        
        Returns context that can be used to guide response generation
        without including the full transformation logic.
        
        Returns:
            Dictionary with tone, style rules, and patterns
        """
        persona = self.active_personality
        
        return {
            "personality_name": persona.name,
            "tone": {
                "primary": persona.tone.primary,
                "secondary": persona.tone.secondary,
                "formality": persona.tone.formality,
                "warmth": persona.tone.warmth
            },
            "style_rules": persona.style_rules,
            "response_patterns": {
                "opening": persona.response_patterns.opening,
                "transitions": persona.response_patterns.transitions,
                "closing": persona.response_patterns.closing
            },
            "guardrails": persona.guardrails,
            "forbidden": persona.forbidden
        }
    
    def get_transformation_prompt(self, base_response: str) -> str:
        """
        Generate a prompt for transforming a base response with personality styling.
        
        This is used when the transformation is done via LLM call.
        
        Args:
            base_response: The factually correct base response to transform
            
        Returns:
            Prompt string for LLM-based transformation
        """
        persona = self.active_personality
        
        style_rules_text = "\n".join(f"- {rule}" for rule in persona.style_rules)
        guardrails_text = "\n".join(f"- {g}" for g in persona.guardrails)
        forbidden_text = "\n".join(f"- {f}" for f in persona.forbidden)
        
        prompt = f"""Transform the following response to match the {persona.name} personality.

PERSONALITY: {persona.description}

TONE:
- Primary: {persona.tone.primary}
- Secondary: {persona.tone.secondary}
- Formality: {persona.tone.formality}
- Warmth: {persona.tone.warmth}

STYLE RULES:
{style_rules_text}

GUARDRAILS (must follow):
{guardrails_text}

FORBIDDEN (never do):
{forbidden_text}

ORIGINAL RESPONSE:
{base_response}

INSTRUCTIONS:
1. Preserve all factual content exactly
2. Apply the personality's tone and style
3. Follow all guardrails
4. Avoid all forbidden behaviors
5. Do not add new facts or remove existing ones

TRANSFORMED RESPONSE:"""
        
        return prompt
    
    def validate_response(self, response: str) -> Dict[str, Any]:
        """
        Validate a response against personality guardrails.
        
        Args:
            response: Response text to validate
            
        Returns:
            Dictionary with validation result and any violations
        """
        persona = self.active_personality
        violations = []
        
        response_lower = response.lower()
        
        # Check for forbidden patterns (simple heuristic check)
        forbidden_indicators = {
            "sarcasm": ["obviously", "duh", "no kidding"],
            "dismissive": ["just do", "simply", "easy, just"],
            "toxic_positivity": ["at least", "could be worse", "look on the bright side"],
        }
        
        for forbidden_item in persona.forbidden:
            forbidden_key = forbidden_item.lower().replace(" ", "_")
            if forbidden_key in forbidden_indicators:
                for indicator in forbidden_indicators[forbidden_key]:
                    if indicator in response_lower:
                        violations.append({
                            "type": "forbidden_pattern",
                            "rule": forbidden_item,
                            "indicator": indicator
                        })
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "personality": persona.name
        }
    
    def get_state(self) -> PersonalityState:
        """Get current personality engine state."""
        return self._state
    
    def suggest_personality(
        self, 
        user_message: str, 
        emotional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Suggest appropriate personality based on context.
        
        This is auto-detection - it suggests but doesn't override user preference.
        
        Args:
            user_message: The user's current message
            emotional_context: Optional emotional context from memory
            
        Returns:
            Suggested personality name
        """
        # If user has explicit preference, respect it
        if self._user_override:
            return self._user_override
        
        message_lower = user_message.lower()
        
        # Simple heuristic detection
        emotional_keywords = [
            "feeling", "felt", "sad", "anxious", "worried", "scared",
            "upset", "angry", "frustrated", "overwhelmed", "stressed",
            "depressed", "lonely", "hurt"
        ]
        
        guidance_keywords = [
            "how do i", "help me", "advice", "should i", "what should",
            "guide", "teach", "explain", "learn", "understand"
        ]
        
        casual_keywords = [
            "hey", "hi", "what's up", "cool", "awesome", "fun",
            "haha", "lol", "joke", "funny"
        ]
        
        # Score each personality
        emotional_score = sum(1 for kw in emotional_keywords if kw in message_lower)
        guidance_score = sum(1 for kw in guidance_keywords if kw in message_lower)
        casual_score = sum(1 for kw in casual_keywords if kw in message_lower)
        
        # Add emotional context weight
        if emotional_context:
            intensity = emotional_context.get("intensity", 0)
            if intensity > 0.7:
                emotional_score += 3
        
        # Determine suggestion
        if emotional_score > guidance_score and emotional_score > casual_score:
            suggestion = "therapist"
        elif guidance_score > casual_score:
            suggestion = "calm_mentor"
        elif casual_score > 0:
            suggestion = "witty_friend"
        else:
            suggestion = self._active_personality_name
        
        # Ensure suggested personality exists
        if suggestion not in self._personalities:
            suggestion = get_default_personality()
        
        logger.debug(
            f"Personality suggestion: {suggestion} (emotional: {emotional_score}, guidance: {guidance_score}, casual: {casual_score})"
        )
        
        return suggestion
