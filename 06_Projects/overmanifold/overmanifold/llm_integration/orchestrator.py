"""
Unified LLM Orchestration System
Coordinates all custom LLM-based systems (SMS, Email, Blockchain, Bridge)
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os

from openai import AsyncOpenAI

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.llm_integration.custom_sms_gateway import LLMSMSProcessor
from overmanifold.llm_integration.custom_email_system import LLMCustomEmailSystem
from overmanifold.llm_integration.custom_blockchain import CustomBlockchain, TransactionType
from overmanifold.llm_integration.custom_membra_bridge import CustomMembraBridge

logger = get_logger("llm_orchestration")


class OrchestrationEventType(Enum):
    """Orchestration event types"""
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    TRANSACTION_EVENT = "transaction_event"
    BRIDGE_EVENT = "bridge_event"
    ALERT_EVENT = "alert_event"
    COMPLIANCE_EVENT = "compliance_event"


@dataclass
class OrchestrationEvent:
    """Orchestration event structure"""
    event_id: str
    event_type: OrchestrationEventType
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: str = "normal"
    status: str = "pending"
    processed_by: List[str] = field(default_factory=list)
    results: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = self._generate_event_id()
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import hashlib
        import secrets
        data = f"{self.event_type.value}{self.source}{self.timestamp.isoformat()}{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()


class LLMOrchestrator:
    """Unified LLM orchestration system"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize LLM client for orchestration decisions
        if self.openai_api_key:
            self.llm_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.llm_client = None
            logger.warning("No OpenAI API key, orchestration limited")
        
        # Initialize all custom systems
        self.sms_system = LLMSMSProcessor(self.openai_api_key)
        self.email_system = LLMCustomEmailSystem(self.openai_api_key)
        self.blockchain = CustomBlockchain(self.openai_api_key)
        self.bridge = CustomMembraBridge(self.openai_api_key)
        
        # Orchestration state
        self.events: Dict[str, OrchestrationEvent] = {}
        self.event_handlers: Dict[str, List[callable]] = {}
        self.system_status: Dict[str, str] = {}
        
        # Build orchestration prompt
        self.orchestration_prompt = self._build_orchestration_prompt()
        
        # Initialize system status
        self._initialize_system_status()
    
    def _build_orchestration_prompt(self) -> str:
        """Build proprietary prompt for orchestration decisions"""
        return """You are the orchestration system for Overmanifold Protocol. Coordinate all systems (SMS, Email, Blockchain, Bridge) for optimal operation.

AVAILABLE SYSTEMS:
1. SMS - Custom SMS gateway for phone-based interactions
2. EMAIL - Custom email system for notifications and confirmations
3. BLOCKCHAIN - Custom blockchain for transactions and state
4. BRIDGE - Custom bridge for cross-chain operations

COORDINATION RULES:
1. USER_REGISTRATION: SMS verification → Email confirmation → Blockchain account creation
2. PAYMENT_RECEIVED: SMS notification → Email receipt → Blockchain transaction → Bridge if needed
3. BRIDGE_REQUEST: Email confirmation → Blockchain lock → Bridge processing → Email notification
4. SECURITY_ALERT: SMS urgent alert → Email detailed alert → Blockchain freeze if needed
5. SYSTEM_UPDATE: Email notification → System health check → Blockchain record

DECISION FACTORS:
- User preferences and communication channels
- Security requirements and urgency
- System availability and performance
- Cost optimization
- Compliance requirements
- Transaction importance
- User experience

ORCHESTRATION FORMAT:
Return JSON with this exact structure:
{
  "recommended_actions": [
    {
      "system": "sms|email|blockchain|bridge",
      "action": "specific_action",
      "priority": "low|medium|high|urgent",
      "parameters": {},
      "reasoning": "explain why this action"
    }
  ],
  "execution_order": [1, 2, 3],
  "total_cost_estimate": 0.0,
  "estimated_time_seconds": 0,
  "risk_assessment": "low|medium|high",
  "requires_manual_approval": false|true,
  "optimization_suggestions": ["suggestion1", "suggestion2"]
}

Coordinate systems efficiently while maintaining security and user experience."""

    def _initialize_system_status(self):
        """Initialize system status monitoring"""
        self.system_status = {
            "sms": "operational",
            "email": "operational",
            "blockchain": "operational",
            "bridge": "operational",
            "orchestrator": "operational"
        }
        
        logger.info("Orchestration system initialized with all subsystems")
    
    async def orchestrate_event(self, event: OrchestrationEvent) -> Dict[str, Any]:
        """Orchestrate an event across all systems"""
        
        # Store event
        self.events[event.event_id] = event
        event.status = "processing"
        
        # Use LLM to determine optimal orchestration
        orchestration_plan = await self._create_orchestration_plan(event)
        
        if not orchestration_plan:
            return {
                "success": False,
                "error": "Failed to create orchestration plan"
            }
        
        # Execute orchestration plan
        execution_results = await self._execute_orchestration_plan(event, orchestration_plan)
        
        # Update event status
        if all(result.get("success", False) for result in execution_results):
            event.status = "completed"
        else:
            event.status = "partial"
        
        event.results = execution_results
        
        return {
            "success": True,
            "event_id": event.event_id,
            "status": event.status,
            "orchestration_plan": orchestration_plan,
            "execution_results": execution_results
        }
    
    async def _create_orchestration_plan(self, event: OrchestrationEvent) -> Optional[Dict[str, Any]]:
        """Create orchestration plan using LLM"""
        
        if not self.llm_client:
            # Fallback to rule-based orchestration
            return self._fallback_orchestration(event)
        
        try:
            orchestration_context = {
                "event_type": event.event_type.value,
                "source": event.source,
                "priority": event.priority,
                "data": event.data,
                "system_status": self.system_status,
                "timestamp": event.timestamp.isoformat()
            }
            
            orchestration_prompt = f"{self.orchestration_prompt}\n\nEvent: {json.dumps(orchestration_context, indent=2)}"
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.orchestration_prompt},
                    {"role": "user", "content": orchestration_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            orchestration_plan = json.loads(response.choices[0].message.content)
            
            logger.info(f"LLM orchestration plan created with {len(orchestration_plan['recommended_actions'])} actions")
            
            return orchestration_plan
            
        except Exception as e:
            logger.error(f"LLM orchestration failed: {e}, using fallback")
            return self._fallback_orchestration(event)
    
    def _fallback_orchestration(self, event: OrchestrationEvent) -> Dict[str, Any]:
        """Fallback rule-based orchestration"""
        
        actions = []
        
        if event.event_type == OrchestrationEventType.USER_ACTION:
            if event.data.get("action") == "register":
                actions = [
                    {
                        "system": "sms",
                        "action": "send_verification",
                        "priority": "high",
                        "parameters": {"phone": event.data.get("phone")},
                        "reasoning": "User registration requires SMS verification"
                    },
                    {
                        "system": "email",
                        "action": "send_welcome",
                        "priority": "medium",
                        "parameters": {"email": event.data.get("email")},
                        "reasoning": "Welcome email for new user"
                    }
                ]
            elif event.data.get("action") == "payment":
                actions = [
                    {
                        "system": "blockchain",
                        "action": "process_transaction",
                        "priority": "high",
                        "parameters": event.data,
                        "reasoning": "Process payment transaction"
                    },
                    {
                        "system": "sms",
                        "action": "send_notification",
                        "priority": "medium",
                        "parameters": {"phone": event.data.get("phone")},
                        "reasoning": "Notify user of payment"
                    }
                ]
        
        elif event.event_type == OrchestrationEventType.TRANSACTION_EVENT:
            actions = [
                {
                    "system": "blockchain",
                    "action": "record_transaction",
                    "priority": "high",
                    "parameters": event.data,
                    "reasoning": "Record transaction on blockchain"
                },
                {
                    "system": "email",
                    "action": "send_receipt",
                    "priority": "medium",
                    "parameters": {"email": event.data.get("email")},
                    "reasoning": "Send transaction receipt"
                }
            ]
        
        return {
            "recommended_actions": actions,
            "execution_order": list(range(1, len(actions) + 1)),
            "total_cost_estimate": 0.0,
            "estimated_time_seconds": 60,
            "risk_assessment": "low",
            "requires_manual_approval": False,
            "optimization_suggestions": []
        }
    
    async def _execute_orchestration_plan(self, event: OrchestrationEvent, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute orchestration plan across systems"""
        
        results = []
        actions = plan.get("recommended_actions", [])
        execution_order = plan.get("execution_order", list(range(1, len(actions) + 1)))
        
        # Sort actions by execution order
        sorted_actions = sorted(zip(actions, execution_order), key=lambda x: x[1])
        
        for action, order in sorted_actions:
            system = action.get("system")
            action_type = action.get("action")
            parameters = action.get("parameters", {})
            
            try:
                result = await self._execute_system_action(system, action_type, parameters)
                event.processed_by.append(system)
                results.append(result)
                
                logger.info(f"Executed {system}.{action_type}: {result.get('success', False)}")
                
            except Exception as e:
                logger.error(f"Failed to execute {system}.{action_type}: {e}")
                results.append({
                    "system": system,
                    "action": action_type,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _execute_system_action(self, system: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action on specific system"""
        
        if system == "sms":
            return await self._execute_sms_action(action, parameters)
        elif system == "email":
            return await self._execute_email_action(action, parameters)
        elif system == "blockchain":
            return await self._execute_blockchain_action(action, parameters)
        elif system == "bridge":
            return await self._execute_bridge_action(action, parameters)
        else:
            return {
                "success": False,
                "error": f"Unknown system: {system}"
            }
    
    async def _execute_sms_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SMS system action"""
        
        if action == "send_verification":
            phone = parameters.get("phone")
            code = await self.sms_system.generate_verification_code(phone)
            result = await self.sms_system.send_sms(phone, f"Your verification code is: {code}")
            return {
                "system": "sms",
                "action": action,
                "success": result,
                "code": code,
                "phone": phone
            }
        
        elif action == "send_notification":
            phone = parameters.get("phone")
            message = parameters.get("message", "Transaction completed successfully")
            result = await self.sms_system.send_sms(phone, message)
            return {
                "system": "sms",
                "action": action,
                "success": result,
                "phone": phone
            }
        
        else:
            return {
                "system": "sms",
                "action": action,
                "success": False,
                "error": "Unknown SMS action"
            }
    
    async def _execute_email_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email system action"""
        
        if action == "send_welcome":
            email = parameters.get("email")
            subject = "Welcome to Overmanifold Protocol"
            body = "Welcome to Overmanifold Protocol! Your account has been created successfully."
            result = await self.email_system.send_custom_email(email, subject, body)
            return {
                "system": "email",
                "action": action,
                "success": result.success,
                "email": email
            }
        
        elif action == "send_receipt":
            email = parameters.get("email")
            amount = parameters.get("amount", 0)
            sender = parameters.get("sender", "Unknown")
            transaction_id = parameters.get("transaction_id", "Unknown")
            result = await self.email_system.send_payment_notification(email, amount, sender, transaction_id)
            return {
                "system": "email",
                "action": action,
                "success": result.success,
                "email": email
            }
        
        else:
            return {
                "system": "email",
                "action": action,
                "success": False,
                "error": "Unknown email action"
            }
    
    async def _execute_blockchain_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute blockchain action"""
        
        if action == "process_transaction":
            from_address = parameters.get("from_address")
            to_address = parameters.get("to_address")
            amount = parameters.get("amount", 0)
            
            transaction = self.blockchain.create_transaction(
                from_address, to_address, amount,
                TransactionType.PAYMENT
            )
            
            tx_id = self.blockchain.submit_transaction(transaction)
            result = await self.blockchain.validate_and_execute_transaction(tx_id)
            
            return {
                "system": "blockchain",
                "action": action,
                "success": result.get("success", False),
                "tx_id": tx_id
            }
        
        elif action == "record_transaction":
            # Similar to process_transaction
            return await self._execute_blockchain_action("process_transaction", parameters)
        
        else:
            return {
                "system": "blockchain",
                "action": action,
                "success": False,
                "error": "Unknown blockchain action"
            }
    
    async def _execute_bridge_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bridge action"""
        
        if action == "process_deposit":
            from_chain = parameters.get("from_chain", "ethereum")
            from_address = parameters.get("from_address")
            to_address = parameters.get("to_address")
            amount = parameters.get("amount", 0)
            
            result = await self.bridge.deposit_to_overmanifold(
                from_chain, from_address, to_address, amount
            )
            
            return {
                "system": "bridge",
                "action": action,
                "success": result.get("success", False),
                "operation_id": result.get("operation_id")
            }
        
        else:
            return {
                "system": "bridge",
                "action": action,
                "success": False,
                "error": "Unknown bridge action"
            }
    
    async def handle_user_registration(self, phone: str, email: str, name: str = "") -> Dict[str, Any]:
        """Handle complete user registration flow"""
        
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.USER_ACTION,
            source="registration",
            data={
                "action": "register",
                "phone": phone,
                "email": email,
                "name": name
            },
            priority="high"
        )
        
        return await self.orchestrate_event(event)
    
    async def handle_payment_received(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        phone: str = None,
        email: str = None
    ) -> Dict[str, Any]:
        """Handle payment received flow"""
        
        event = OrchestrationEvent(
            event_type=OrchestrationEventType.TRANSACTION_EVENT,
            source="payment",
            data={
                "action": "payment",
                "from_address": from_address,
                "to_address": to_address,
                "amount": amount,
                "phone": phone,
                "email": email
            },
            priority="high"
        )
        
        return await self.orchestrate_event(event)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all systems"""
        
        # Get individual system statistics
        sms_stats = self.sms_system.get_system_health()
        email_stats = asyncio.run(self.email_system.get_email_statistics())
        blockchain_stats = self.blockchain.get_chain_stats()
        bridge_stats = self.bridge.get_bridge_statistics()
        
        return {
            "orchestrator": self.system_status["orchestrator"],
            "subsystems": {
                "sms": {
                    "status": self.system_status["sms"],
                    "statistics": sms_stats
                },
                "email": {
                    "status": self.system_status["email"],
                    "statistics": email_stats
                },
                "blockchain": {
                    "status": self.system_status["blockchain"],
                    "statistics": blockchain_stats
                },
                "bridge": {
                    "status": self.system_status["bridge"],
                    "statistics": bridge_stats
                }
            },
            "total_events_processed": len(self.events),
            "active_handlers": len(self.event_handlers)
        }


# Global orchestrator instance
llm_orchestrator = LLMOrchestrator()