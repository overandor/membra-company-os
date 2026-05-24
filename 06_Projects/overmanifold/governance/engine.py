"""
Overmanifold LLM Governance Engine
Semantic intent interpretation and economic task transformation.
Translates ambiguous human desire into executable graph transformations.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio
from enum import Enum

from ..core.types import (
    Hash,
    EndpointID,
    IntentFragment,
    StateTransition,
    StateTransitionType,
    EconomicSignal
)
from ..core.config import GovernanceConfig


class IntentType(Enum):
    """Types of semantic intents."""
    TRANSFER = "transfer"
    SWAP = "swap"
    STAKE = "stake"
    GOVERNANCE = "governance"
    PRODUCTION = "production"
    VALIDATION = "validation"
    ROUTING = "routing"
    SETTLEMENT = "settlement"
    UNKNOWN = "unknown"


@dataclass
class EconomicTask:
    """Structured economic task derived from semantic intent."""
    task_id: Hash
    intent_type: IntentType
    description: str
    parameters: Dict[str, Any]
    required_capabilities: List[str]
    estimated_cost: float
    priority: float
    confidence: float
    created_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        return {
            "task_id": str(self.task_id),
            "intent_type": self.intent_type.value,
            "description": self.description,
            "parameters": self.parameters,
            "required_capabilities": self.required_capabilities,
            "estimated_cost": self.estimated_cost,
            "priority": self.priority,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class GovernanceDecision:
    """Decision made by LLM governance engine."""
    decision_id: Hash
    intent_fragment: IntentFragment
    economic_tasks: List[EconomicTask]
    reasoning: str
    confidence: float
    requires_approval: bool
    approval_threshold: int
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert decision to dictionary."""
        return {
            "decision_id": str(self.decision_id),
            "intent_fragment_id": str(self.intent_fragment.fragment_id),
            "economic_tasks": [task.to_dict() for task in self.economic_tasks],
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "requires_approval": self.requires_approval,
            "approval_threshold": self.approval_threshold,
            "timestamp": self.timestamp.isoformat()
        }


class IntentInterpreter:
    """
    Interprets semantic intent from human input.
    Converts natural language to structured economic tasks.
    """
    
    def __init__(self, config: GovernanceConfig):
        self.config = config
        self.intent_patterns = {
            IntentType.TRANSFER: ["send", "transfer", "pay", "give", "move"],
            IntentType.SWAP: ["swap", "exchange", "convert", "trade"],
            IntentType.STAKE: ["stake", "lock", "deposit", "bond"],
            IntentType.GOVERNANCE: ["vote", "propose", "govern", "decide"],
            IntentType.PRODUCTION: ["produce", "create", "build", "deploy"],
            IntentType.VALIDATION: ["validate", "verify", "check", "audit"],
            IntentType.ROUTING: ["route", "path", "bridge", "connect"],
            IntentType.SETTLEMENT: ["settle", "finalize", "complete", "execute"]
        }
    
    def interpret_intent(self, human_input: str, context: Optional[Dict] = None) -> Tuple[IntentType, float, Dict]:
        """
        Interpret human input into semantic intent.
        Returns (intent_type, confidence, parameters).
        """
        input_lower = human_input.lower()
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        parameters = {}
        
        # Match intent patterns
        for intent_type, keywords in self.intent_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in input_lower)
            confidence = min(matches / len(keywords), 1.0)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent_type
        
        # Extract parameters based on intent type
        parameters = self._extract_parameters(human_input, best_intent, context)
        
        return best_intent, best_confidence, parameters
    
    def _extract_parameters(self, human_input: str, intent_type: IntentType, 
                           context: Optional[Dict]) -> Dict:
        """Extract parameters from human input based on intent type."""
        parameters = {}
        
        # Add context if available
        if context:
            parameters["context"] = context
        
        # Intent-specific parameter extraction
        if intent_type == IntentType.TRANSFER:
            parameters = self._extract_transfer_params(human_input)
        elif intent_type == IntentType.SWAP:
            parameters = self._extract_swap_params(human_input)
        elif intent_type == IntentType.STAKE:
            parameters = self._extract_stake_params(human_input)
        
        return parameters
    
    def _extract_transfer_params(self, human_input: str) -> Dict:
        """Extract transfer parameters."""
        import re
        params = {}
        
        # Extract amount
        amounts = re.findall(r'\d+\.?\d*', human_input)
        if amounts:
            params["amount"] = float(amounts[0])
        
        # Extract recipient/address
        addresses = re.findall(r'[a-zA-Z0-9]{32,}', human_input)
        if addresses:
            params["recipient"] = addresses[0]
        
        return params
    
    def _extract_swap_params(self, human_input: str) -> Dict:
        """Extract swap parameters."""
        import re
        params = {}
        
        # Extract amounts
        amounts = re.findall(r'\d+\.?\d*', human_input)
        if amounts:
            params["amount"] = float(amounts[0])
        
        # Extract token symbols (simple heuristic)
        tokens = re.findall(r'\b[A-Z]{2,6}\b', human_input)
        if len(tokens) >= 2:
            params["from_token"] = tokens[0]
            params["to_token"] = tokens[1]
        
        return params
    
    def _extract_stake_params(self, human_input: str) -> Dict:
        """Extract staking parameters."""
        import re
        params = {}
        
        # Extract amount
        amounts = re.findall(r'\d+\.?\d*', human_input)
        if amounts:
            params["amount"] = float(amounts[0])
        
        return params


