from enum import Enum

class ConfidenceLevel(str, Enum):
    """Confidence levels for extracted information."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class MemoryLayer(str, Enum):
    """Memory layers inspired by mem0 architecture."""
    USER = "user"       # Cross-session user-specific information
    SESSION = "session" # Session-specific context and facts
    AGENT = "agent"     # Agent learning and behavioral patterns

class MemoryType(str, Enum):
    """Types of memories following mem0 categorization."""
    PREFERENCE = "preference"
    EMOTION = "emotion"
    FACT = "fact"
    BEHAVIOR = "behavior"
    CONTEXT = "context"
    
class PreferenceCategory(str, Enum):
    """Categories for user preferences - simplified for MVP."""
    FOOD = "food"
    COMMUNICATION = "communication"
    WORK = "work"
    LIFESTYLE = "lifestyle"
    ENTERTAINMENT = "entertainment"
    LEARNING = "learning"
    OTHER = "other"

class EmotionType(str, Enum):
    """Types of emotions - simplified for MVP."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    ANXIETY = "anxiety"
    EXCITEMENT = "excitement"
    FRUSTRATION = "frustration"
    CURIOSITY = "curiosity"
    CONTENTMENT = "contentment"
