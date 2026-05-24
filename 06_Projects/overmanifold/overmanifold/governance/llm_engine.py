"""
Overmanifold LLM Governance Engine
Interprets human intent into structured economic tasks and resolves semantic ambiguity.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import re
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of semantic intents the LLM governor can interpret"""
    RESOURCE_ALLOCATION = "resource_allocation"
    LIQUIDITY_ROUTING = "liquidity_routing"
    TRUST_ESTABLISHMENT = "trust_establishment"
    COMPUTATION_REQUEST = "computation_request"
    STORAGE_PROVISION = "storage_provision"
    MESSAGE_RELAY = "message_relay"
    SETTLEMENT_EXECUTION = "settlement_execution"
    GOVERNANCE_ACTION = "governance_action"
    PROOF_GENERATION = "proof_generation"
    VALIDATION_REQUEST = "validation_request"


class TaskPriority(Enum):
    """Priority levels for economic tasks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Status of economic tasks"""
    PENDING = "pending"
    INTERPRETING = "interpreting"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EconomicTask:
    """
    Structured economic task derived from human intent
    """
    task_id: str
    intent_type: IntentType
    description: str
    required_capabilities: List[str]
    priority: TaskPriority
    estimated_cost: float
    estimated_duration_seconds: int
    required_endpoints: List[str]
    settlement_conditions: List[str]
    governance_approval_required: bool
    semantic_confidence: float
    status: TaskStatus
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['intent_type'] = self.intent_type.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data


@dataclass
class IntentInterpretation:
    """
    Result of LLM intent interpretation
    """
    interpretation_id: str
    original_intent: str
    interpreted_tasks: List[EconomicTask]
    confidence_score: float
    ambiguity_detected: bool
    alternative_interpretations: List[Dict]
    governance_requirements: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['interpreted_tasks'] = [task.to_dict() for task in self.interpreted_tasks]
        return data


@dataclass
class GovernanceDecision:
    """
    Decision made by LLM governor
    """
    decision_id: str
    task_id: str
    decision: str  # 'approve', 'reject', 'modify', 'defer'
    reasoning: str
    conditions: List[str]
    economic_impact: float
    trust_impact: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_interpretation(
        self,
        intent: str,
        context: Dict
    ) -> Tuple[str, float]:
        """Generate interpretation and confidence score"""
        pass


class OpenAIProvider(LLMProvider):
    """Real OpenAI LLM provider for production"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.call_count = 0
        
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
    
    async def generate_interpretation(
        self,
        intent: str,
        context: Dict
    ) -> Tuple[str, float]:
        """Generate interpretation using real OpenAI API"""
        self.call_count += 1
        
        system_prompt = """You are an economic governance interpreter for the Overmanifold Protocol. 
Analyze human intent and convert it into structured economic tasks.
Respond ONLY with valid JSON in this format:
{
    "intent_type": "resource_allocation|liquidity_routing|trust_establishment|computation_request|message_relay",
    "description": "detailed description",
    "required_capabilities": ["capability1", "capability2"],
    "priority": "critical|high|medium|low",
    "estimated_cost": float,
    "governance_approval": boolean
}"""

        user_prompt = f"Human Intent: {intent}\nContext: {json.dumps(context, indent=2)}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            interpretation_text = response.choices[0].message.content.strip()
            confidence = 0.85  # Base confidence for GPT-4
            
            # Validate JSON response
            try:
                json.loads(interpretation_text)
            except json.JSONDecodeError:
                # Fallback to structured format if JSON parsing fails
                interpretation_text = json.dumps({
                    'intent_type': 'message_relay',
                    'description': intent,
                    'required_capabilities': ['messaging_reachability'],
                    'priority': 'low',
                    'estimated_cost': 25.0,
                    'governance_approval': False
                })
                confidence = 0.5
            
            return interpretation_text, confidence
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            # Fallback to basic interpretation
            interpretation_text = json.dumps({
                'intent_type': 'message_relay',
                'description': intent,
                'required_capabilities': ['messaging_reachability'],
                'priority': 'low',
                'estimated_cost': 25.0,
                'governance_approval': False
            })
            return interpretation_text, 0.3


class AnthropicProvider(LLMProvider):
    """Real Anthropic Claude LLM provider for production"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model
        self.call_count = 0
        
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Anthropic library not installed. Install with: pip install anthropic")
    
    async def generate_interpretation(
        self,
        intent: str,
        context: Dict
    ) -> Tuple[str, float]:
        """Generate interpretation using real Anthropic API"""
        self.call_count += 1
        
        system_prompt = """You are an economic governance interpreter for the Overmanifold Protocol. 
Analyze human intent and convert it into structured economic tasks.
Respond ONLY with valid JSON in this format:
{
    "intent_type": "resource_allocation|liquidity_routing|trust_establishment|computation_request|message_relay",
    "description": "detailed description",
    "required_capabilities": ["capability1", "capability2"],
    "priority": "critical|high|medium|low",
    "estimated_cost": float,
    "governance_approval": boolean
}"""

        user_prompt = f"Human Intent: {intent}\nContext: {json.dumps(context, indent=2)}"
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            interpretation_text = response.content[0].text.strip()
            confidence = 0.88  # Base confidence for Claude Opus
            
            # Validate JSON response
            try:
                json.loads(interpretation_text)
            except json.JSONDecodeError:
                # Fallback to structured format if JSON parsing fails
                interpretation_text = json.dumps({
                    'intent_type': 'message_relay',
                    'description': intent,
                    'required_capabilities': ['messaging_reachability'],
                    'priority': 'low',
                    'estimated_cost': 25.0,
                    'governance_approval': False
                })
                confidence = 0.5
            
            return interpretation_text, confidence
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            # Fallback to basic interpretation
            interpretation_text = json.dumps({
                'intent_type': 'message_relay',
                'description': intent,
                'required_capabilities': ['messaging_reachability'],
                'priority': 'low',
                'estimated_cost': 25.0,
                'governance_approval': False
            })
            return interpretation_text, 0.3