class LLMPolicyEngine:
    """
    LLM-powered policy engine for governance decisions.
    Evaluates intents against economic policies and constraints.
    """
    
    def __init__(self, config: GovernanceConfig):
        self.config = config
        self.policies: Dict[str, Dict] = {}
        self.decision_history: List[GovernanceDecision] = []
    
    def add_policy(self, policy_name: str, policy_rules: Dict) -> None:
        """Add governance policy."""
        self.policies[policy_name] = policy_rules
    
    def evaluate_intent(self, intent_type: IntentType, parameters: Dict, 
                       actor: EndpointID) -> Tuple[bool, str, float]:
        """
        Evaluate intent against policies.
        Returns (allowed, reasoning, confidence).
        """
        # Default to allow if no policies constrain the intent
        if not self.policies:
            return True, "No constraining policies", 1.0
        
        # Check policies (simplified - in production would use actual LLM)
        for policy_name, policy_rules in self.policies.items():
            if intent_type.value in policy_rules.get("constrained_intents", []):
                # Check if actor has permission
                if str(actor) not in policy_rules.get("allowed_actors", []):
                    return False, f"Blocked by policy: {policy_name}", 0.0
        
        return True, "Intent allowed by all policies", 1.0
    
    def generate_economic_tasks(self, intent_type: IntentType, parameters: Dict,
                               confidence: float) -> List[EconomicTask]:
        """Generate economic tasks from interpreted intent."""
        tasks = []
        
        # Create primary task based on intent
        task_id = Hash.from_data(f"{intent_type.value}_{parameters}_{datetime.utcnow()}")
        
        required_capabilities = self._get_required_capabilities(intent_type)
        estimated_cost = self._estimate_cost(intent_type, parameters)
        
        task = EconomicTask(
            task_id=task_id,
            intent_type=intent_type,
            description=f"Execute {intent_type.value} operation",
            parameters=parameters,
            required_capabilities=required_capabilities,
            estimated_cost=estimated_cost,
            priority=0.5,
            confidence=confidence,
            created_at=datetime.utcnow()
        )
        
        tasks.append(task)
        
        # Add supplementary tasks based on intent complexity
        if intent_type in [IntentType.TRANSFER, IntentType.SWAP]:
            # Add routing task
            routing_task = EconomicTask(
                task_id=Hash.from_data(f"routing_{task_id.value}"),
                intent_type=IntentType.ROUTING,
                description="Find optimal routing path",
                parameters={"parent_task": str(task_id)},
                required_capabilities=["routing"],
                estimated_cost=estimated_cost * 0.1,
                priority=0.8,
                confidence=confidence,
                created_at=datetime.utcnow()
            )
            tasks.append(routing_task)
        
        return tasks
    
    def _get_required_capabilities(self, intent_type: IntentType) -> List[str]:
        """Get required capabilities for intent type."""
        capability_map = {
            IntentType.TRANSFER: ["settlement", "messaging"],
            IntentType.SWAP: ["liquidity", "routing", "settlement"],
            IntentType.STAKE: ["settlement", "governance"],
            IntentType.GOVERNANCE: ["governance", "validation"],
            IntentType.PRODUCTION: ["production", "storage"],
            IntentType.VALIDATION: ["validation", "compute"],
            IntentType.ROUTING: ["routing", "relay"],
            IntentType.SETTLEMENT: ["settlement"]
        }
        return capability_map.get(intent_type, [])
    
    def _estimate_cost(self, intent_type: IntentType, parameters: Dict) -> float:
        """Estimate economic cost for intent execution."""
        base_costs = {
            IntentType.TRANSFER: 0.001,
            IntentType.SWAP: 0.005,
            IntentType.STAKE: 0.002,
            IntentType.GOVERNANCE: 0.01,
            IntentType.PRODUCTION: 0.05,
            IntentType.VALIDATION: 0.003,
            IntentType.ROUTING: 0.0005,
            IntentType.SETTLEMENT: 0.001
        }
        
        base_cost = base_costs.get(intent_type, 0.01)
        
        # Adjust for amount if present
        if "amount" in parameters:
            amount = parameters["amount"]
            base_cost *= (1 + amount / 1000.0)  # Scale with amount
        
        return base_cost


