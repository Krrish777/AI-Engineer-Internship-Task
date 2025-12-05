"""
Advanced Multi-Agent Memory Extraction Orchestrator.

This implements a hybrid memory architecture with:
- Parallel processing across specialized agents
- Private agent memory for internal reasoning
- Shared consensus memory for verified conclusions
- Controlled cross-domain influence without memory conflation
- Explicit consensus building with conflict resolution
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import os
from dataclasses import dataclass

from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.team import Team

from src.core.logging import CustomLogger
from src.core.config import config
from src.utils.config_loader import load_app_config, get_model_config
from src.models import BaseMemory, MemoryExtractionOutput
from .base_classes import BaseExtractor
from .emotional_agent import EmotionalExtractor
from .factual_agent import FactualExtractor
from .preference_agent import PreferenceExtractor
from .analysis_agent import AnalysisAgent

logger_instance = CustomLogger("memory_orchestrator")
logger = logger_instance.get_logger()


@dataclass
class ConflictResolution:
    """Represents a conflict resolution between agents."""
    conflict_type: str
    agents_involved: List[str]
    original_values: Dict[str, Any]
    resolved_value: Any
    resolution_method: str
    confidence_score: float
    timestamp: datetime


@dataclass
class AgentOutput:
    """Structured output from individual agent processing."""
    agent_name: str
    raw_extractions: List[Any]
    confidence_scores: Dict[str, float]
    reasoning_traces: List[str]
    filtered_conclusions: List[BaseMemory]
    processing_metadata: Dict[str, Any]


class PrivateAgentMemory:
    """Each agent's internal memory for reasoning and observations."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.raw_observations: List[str] = []
        self.reasoning_traces: List[str] = []
        self.confidence_scores: Dict[str, float] = {}
        self.hypothesis_space: List[str] = []
        self.rejection_log: List[Dict[str, Any]] = []
        self.processing_context: Dict[str, Any] = {}
    
    def add_observation(self, observation: str, confidence: float):
        """Add raw observation with confidence score."""
        self.raw_observations.append(observation)
        self.confidence_scores[observation] = confidence
    
    def add_reasoning_trace(self, reasoning: str):
        """Track internal reasoning process."""
        self.reasoning_traces.append(f"[{datetime.now().isoformat()}] {reasoning}")
    
    def record_rejection(self, item: str, reason: str, confidence: float):
        """Log what was filtered out and why."""
        self.rejection_log.append({
            "item": item,
            "reason": reason,
            "confidence": confidence,
            "timestamp": datetime.now()
        })


class SharedConsensusMemory:
    """Global shared memory for verified, agreed-upon knowledge."""
    
    def __init__(self):
        # Separate memory domains to avoid conflation
        self.factual_assertions: Dict[str, Any] = {}
        self.emotional_patterns: Dict[str, Any] = {}
        self.preference_model: Dict[str, Any] = {}
        self.behavioral_insights: Dict[str, Any] = {}
        self.consensus_log: List[ConflictResolution] = []
    
    def commit_factual(self, fact_id: str, fact_data: Dict[str, Any]):
        """Commit verified factual information."""
        self.factual_assertions[fact_id] = {
            **fact_data,
            "committed_at": datetime.now(),
            "memory_type": "factual"
        }
    
    def commit_emotional(self, pattern_id: str, pattern_data: Dict[str, Any]):
        """Commit verified emotional pattern."""
        self.emotional_patterns[pattern_id] = {
            **pattern_data,
            "committed_at": datetime.now(),
            "memory_type": "emotional"
        }
    
    def commit_preference(self, pref_id: str, pref_data: Dict[str, Any]):
        """Commit verified preference information."""
        self.preference_model[pref_id] = {
            **pref_data,
            "committed_at": datetime.now(),
            "memory_type": "preference"
        }
    
    def get_cross_domain_context(self, requesting_domain: str) -> Dict[str, Any]:
        """Provide controlled cross-domain context without memory conflation."""
        context = {}
        
        if requesting_domain == "emotional":
            # Emotional processing gets preference context for interpretation
            context["preference_context"] = {
                "communication_style": self.preference_model.get("communication_style"),
                "interaction_pace": self.preference_model.get("pace_preference"),
                "feedback_sensitivity": self.preference_model.get("feedback_tolerance")
            }
        
        elif requesting_domain == "factual":
            # Factual processing gets emotional policies for evidence standards
            emotional_summary = self._summarize_emotional_patterns()
            context["processing_policies"] = {
                "evidence_threshold": "high" if emotional_summary.get("distrust_tendency") else "medium",
                "assumption_flagging": emotional_summary.get("detail_orientation", "standard"),
                "uncertainty_handling": emotional_summary.get("ambiguity_tolerance", "explicit")
            }
        
        elif requesting_domain == "preference":
            # Preference extraction gets emotional context for intensity calibration
            context["emotional_context"] = {
                "baseline_intensity": self._get_emotional_baseline(),
                "expression_patterns": self.emotional_patterns.get("expression_style", {})
            }
        
        return context
    
    def _summarize_emotional_patterns(self) -> Dict[str, Any]:
        """Create summary of emotional patterns for policy decisions."""
        # Implementation would analyze emotional_patterns and extract key tendencies
        return {}
    
    def _get_emotional_baseline(self) -> Dict[str, float]:
        """Get user's emotional baseline for preference intensity calibration."""
        # Implementation would calculate emotional baseline from patterns
        return {}


