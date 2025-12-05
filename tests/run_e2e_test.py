"""
End-to-end test runner for Memory Extraction and Personality Response Pipeline.

This script:
1. Loads 30 chat messages from sample data
2. Runs memory extraction using the orchestrator
3. Shows extracted facts, preferences, emotional patterns
4. Demonstrates before/after personality response differences
5. Saves results to JSON for demonstration
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set GOOGLE_API_KEY from GEMINI_API_KEY if not already set
if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from src.core.logging import CustomLogger
from src.memory.extractors.orchestractor import HybridMemoryOrchestrator
from src.personality.engine import PersonalityEngine
from src.pipeline.transformer import ResponseTransformer

logger_instance = CustomLogger("e2e_test")
logger = logger_instance.get_logger()


def load_chat_messages() -> dict:
    """Load sample chat messages from data directory."""
    data_path = Path(__file__).parent / "data" / "sample_chat_messages.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_conversation(messages: list) -> str:
    """Format chat messages into conversation text."""
    lines = []
    for msg in messages:
        lines.append(f"User: {msg['content']}")
    return "\n".join(lines)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_memories(memories: list, category: str) -> None:
    """Print extracted memories in a formatted way."""
    print(f"\n[{category.upper()}] - {len(memories)} items extracted:")
    print("-" * 50)
    for i, memory in enumerate(memories, 1):
        content = memory.content if hasattr(memory, 'content') else str(memory)
        confidence = memory.confidence if hasattr(memory, 'confidence') else 'N/A'
        print(f"  {i}. {content}")
        print(f"     Confidence: {confidence}")
    print()


async def run_memory_extraction(
    orchestrator: HybridMemoryOrchestrator,
    conversation: str,
    user_id: str,
    session_id: str
) -> dict:
    """Run the memory extraction pipeline."""
    print_section("PHASE 1: MEMORY EXTRACTION")
    print(f"Processing {len(conversation.split(chr(10)))} messages...")
    
    # Run extraction
    result = await orchestrator.extract_memories(
        conversation_text=conversation,
        user_id=user_id,
        session_id=session_id
    )
    
    return result


def show_extraction_results(result, expected: dict) -> None:
    """Display extraction results compared to expected."""
    print_section("EXTRACTION RESULTS")
    
    # Get memories from shared memory
    if hasattr(result, 'memories'):
        # Group by type
        factual = [m for m in result.memories if hasattr(m, 'memory_type') and 'fact' in str(m.memory_type).lower()]
        preferences = [m for m in result.memories if hasattr(m, 'memory_type') and 'prefer' in str(m.memory_type).lower()]
        emotional = [m for m in result.memories if hasattr(m, 'memory_type') and 'emotion' in str(m.memory_type).lower()]
        
        print_memories(factual, "Facts")
        print_memories(preferences, "Preferences") 
        print_memories(emotional, "Emotional Patterns")
    else:
        print("Result structure:", type(result))
        print(result)
    
    # Show expected for comparison
    print("\n[EXPECTED EXTRACTIONS]")
    print("-" * 50)
    print(f"Facts: {len(expected.get('facts', []))} expected")
    print(f"Preferences: {len(expected.get('preferences', []))} expected")
    print(f"Emotional Patterns: {len(expected.get('emotional_patterns', []))} expected")


def build_memory_context_from_extraction(result) -> dict:
    """Convert extraction result to memory context format for pipeline."""
    context = {
        "factual": {},
        "preferences": {},
        "emotional_patterns": {}
    }
    
    if hasattr(result, 'memories'):
        for i, memory in enumerate(result.memories):
            mem_type = str(getattr(memory, 'memory_type', 'unknown')).lower()
            content = getattr(memory, 'content', str(memory))
            confidence = getattr(memory, 'confidence', 0.7)
            
            if 'fact' in mem_type:
                context["factual"][f"fact_{i}"] = {"content": content, "confidence": confidence}
            elif 'prefer' in mem_type:
                context["preferences"][f"pref_{i}"] = {"content": content, "confidence": confidence}
            elif 'emotion' in mem_type:
                context["emotional_patterns"][f"emotion_{i}"] = {"content": content, "confidence": confidence}
    
    return context


async def demonstrate_personality_differences(
    transformer: ResponseTransformer,
    memory_context: dict,
    test_message: str
) -> dict:
    """Show how different personalities respond to the same message.
    
    Returns:
        Dictionary with transformation results for saving.
    """
    print_section("PHASE 2: PERSONALITY RESPONSE DIFFERENCES")
    print(f"\nTest Message: \"{test_message}\"")
    print("\nMemory Context Summary:")
    print(f"  - Factual items: {len(memory_context.get('factual', {}))}")
    print(f"  - Preference items: {len(memory_context.get('preferences', {}))}")
    print(f"  - Emotional patterns: {len(memory_context.get('emotional_patterns', {}))}")
    
    personalities = ["calm_mentor", "witty_friend", "therapist"]
    
    transformation_results = {
        "test_message": test_message,
        "memory_context_summary": {
            "factual_count": len(memory_context.get('factual', {})),
            "preferences_count": len(memory_context.get('preferences', {})),
            "emotional_count": len(memory_context.get('emotional_patterns', {}))
        },
        "personality_responses": {}
    }
    
    for personality in personalities:
        print(f"\n{'─' * 70}")
        print(f"PERSONALITY: {personality.upper()}")
        print(f"{'─' * 70}")
        
        # Show weights for this personality
        transformer.switch_personality(personality)
        engine = transformer._personality_engine
        weights = engine.get_active_weights()
        
        print("\nMemory Weights Applied:")
        print(f"  - Factual: {weights.factual}")
        print(f"  - Preferences: {weights.preferences}")
        print(f"  - Emotional: {weights.emotional_patterns}")
        
        # Get style context
        style = engine.get_style_context()
        print("\nStyle Profile:")
        print(f"  - Tone: {style['tone']['primary']} / {style['tone']['secondary']}")
        print(f"  - Formality: {style['tone']['formality']}")
        
        try:
            # Run transformation
            result = transformer.transform(
                user_message=test_message,
                memory_context=memory_context,
                personality_name=personality
            )
            
            print("\nBase Response:")
            print(f"  {result.base_response[:200]}..." if len(result.base_response) > 200 else f"  {result.base_response}")
            
            print(f"\nStyled Response ({personality}):")
            print(f"  {result.styled_response[:300]}..." if len(result.styled_response) > 300 else f"  {result.styled_response}")
            
            print(f"\nValidation: {'PASSED' if result.is_valid else 'FAILED'}")
            if not result.is_valid:
                print(f"  Violations: {result.validation.violations}")
            
            # Store results
            transformation_results["personality_responses"][personality] = {
                "weights": {
                    "factual": weights.factual,
                    "preferences": weights.preferences,
                    "emotional_patterns": weights.emotional_patterns
                },
                "style_profile": {
                    "tone_primary": style['tone']['primary'],
                    "tone_secondary": style['tone']['secondary'],
                    "formality": style['tone']['formality']
                },
                "base_response": result.base_response,
                "styled_response": result.styled_response,
                "validation_passed": result.is_valid
            }
                
        except Exception as e:
            print(f"\nError during transformation: {e}")
            logger.error(f"Transformation error for {personality}: {e}")
            transformation_results["personality_responses"][personality] = {
                "error": str(e)
            }
    
    return transformation_results


async def run_quick_personality_demo(memory_context: dict) -> dict:
    """Run a quick demo showing personality differences without full LLM calls.
    
    Returns:
        Dictionary with demo results for saving.
    """
    print_section("QUICK DEMO: MEMORY WEIGHTING BY PERSONALITY")
    
    from src.personality.engine import PersonalityEngine
    from src.pipeline.stages import MemoryWeightingStage
    from src.pipeline.context import PipelineContext, PipelineMetadata
    
    engine = PersonalityEngine()
    stage = MemoryWeightingStage(engine)
    
    test_message = "I'm feeling anxious about learning Python. Can you help?"
    
    print(f"\nTest Message: \"{test_message}\"")
    print("\nInput Memory Context:")
    print(f"  - {len(memory_context.get('factual', {}))} factual items")
    print(f"  - {len(memory_context.get('preferences', {}))} preference items")
    print(f"  - {len(memory_context.get('emotional_patterns', {}))} emotional items")
    
    demo_results = {
        "test_message": test_message,
        "memory_context_summary": {
            "factual_count": len(memory_context.get('factual', {})),
            "preferences_count": len(memory_context.get('preferences', {})),
            "emotional_count": len(memory_context.get('emotional_patterns', {}))
        },
        "personality_weights": {}
    }
    
    for personality in ["calm_mentor", "witty_friend", "therapist"]:
        engine.switch_personality(personality)
        
        context = PipelineContext(
            user_message=test_message,
            raw_memory_context=memory_context,
            metadata=PipelineMetadata(personality_name=personality)
        )
        
        result = stage.process(context)
        weights = result.weighted_memory.weights
        
        print(f"\n[{personality.upper()}]")
        print(f"  Weights: factual={weights.factual}, prefs={weights.preferences}, emotional={weights.emotional_patterns}")
        
        # Store results
        demo_results["personality_weights"][personality] = {
            "factual": weights.factual,
            "preferences": weights.preferences,
            "emotional_patterns": weights.emotional_patterns,
            "prioritizes": "FACTUAL" if weights.factual >= weights.emotional_patterns else "EMOTIONAL"
        }
        
        # Show what gets prioritized
        if weights.factual >= weights.emotional_patterns:
            print("  → Prioritizes: FACTUAL information (facts about user)")
        else:
            print("  → Prioritizes: EMOTIONAL context (user's feelings)")
    
    return demo_results


def save_results_to_json(results: dict, filename: str) -> Path:
    """Save test results to JSON file in data directory.
    
    Args:
        results: Dictionary of results to save.
        filename: Name of the output file (without extension).
    
    Returns:
        Path to the saved file.
    """
    output_path = Path(__file__).parent / "data" / f"{filename}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 Results saved to: {output_path}")
    return output_path


async def main():
    """Main entry point for the E2E test."""
    print("\n" + "=" * 70)
    print("  MEMORY EXTRACTION & PERSONALITY PIPELINE - E2E TEST")
    print("=" * 70)
    
    # Initialize results collection
    all_results = {
        "test_run_info": {
            "timestamp": datetime.now().isoformat(),
            "description": "E2E test demonstrating memory extraction and personality-based response transformation"
        },
        "quick_demo": None,
        "full_extraction": None,
        "personality_responses": None
    }
    
    # Load test data
    data = load_chat_messages()
    messages = data["chat_messages"]
    expected = data["expected_extractions"]
    metadata = data["metadata"]
    
    print(f"\nLoaded {len(messages)} chat messages")
    print(f"User ID: {metadata['user_id']}")
    print(f"Session ID: {metadata['session_id']}")
    
    all_results["test_run_info"]["messages_count"] = len(messages)
    all_results["test_run_info"]["user_id"] = metadata["user_id"]
    all_results["test_run_info"]["session_id"] = metadata["session_id"]
    
    # Format conversation
    conversation = format_conversation(messages)
    
    # Demo 1: Quick personality weighting demo (no LLM calls)
    mock_memory_context = {
        "factual": {
            "fact_1": {"content": "User's name is Alex, 28 years old", "confidence": 0.95},
            "fact_2": {"content": "Works as data analyst in San Francisco", "confidence": 0.92},
            "fact_3": {"content": "Knows Excel and SQL", "confidence": 0.85},
        },
        "preferences": {
            "pref_1": {"content": "Prefers hands-on learning", "confidence": 0.90},
            "pref_2": {"content": "Likes concise explanations", "confidence": 0.88},
            "pref_3": {"content": "Visual learner", "confidence": 0.85},
        },
        "emotional_patterns": {
            "emotion_1": {"content": "Gets frustrated when things don't work", "confidence": 0.88},
            "emotion_2": {"content": "Anxious about giving up", "confidence": 0.85},
            "emotion_3": {"content": "Motivated by small wins", "confidence": 0.90},
        }
    }
    
    quick_demo_results = await run_quick_personality_demo(mock_memory_context)
    all_results["quick_demo"] = quick_demo_results
    
    # Check for --full flag to run full extraction
    import sys
    run_full = '--full' in sys.argv
    
    # If interactive mode, ask user
    if not run_full and sys.stdin.isatty():
        print("\n" + "=" * 70)
        print("  FULL PIPELINE TEST (requires API calls)")
        print("=" * 70)
        try:
            run_full = input("\nRun full memory extraction with LLM? (y/n): ").strip().lower() == 'y'
        except EOFError:
            run_full = False
    elif run_full:
        print("\n" + "=" * 70)
        print("  FULL PIPELINE TEST (--full flag detected)")
        print("=" * 70)
    
    if run_full:
        # Initialize orchestrator
        print("\nInitializing Memory Orchestrator...")
        orchestrator = HybridMemoryOrchestrator()
        
        # Run extraction
        extraction_result = await run_memory_extraction(
            orchestrator,
            conversation,
            metadata["user_id"],
            metadata["session_id"]
        )
        
        # Show results
        show_extraction_results(extraction_result, expected)
        
        # Build memory context from extraction
        memory_context = build_memory_context_from_extraction(extraction_result)
        
        # Store extraction info
        all_results["full_extraction"] = {
            "input_messages_count": len(messages),
            "memory_context": memory_context,
            "expected_extractions": expected
        }
        
        # Demo personality differences (auto-run with --full flag)
        run_personality = True
        if sys.stdin.isatty() and '--full' not in sys.argv:
            try:
                run_personality = input("\nRun personality response demo? (y/n): ").strip().lower() == 'y'
            except EOFError:
                run_personality = True
        
        if run_personality:
            print("\nInitializing Response Transformer...")
            engine = PersonalityEngine()
            transformer = ResponseTransformer(engine)
            
            test_message = "I'm feeling anxious about learning Python. Can you help me get started?"
            
            transformation_results = await demonstrate_personality_differences(
                transformer,
                memory_context,
                test_message
            )
            all_results["personality_responses"] = transformation_results
    
    # Save results to JSON
    save_results_to_json(all_results, "e2e_test_results")
    
    print_section("TEST COMPLETE")
    print("\nSummary:")
    print("  ✓ Memory weighting demo completed")
    if run_full == 'y':
        print("  ✓ Full memory extraction completed")
        if all_results["personality_responses"]:
            print("  ✓ Personality responses generated and saved")
    print("  ✓ Results saved to data/e2e_test_results.json")
    print("\nThe pipeline successfully shows how different personalities")
    print("weight and respond to the same user context differently.")


if __name__ == "__main__":
    asyncio.run(main())