class GovernanceEngine:
    """
    Main LLM governance engine for Overmanifold.
    Coordinates intent interpretation, policy evaluation, and task generation.
    """
    
    def __init__(self, config: GovernanceConfig):
        self.config = config
        self.intent_interpreter = IntentInterpreter(config)
        self.policy_engine = LLMPolicyEngine(config)
        self.pending_intents: Dict[Hash, IntentFragment] = {}
        self.decisions: Dict[Hash, GovernanceDecision] = {}
        self.approval_votes: Dict[Hash, Dict[EndpointID, bool]] = {}
    
    def process_human_intent(self, human_input: str, actor: EndpointID, 
                            context: Optional[Dict] = None) -> Optional[GovernanceDecision]:
        """
        Process human intent and generate governance decision.
        Returns decision or None if intent is rejected.
        """
        # Interpret intent
        intent_type, confidence, parameters = self.intent_interpreter.interpret_intent(human_input, context)
        
        if intent_type == IntentType.UNKNOWN or confidence < 0.3:
            return None
        
        # Create intent fragment
        fragment = IntentFragment(
            fragment_id=Hash.from_data(human_input + str(actor)),
            intent_data={"type": intent_type.value, "parameters": parameters},
            probability=confidence,
            convergence_threshold=self.config.convergence_threshold,
            created_at=datetime.utcnow()
        )
        
        self.pending_intents[fragment.fragment_id] = fragment
        
        # Evaluate against policies
        allowed, reasoning, policy_confidence = self.policy_engine.evaluate_intent(
            intent_type, parameters, actor
        )
        
        if not allowed:
            return None
        
        # Generate economic tasks
        tasks = self.policy_engine.generate_economic_tasks(intent_type, parameters, confidence)
        
        # Create governance decision
        decision = GovernanceDecision(
            decision_id=Hash.from_data(f"decision_{fragment.fragment_id.value}"),
            intent_fragment=fragment,
            economic_tasks=tasks,
            reasoning=reasoning,
            confidence=min(confidence, policy_confidence),
            requires_approval=len(tasks) > 1 or confidence < 0.8,
            approval_threshold=self.config.convergence_threshold,
            timestamp=datetime.utcnow()
        )
        
        self.decisions[decision.decision_id] = decision
        
        # Initialize approval tracking if required
        if decision.requires_approval:
            self.approval_votes[decision.decision_id] = {}
        
        return decision
    
    def submit_approval(self, decision_id: Hash, voter: EndpointID, approved: bool) -> bool:
        """Submit approval vote for governance decision."""
        if decision_id not in self.approval_votes:
            return False
        
        self.approval_votes[decision_id][voter] = approved
        
        # Check if decision has reached approval threshold
        decision = self.decisions.get(decision_id)
        if decision:
            approvals = sum(1 for vote in self.approval_votes[decision_id].values() if vote)
            if approvals >= decision.approval_threshold:
                decision.intent_fragment.resolved = True
        
        return True
    
    def get_decision_status(self, decision_id: Hash) -> Optional[Dict]:
        """Get status of governance decision."""
        decision = self.decisions.get(decision_id)
        if not decision:
            return None
        
        votes = self.approval_votes.get(decision_id, {})
        approvals = sum(1 for vote in votes.values() if vote)
        
        return {
            "decision_id": str(decision_id),
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "requires_approval": decision.requires_approval,
            "approval_threshold": decision.approval_threshold,
            "current_approvals": approvals,
            "total_votes": len(votes),
            "resolved": decision.intent_fragment.resolved,
            "economic_tasks": [task.to_dict() for task in decision.economic_tasks]
        }
    
    def execute_approved_tasks(self, decision_id: Hash) -> List[StateTransition]:
        """Execute economic tasks from approved decision."""
        decision = self.decisions.get(decision_id)
        if not decision or not decision.intent_fragment.resolved:
            return []
        
        transitions = []
        for task in decision.economic_tasks:
            # Create state transition for each task
            transition = StateTransition(
                transition_id=task.task_id,
                transition_type=StateTransitionType.SEMANTIC_INTENT,
                from_state=Hash.from_data("pending"),
                to_state=Hash.from_data("executing"),
                timestamp=datetime.utcnow(),
                actor=EndpointID.generate("governance", task.task_id.value[:16])
            )
            transitions.append(transition)
        
        return transitions
    
    def get_governance_statistics(self) -> Dict:
        """Get governance engine statistics."""
        return {
            "total_intents_processed": len(self.pending_intents),
            "total_decisions": len(self.decisions),
            "pending_approvals": sum(1 for d in self.decisions.values() if d.requires_approval and not d.intent_fragment.resolved),
            "resolved_decisions": sum(1 for d in self.decisions.values() if d.intent_fragment.resolved),
            "active_policies": len(self.policy_engine.policies),
            "avg_confidence": sum(d.confidence for d in self.decisions.values()) / len(self.decisions) if self.decisions else 0.0
        }