class LLMGovernanceEngine:
    """
    LLM Governance Engine
    Interprets human intent into structured economic tasks and makes governance decisions.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self.interpretation_history: List[IntentInterpretation] = []
        self.task_queue: List[EconomicTask] = []
        self.governance_decisions: List[GovernanceDecision] = []
        self.semantic_ambiguity_buffer: Dict[str, List[Dict]] = {}
        
        # Governance parameters
        self.confidence_threshold = 0.7
        self.governance_approval_threshold = 0.8
        self.max_concurrent_tasks = 10
    
    async def interpret_intent(
        self,
        human_intent: str,
        context: Dict = None,
        require_governance_approval: bool = False
    ) -> IntentInterpretation:
        """
        Interpret human intent into structured economic tasks
        """
        context = context or {}
        
        # Generate interpretation using LLM
        interpretation_text, confidence = await self.llm_provider.generate_interpretation(
            human_intent,
            context
        )
        
        # Parse interpretation
        try:
            interpretation_data = json.loads(interpretation_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM interpretation: {interpretation_text}")
            interpretation_data = {
                'intent_type': 'message_relay',
                'description': human_intent,
                'required_capabilities': ['messaging_reachability'],
                'priority': 'low',
                'estimated_cost': 25.0,
                'governance_approval': False
            }
            confidence = 0.5
        
        # Create economic task
        task = self._create_economic_task(interpretation_data, human_intent, confidence)
        
        # Check for ambiguity
        ambiguity_detected = confidence < self.confidence_threshold
        
        # Generate alternative interpretations if ambiguous
        alternative_interpretations = []
        if ambiguity_detected:
            alternative_interpretations = await self._generate_alternative_interpretations(
                human_intent,
                context
            )
        
        # Determine governance requirements
        governance_requirements = []
        if require_governance_approval or interpretation_data.get('governance_approval', False):
            governance_requirements.append('governance_approval')
        
        if task.estimated_cost > 1000:
            governance_requirements.append('treasury_approval')
        
        if task.priority == TaskPriority.CRITICAL:
            governance_requirements.append('critical_action_review')
        
        # Create interpretation result
        interpretation_id = hashlib.sha256(
            f"{human_intent}{interpretation_text}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        interpretation = IntentInterpretation(
            interpretation_id=interpretation_id,
            original_intent=human_intent,
            interpreted_tasks=[task],
            confidence_score=confidence,
            ambiguity_detected=ambiguity_detected,
            alternative_interpretations=alternative_interpretations,
            governance_requirements=governance_requirements,
            timestamp=datetime.now().isoformat()
        )
        
        self.interpretation_history.append(interpretation)
        
        # Add task to queue if no ambiguity or if governance approved
        if not ambiguity_detected or not governance_requirements:
            self.task_queue.append(task)
        
        # Buffer ambiguous intents for convergence
        if ambiguity_detected:
            self._buffer_ambiguous_intent(interpretation_id, human_intent, interpretation_data)
        
        logger.info(f"Interpreted intent: {human_intent} -> {task.intent_type.value}")
        return interpretation
    
    def _create_economic_task(
        self,
        interpretation_data: Dict,
        original_intent: str,
        confidence: float
    ) -> EconomicTask:
        """Create economic task from interpretation data"""
        task_id = hashlib.sha256(
            f"{original_intent}{json.dumps(interpretation_data)}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        # Map intent type
        intent_type_str = interpretation_data.get('intent_type', 'message_relay')
        try:
            intent_type = IntentType(intent_type_str)
        except ValueError:
            intent_type = IntentType.MESSAGE_RELAY
        
        # Map priority
        priority_str = interpretation_data.get('priority', 'medium')
        try:
            priority = TaskPriority(priority_str)
        except ValueError:
            priority = TaskPriority.MEDIUM
        
        task = EconomicTask(
            task_id=task_id,
            intent_type=intent_type,
            description=interpretation_data.get('description', original_intent),
            required_capabilities=interpretation_data.get('required_capabilities', []),
            priority=priority,
            estimated_cost=interpretation_data.get('estimated_cost', 50.0),
            estimated_duration_seconds=interpretation_data.get('estimated_duration', 60),
            required_endpoints=interpretation_data.get('required_endpoints', []),
            settlement_conditions=interpretation_data.get('settlement_conditions', []),
            governance_approval_required=interpretation_data.get('governance_approval', False),
            semantic_confidence=confidence,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        return task
    
    async def _generate_alternative_interpretations(
        self,
        human_intent: str,
        context: Dict
    ) -> List[Dict]:
        """Generate alternative interpretations for ambiguous intents"""
        alternatives = []
        
        # Generate variations based on different emphasis
        variations = [
            f"Primary focus: {human_intent}",
            f"Economic priority: {human_intent}",
            f"Technical implementation: {human_intent}"
        ]
        
        for variation in variations:
            try:
                interpretation_text, confidence = await self.llm_provider.generate_interpretation(
                    variation,
                    context
                )
                interpretation_data = json.loads(interpretation_text)
                alternatives.append({
                    'interpretation': interpretation_data,
                    'confidence': confidence,
                    'variation': variation
                })
            except:
                continue
        
        return alternatives
    
    def _buffer_ambiguous_intent(
        self,
        interpretation_id: str,
        original_intent: str,
        interpretation_data: Dict
    ):
        """Buffer ambiguous intent for convergence with other observers"""
        if interpretation_id not in self.semantic_ambiguity_buffer:
            self.semantic_ambiguity_buffer[interpretation_id] = []
        
        self.semantic_ambiguity_buffer[interpret_id].append({
            'original_intent': original_intent,
            'interpretation': interpretation_data,
            'timestamp': datetime.now().isoformat()
        })
    
    async def make_governance_decision(
        self,
        task_id: str,
        context: Dict = None
    ) -> GovernanceDecision:
        """
        Make governance decision on a task
        """
        context = context or {}
        
        # Find task
        task = next((t for t in self.task_queue if t.task_id == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Simulate governance decision logic
        decision = "approve"
        reasoning = f"Task {task_id} meets governance requirements"
        conditions = []
        economic_impact = task.estimated_cost * 0.1  # 10% of cost as impact
        trust_impact = 0.05 if task.semantic_confidence > 0.8 else -0.02
        
        # Check if governance approval is required
        if task.governance_approval_required:
            if task.semantic_confidence < self.governance_approval_threshold:
                decision = "defer"
                reasoning = f"Confidence {task.semantic_confidence} below threshold {self.governance_approval_threshold}"
                conditions.append("require_additional_interpretation")
            else:
                decision = "approve"
                conditions.append("governance_approved")
        
        # Check economic impact
        if task.estimated_cost > 1000:
            conditions.append("treasury_review_required")
            if task.priority != TaskPriority.CRITICAL:
                decision = "modify"
                reasoning = "High cost requires priority justification or cost reduction"
                conditions.append("reduce_cost_or_increase_priority")
        
        # Create governance decision
        decision_id = hashlib.sha256(
            f"{task_id}{decision}{reasoning}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        governance_decision = GovernanceDecision(
            decision_id=decision_id,
            task_id=task_id,
            decision=decision,
            reasoning=reasoning,
            conditions=conditions,
            economic_impact=economic_impact,
            trust_impact=trust_impact,
            timestamp=datetime.now().isoformat()
        )
        
        self.governance_decisions.append(governance_decision)
        
        # Update task status based on decision
        if decision == "approve":
            task.status = TaskStatus.SCHEDULED
        elif decision == "reject":
            task.status = TaskStatus.FAILED
            task.error_message = "Rejected by governance"
        elif decision == "defer":
            task.status = TaskStatus.PENDING
        elif decision == "modify":
            task.status = TaskStatus.PENDING
        
        logger.info(f"Governance decision for task {task_id}: {decision}")
        return governance_decision
    
    async def execute_task(self, task_id: str) -> EconomicTask:
        """
        Execute an economic task
        """
        # Find task
        task = next((t for t in self.task_queue if t.task_id == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        task.status = TaskStatus.EXECUTING
        
        # Simulate task execution based on intent type
        try:
            result = await self._execute_task_by_type(task)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            task.result = result
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            logger.error(f"Task execution failed: {e}")
        
        return task
    
    async def _execute_task_by_type(self, task: EconomicTask) -> Dict:
        """Execute task based on its intent type"""
        # Simulate execution based on task type
        await asyncio.sleep(1)  # Simulate processing time
        
        if task.intent_type == IntentType.RESOURCE_ALLOCATION:
            return {
                'allocated_resources': True,
                'resource_type': 'computation',
                'amount': task.estimated_cost / 10,
                'duration_seconds': task.estimated_duration_seconds
            }
        elif task.intent_type == IntentType.LIQUIDITY_ROUTING:
            return {
                'routed_liquidity': True,
                'route_optimized': True,
                'cost_savings': task.estimated_cost * 0.1
            }
        elif task.intent_type == IntentType.TRUST_ESTABLISHMENT:
            return {
                'trust_established': True,
                'trust_score_increase': 0.1,
                'verification_complete': True
            }
        else:
            return {
                'task_completed': True,
                'execution_time_seconds': task.estimated_duration_seconds
            }
    
    def get_task_queue_status(self) -> Dict:
        """Get status of task queue"""
        pending = len([t for t in self.task_queue if t.status == TaskStatus.PENDING])
        executing = len([t for t in self.task_queue if t.status == TaskStatus.EXECUTING])
        completed = len([t for t in self.task_queue if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in self.task_queue if t.status == TaskStatus.FAILED])
        
        return {
            'total_tasks': len(self.task_queue),
            'pending': pending,
            'executing': executing,
            'completed': completed,
            'failed': failed,
            'total_interpretations': len(self.interpretation_history),
            'total_governance_decisions': len(self.governance_decisions),
            'ambiguous_intents_buffered': len(self.semantic_ambiguity_buffer)
        }
    
    def resolve_ambiguity(
        self,
        interpretation_id: str,
        converged_interpretation: Dict
    ) -> bool:
        """
        Resolve semantic ambiguity by converging on an interpretation
        """
        if interpretation_id not in self.semantic_ambiguity_buffer:
            return False
        
        # Remove from buffer
        del self.semantic_ambiguity_buffer[interpretation_id]
        
        # Create task from converged interpretation
        task = self._create_economic_task(
            converged_interpretation,
            converged_interpretation.get('description', ''),
            0.9  # High confidence after convergence
        )
        
        task.status = TaskStatus.SCHEDULED
        self.task_queue.append(task)
        
        logger.info(f"Resolved ambiguity for {interpretation_id}")
        return True


async def main():
    """Example usage of LLM Governance Engine with real providers"""
    # Create real LLM provider and governance engine
    import os
    
    llm_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not llm_api_key:
        raise ValueError("LLM_API_KEY environment variable must be set")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        llm_provider = AnthropicProvider(llm_api_key)
    else:
        llm_provider = OpenAIProvider(llm_api_key)
    
    governance_engine = LLMGovernanceEngine(llm_provider)
    
    # Interpret some human intents
    intents = [
        "Allocate 100 units of compute resource to validator node",
        "Route liquidity through the most trustworthy path",
        "Establish trust relationship with new endpoint",
        "Process this data computation request"
    ]
    
    print("=== Interpreting Human Intents ===\n")
    
    for intent in intents:
        interpretation = await governance_engine.interpret_intent(intent)
        print(f"Intent: {intent}")
        print(f"Interpreted as: {interpret.interpreted_tasks[0].intent_type.value}")
        print(f"Confidence: {interpretation.confidence_score:.2f}")
        print(f"Ambiguity detected: {interpretation.ambiguity_detected}")
        print()
    
    # Get task queue status
    status = governance_engine.get_task_queue_status()
    print("=== Task Queue Status ===")
    print(json.dumps(status, indent=2))
    
    # Make governance decision for a task
    if governance_engine.task_queue:
        task = governance_engine.task_queue[0]
        decision = await governance_engine.make_governance_decision(task.task_id)
        print(f"\n=== Governance Decision ===")
        print(json.dumps(decision.to_dict(), indent=2))
        
        # Execute the task
        if decision.decision == "approve":
            result = await governance_engine.execute_task(task.task_id)
            print(f"\n=== Task Execution Result ===")
            print(json.dumps(result.to_dict(), indent=2))


if __name__ == '__main__':
    asyncio.run(main())