class ConsensusBuilder:
    """Handles explicit consensus building and conflict resolution."""
    
    def __init__(self):
        self.voting_weights = {
            "factual": {"confidence": 0.4, "evidence_strength": 0.6},
            "emotional": {"pattern_strength": 0.5, "context_fit": 0.5},
            "preference": {"reinforcement_count": 0.3, "consistency": 0.7}
        }
    
    async def build_consensus(
        self, 
        agent_outputs: Dict[str, AgentOutput],
        shared_memory: SharedConsensusMemory
    ) -> Dict[str, Any]:
        """Build consensus from agent outputs with explicit conflict resolution."""
        
        # Detect conflicts between agent outputs
        conflicts = self._detect_conflicts(agent_outputs)
        
        # Resolve conflicts using domain-specific strategies
        resolutions = []
        for conflict in conflicts:
            resolution = await self._resolve_conflict(conflict, agent_outputs, shared_memory)
            resolutions.append(resolution)
            shared_memory.consensus_log.append(resolution)
        
        # Merge non-conflicting outputs
        consensus_output = self._merge_non_conflicting_outputs(agent_outputs, resolutions)
        
        return consensus_output
    
    def _detect_conflicts(self, agent_outputs: Dict[str, AgentOutput]) -> List[Dict[str, Any]]:
        """Detect conflicts between agent outputs."""
        conflicts = []
        
        # Check for confidence disagreements
        confidence_conflicts = self._detect_confidence_conflicts(agent_outputs)
        conflicts.extend(confidence_conflicts)
        
        # Check for category/classification disagreements
        category_conflicts = self._detect_category_conflicts(agent_outputs)
        conflicts.extend(category_conflicts)
        
        # Check for interpretation disagreements
        interpretation_conflicts = self._detect_interpretation_conflicts(agent_outputs)
        conflicts.extend(interpretation_conflicts)
        
        return conflicts
    
    def _detect_confidence_conflicts(self, agent_outputs: Dict[str, AgentOutput]) -> List[Dict[str, Any]]:
        """Detect when agents have significantly different confidence scores for similar items."""
        # Implementation would compare confidence scores across agents
        return []
    
    def _detect_category_conflicts(self, agent_outputs: Dict[str, AgentOutput]) -> List[Dict[str, Any]]:
        """Detect when agents categorize similar content differently."""
        # Implementation would compare categorizations
        return []
    
    def _detect_interpretation_conflicts(self, agent_outputs: Dict[str, AgentOutput]) -> List[Dict[str, Any]]:
        """Detect when agents interpret the same information differently."""
        # Implementation would compare interpretations
        return []
    
    async def _resolve_conflict(
        self, 
        conflict: Dict[str, Any], 
        agent_outputs: Dict[str, AgentOutput],
        shared_memory: SharedConsensusMemory
    ) -> ConflictResolution:
        """Resolve a specific conflict using appropriate strategy."""
        
        if conflict["type"] == "confidence_disagreement":
            return await self._weighted_average_resolution(conflict, agent_outputs)
        elif conflict["type"] == "category_disagreement":
            return await self._evidence_based_resolution(conflict, agent_outputs)
        elif conflict["type"] == "interpretation_disagreement":
            return await self._context_mediated_resolution(conflict, agent_outputs, shared_memory)
        else:
            return await self._default_resolution(conflict, agent_outputs)
    
    async def _weighted_average_resolution(
        self, 
        conflict: Dict[str, Any], 
        agent_outputs: Dict[str, AgentOutput]
    ) -> ConflictResolution:
        """Resolve confidence disagreements using weighted averaging."""
        # Implementation would calculate weighted average based on agent reliability
        return ConflictResolution(
            conflict_type="confidence_disagreement",
            agents_involved=conflict["agents"],
            original_values=conflict["values"],
            resolved_value=0.0,  # Calculated weighted average
            resolution_method="weighted_average",
            confidence_score=0.0,  # Calculated confidence
            timestamp=datetime.now()
        )
    
    async def _evidence_based_resolution(
        self, 
        conflict: Dict[str, Any], 
        agent_outputs: Dict[str, AgentOutput]
    ) -> ConflictResolution:
        """Resolve category disagreements based on evidence strength."""
        # Implementation would analyze evidence supporting each categorization
        return ConflictResolution(
            conflict_type="category_disagreement",
            agents_involved=conflict["agents"],
            original_values=conflict["values"],
            resolved_value="",  # Best-supported category
            resolution_method="evidence_based",
            confidence_score=0.0,
            timestamp=datetime.now()
        )
    
    async def _context_mediated_resolution(
        self, 
        conflict: Dict[str, Any], 
        agent_outputs: Dict[str, AgentOutput],
        shared_memory: SharedConsensusMemory
    ) -> ConflictResolution:
        """Resolve interpretation disagreements using shared context."""
        # Implementation would use shared memory context to mediate
        return ConflictResolution(
            conflict_type="interpretation_disagreement",
            agents_involved=conflict["agents"],
            original_values=conflict["values"],
            resolved_value="",  # Context-mediated interpretation
            resolution_method="context_mediated",
            confidence_score=0.0,
            timestamp=datetime.now()
        )
    
    async def _default_resolution(
        self, 
        conflict: Dict[str, Any], 
        agent_outputs: Dict[str, AgentOutput]
    ) -> ConflictResolution:
        """Default conflict resolution strategy."""
        return ConflictResolution(
            conflict_type="unknown",
            agents_involved=conflict["agents"],
            original_values=conflict["values"],
            resolved_value=conflict["values"][0],  # Take first value
            resolution_method="default",
            confidence_score=0.5,
            timestamp=datetime.now()
        )
    
    def _merge_non_conflicting_outputs(
        self, 
        agent_outputs: Dict[str, AgentOutput], 
        resolutions: List[ConflictResolution]
    ) -> Dict[str, Any]:
        """Merge outputs that don't have conflicts."""
        # Implementation would merge non-conflicting outputs
        return {}


class HybridMemoryOrchestrator:
    """
    Orchestrates parallel multi-agent memory extraction with hybrid memory architecture.
    
    Features:
    - Parallel processing across specialized agents
    - Private agent memory for internal reasoning
    - Shared consensus memory for verified conclusions
    - Controlled cross-domain influence
    - Explicit consensus building
    """
    
    def __init__(self, model: Optional[Gemini] = None, db: Optional[SqliteDb] = None):
        # Load configuration
        self.app_config = load_app_config()
        self.model_config = get_model_config()
        
        # Initialize model if not provided
        if model is None:
            api_key = os.getenv("GEMINI_API_KEY") or config.GEMINI_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment or config")
            
            self.model = Gemini(
                id=self.model_config.get("gemini", {}).get("model", "gemini-2.0-flash"),
                api_key=api_key
            )
        else:
            self.model = model
        
        # Initialize database if not provided
        if db is None:
            db_path = self.app_config.get("databases", {}).get("memory", {}).get("path", "./data/memory.db")
            self.db = SqliteDb(db_file=db_path)
        else:
            self.db = db
        
        # Initialize specialized agents
        self.agents = {
            "emotional": EmotionalExtractor(self.model, self.db),
            "factual": FactualExtractor(self.model, self.db),
            "preference": PreferenceExtractor(self.model, self.db),
            "analysis": AnalysisAgent(self.model, self.db)
        }
        
        # Initialize Agno Team for collaborative processing
        self.memory_extraction_team = self._setup_agno_team()
        
        # Initialize memory systems
        self.private_memories = {
            agent_name: PrivateAgentMemory(agent_name) 
            for agent_name in self.agents.keys()
        }
        self.shared_memory = SharedConsensusMemory()
        self.consensus_builder = ConsensusBuilder()
        
        logger.info("HybridMemoryOrchestrator initialized with 4 specialized agents")
    
    def _setup_agno_team(self) -> Team:
        """Set up Agno Team for collaborative memory extraction."""
        # Convert extractors to Agno agents for team collaboration
        team_members = []
        for agent_name, extractor in self.agents.items():
            if hasattr(extractor, 'agent'):
                team_members.append(extractor.agent)
            else:
                # Create basic agent if extractor doesn't have one
                agent = Agent(
                    name=f"{agent_name.title()} Memory Agent",
                    model=self.model,
                    db=self.db,
                    instructions=[
                        f"You are a {agent_name} memory extraction specialist.",
                        "Extract relevant information from conversations.",
                        "Collaborate with other agents for comprehensive analysis."
                    ]
                )
                team_members.append(agent)
        
        team = Team(
            name="Memory Extraction Team",
            model=self.model,
            db=self.db,
            members=team_members,
            instructions=[
                "Collaborate to extract comprehensive memory profiles from conversations.",
                "Each agent focuses on their specialty while sharing insights.",
                "Build consensus on overlapping findings.",
                "Provide detailed analysis from multiple perspectives."
            ],
            show_members_responses=True,  # Show individual agent outputs
            add_history_to_context=True,  # Include conversation history
            markdown=False
        )
        
        logger.info(f"Agno Team initialized with {len(team_members)} members")
        return team
    
    async def extract_memories(
        self, 
        conversation_text: str, 
        user_id: str, 
        session_id: str
    ) -> MemoryExtractionOutput:
        """
        Extract memories using parallel processing and consensus building.
        
        Process:
        1. Parallel extraction by all agents
        2. Cross-domain context sharing
        3. Conflict detection and resolution
        4. Consensus building
        5. Shared memory commitment
        """
        
        # Phase 1: Parallel extraction with private memory tracking
        agent_outputs = await self._parallel_extraction(conversation_text, user_id, session_id)
        
        # Phase 2: Cross-domain context enrichment
        enriched_outputs = await self._enrich_with_cross_domain_context(agent_outputs)
        
        # Phase 3: Consensus building and conflict resolution
        consensus_results = await self.consensus_builder.build_consensus(
            enriched_outputs, self.shared_memory
        )
        
        # Phase 4: Commit verified conclusions to shared memory
        await self._commit_to_shared_memory(consensus_results)
        
        # Phase 5: Generate final extraction output
        final_output = self._generate_extraction_output(consensus_results, user_id, session_id)
        
        return final_output
    
    async def _parallel_extraction(
        self, 
        conversation_text: str, 
        user_id: str, 
        session_id: str
    ) -> Dict[str, AgentOutput]:
        """Run all agents in parallel and capture their private reasoning."""
        
        # Create parallel extraction tasks
        extraction_tasks = {
            agent_name: self._extract_with_private_memory(
                agent, agent_name, conversation_text, user_id, session_id
            )
            for agent_name, agent in self.agents.items()
        }
        
        # Execute all extractions in parallel
        results = await asyncio.gather(*[
            task for task in extraction_tasks.values()
        ], return_exceptions=True)
        
        # Package results with agent names
        agent_outputs = {}
        for i, (agent_name, _) in enumerate(extraction_tasks.items()):
            if not isinstance(results[i], Exception):
                agent_outputs[agent_name] = results[i]
            else:
                logger.error(f"Agent {agent_name} extraction failed: {results[i]}")
        
        return agent_outputs
    
    async def _extract_with_private_memory(
        self, 
        agent: BaseExtractor, 
        agent_name: str, 
        conversation_text: str, 
        user_id: str, 
        session_id: str
    ) -> AgentOutput:
        """Extract memories while tracking private reasoning process."""
        
        private_memory = self.private_memories[agent_name]
        
        # Record processing start
        private_memory.add_reasoning_trace(f"Starting extraction for session {session_id}")
        
        # Perform extraction
        extracted_memories = agent.extract(conversation_text, user_id, session_id)
        
        # Track confidence scores
        confidence_scores = {}
        for memory in extracted_memories:
            confidence_scores[memory.id] = memory.confidence
            private_memory.add_observation(memory.content, memory.confidence)
        
        # Record reasoning traces (if agent provides them)
        reasoning_traces = []
        if hasattr(agent, 'agent') and hasattr(agent.agent, 'conversation_history'):
            # Extract reasoning from agent's recent history
            reasoning_traces = [f"Processed {len(extracted_memories)} memories with avg confidence {sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0:.2f}"]
        
        for trace in reasoning_traces:
            private_memory.add_reasoning_trace(trace)
        
        return AgentOutput(
            agent_name=agent_name,
            raw_extractions=[],  # Would capture raw LLM outputs
            confidence_scores=confidence_scores,
            reasoning_traces=private_memory.reasoning_traces[-10:],  # Last 10 traces
            filtered_conclusions=extracted_memories,
            processing_metadata={
                "processing_time": 0,  # Would measure actual time
                "memory_count": len(extracted_memories),
                "avg_confidence": sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
            }
        )
    
    async def _enrich_with_cross_domain_context(
        self, 
        agent_outputs: Dict[str, AgentOutput]
    ) -> Dict[str, AgentOutput]:
        """Enrich agent outputs with controlled cross-domain context."""
        
        enriched_outputs = {}
        
        for agent_name, output in agent_outputs.items():
            # Get cross-domain context for this agent
            cross_domain_context = self.shared_memory.get_cross_domain_context(
                agent_name.replace("_agent", "").replace("_extractor", "")
            )
            
            # Apply context to refine conclusions if applicable
            if cross_domain_context:
                refined_output = await self._apply_cross_domain_context(output, cross_domain_context)
                enriched_outputs[agent_name] = refined_output
            else:
                enriched_outputs[agent_name] = output
        
        return enriched_outputs
    
    async def _apply_cross_domain_context(
        self, 
        output: AgentOutput, 
        context: Dict[str, Any]
    ) -> AgentOutput:
        """Apply cross-domain context to refine agent output."""
        # Implementation would use context to adjust confidence scores, 
        # filter conclusions, or modify categorizations
        return output
    
    async def _commit_to_shared_memory(self, consensus_results: Dict[str, Any]):
        """Commit verified conclusions to shared consensus memory."""
        
        for domain, results in consensus_results.items():
            if domain == "factual":
                for fact_id, fact_data in results.items():
                    self.shared_memory.commit_factual(fact_id, fact_data)
            elif domain == "emotional":
                for pattern_id, pattern_data in results.items():
                    self.shared_memory.commit_emotional(pattern_id, pattern_data)
            elif domain == "preference":
                for pref_id, pref_data in results.items():
                    self.shared_memory.commit_preference(pref_id, pref_data)
    
    def _generate_extraction_output(
        self, 
        consensus_results: Dict[str, Any], 
        user_id: str, 
        session_id: str
    ) -> MemoryExtractionOutput:
        """Generate final memory extraction output."""
        
        # Implementation would create MemoryExtractionOutput from consensus results
        return MemoryExtractionOutput(
            user_preferences=consensus_results.get("preferences", []),
            emotional_patterns=consensus_results.get("emotional", []),
            factual_memories=consensus_results.get("factual", []),
            extraction_confidence=consensus_results.get("avg_confidence", 0.8),
            source_messages_count=consensus_results.get("message_count", 1),
            processing_time_ms=consensus_results.get("processing_time_ms"),
            session_summary=consensus_results.get("session_summary"),
            key_insights=consensus_results.get("key_insights", []),
            suggested_personality=consensus_results.get("suggested_personality")
        )
    
    def get_shared_memory_snapshot(self) -> Dict[str, Any]:
        """Get current state of shared consensus memory."""
        return {
            "factual_assertions": len(self.shared_memory.factual_assertions),
            "emotional_patterns": len(self.shared_memory.emotional_patterns),
            "preference_model": len(self.shared_memory.preference_model),
            "behavioral_insights": len(self.shared_memory.behavioral_insights),
            "consensus_resolutions": len(self.shared_memory.consensus_log)
        }
    
    def get_private_memory_summary(self) -> Dict[str, Any]:
        """Get summary of all agents' private memory states."""
        return {
            agent_name: {
                "observations": len(memory.raw_observations),
                "reasoning_traces": len(memory.reasoning_traces),
                "rejections": len(memory.rejection_log),
                "avg_confidence": sum(memory.confidence_scores.values()) / len(memory.confidence_scores) 
                    if memory.confidence_scores else 0
            }
            for agent_name, memory in self.private_memories.items()
        }
