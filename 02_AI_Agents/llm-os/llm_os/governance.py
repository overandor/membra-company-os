"""Governance — Safety gates, policy enforcement, and human approval flows.

The Governance module is the OS security kernel. It enforces:
1. Hard policy gates on irreversible actions
2. Cost ceilings and risk limits
3. Human approval for critical operations
4. Activity logging and audit trails
5. Emergency halt capabilities

Policies are evaluated BEFORE any action that could:
- Move real money
- Deploy to production
- Train expensive models
- Expose secrets
- Modify OS code itself
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set


class ActionClass(Enum):
    SAFE = "safe"               # Read-only, local, reversible
    STANDARD = "standard"       # Normal operations with cost tracking
    RISKY = "risky"             # Higher cost or external impact
    CRITICAL = "critical"       # Money movement, production deploy, key exposure
    SELF_MODIFYING = "self_mod" # OS modifying its own code


class ApprovalState(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    BYPASSED_SIMULATION = "bypassed_simulation"


@dataclass
class Policy:
    """A governance policy that controls what actions are permitted."""
    name: str
    action_classes: Set[ActionClass]
    daily_cost_limit_usd: float = 100.0
    single_action_cost_limit_usd: float = 50.0
    require_human_approval_for: Set[ActionClass] = field(default_factory=lambda: {
        ActionClass.CRITICAL, ActionClass.SELF_MODIFYING
    })
    allowed_trading_symbols: Set[str] = field(default_factory=set)
    max_trading_position_usd: float = 0.0
    allow_real_payments: bool = False
    allow_production_deploy: bool = False
    allow_model_training: bool = True
    allow_self_modification: bool = False
    simulation_mode: bool = True

    def is_allowed(self, action_class: ActionClass) -> bool:
        return action_class in self.action_classes

    def requires_approval(self, action_class: ActionClass) -> bool:
        if self.simulation_mode and action_class != ActionClass.SELF_MODIFYING:
            return False
        return action_class in self.require_human_approval_for


@dataclass
class ActionRequest:
    """A request to perform an action, tracked for audit."""
    request_id: str
    action_type: str
    action_class: ActionClass
    description: str
    estimated_cost_usd: float
    actor: str  # Which subsystem requested this
    payload: dict = field(default_factory=dict)
    requested_at: float = field(default_factory=time.time)
    approval_state: ApprovalState = ApprovalState.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None
    executed_at: Optional[float] = None
    result: Optional[dict] = None

    def hash(self) -> str:
        data = f"{self.request_id}:{self.action_type}:{self.actor}:{self.requested_at}"
        return hashlib.sha256(data.encode()).hexdigest()


class Governance:
    """Central governance and safety controller for the LLM OS.

    All subsystems must route potentially dangerous actions through here.
    """

    def __init__(self, policy: Optional[Policy] = None, audit_log_path: str = None):
        self.policy = policy or self._default_policy()
        self.audit_log_path = audit_log_path or "/tmp/llm_os_audit.jsonl"
        self.pending_requests: Dict[str, ActionRequest] = {}
        self.approved_requests: Dict[str, ActionRequest] = {}
        self.rejected_requests: Dict[str, ActionRequest] = {}
        self.daily_spent_usd: float = 0.0
        self.day_start: float = time.time()
        self._reset_daily_if_needed()
        self._halted: bool = False
        self._halt_reason: Optional[str] = None

    def _default_policy(self) -> Policy:
        """Default conservative policy — safe for development."""
        return Policy(
            name="conservative_default",
            action_classes={ActionClass.SAFE, ActionClass.STANDARD, ActionClass.RISKY},
            daily_cost_limit_usd=50.0,
            single_action_cost_limit_usd=25.0,
            require_human_approval_for={ActionClass.CRITICAL, ActionClass.SELF_MODIFYING},
            allow_real_payments=False,
            allow_production_deploy=False,
            allow_model_training=True,
            allow_self_modification=False,
            simulation_mode=True,
        )

    def _reset_daily_if_needed(self):
        """Reset daily counters at UTC midnight."""
        now = time.time()
        seconds_in_day = 86400
        if now - self.day_start >= seconds_in_day:
            self.daily_spent_usd = 0.0
            self.day_start = now

    def request_action(self, action_type: str, action_class: ActionClass,
                       description: str, estimated_cost_usd: float,
                       actor: str, payload: dict = None) -> ActionRequest:
        """Request permission to perform an action.

        Returns an ActionRequest. Check approval_state to see if approved.
        If PENDING, the action requires human approval.
        """
        self._reset_daily_if_needed()

        if self._halted:
            req = ActionRequest(
                request_id=f"req-{int(time.time()*1000)}",
                action_type=action_type,
                action_class=action_class,
                description=description,
                estimated_cost_usd=estimated_cost_usd,
                actor=actor,
                payload=payload or {},
                approval_state=ApprovalState.REJECTED,
            )
            req.result = {"error": f"OS halted: {self._halt_reason}"}
            self._log(req)
            return req

        req = ActionRequest(
            request_id=f"req-{int(time.time()*1000)}-{hashlib.sha256(description.encode()).hexdigest()[:8]}",
            action_type=action_type,
            action_class=action_class,
            description=description,
            estimated_cost_usd=estimated_cost_usd,
            actor=actor,
            payload=payload or {},
        )

        # Check if action class is allowed by policy
        if not self.policy.is_allowed(action_class):
            req.approval_state = ApprovalState.REJECTED
            req.result = {"error": f"Action class {action_class.value} not permitted by policy {self.policy.name}"}
            self.rejected_requests[req.request_id] = req
            self._log(req)
            return req

        # Check cost limits
        if estimated_cost_usd > self.policy.single_action_cost_limit_usd:
            req.approval_state = ApprovalState.REJECTED
            req.result = {"error": f"Cost ${estimated_cost_usd} exceeds single-action limit ${self.policy.single_action_cost_limit_usd}"}
            self.rejected_requests[req.request_id] = req
            self._log(req)
            return req

        if self.daily_spent_usd + estimated_cost_usd > self.policy.daily_cost_limit_usd:
            req.approval_state = ApprovalState.REJECTED
            req.result = {"error": f"Daily cost limit ${self.policy.daily_cost_limit_usd} would be exceeded"}
            self.rejected_requests[req.request_id] = req
            self._log(req)
            return req

        # Check if human approval required
        if self.policy.requires_approval(action_class):
            req.approval_state = ApprovalState.PENDING
            self.pending_requests[req.request_id] = req
            self._log(req)
            return req

        # Auto-approve in simulation mode or for safe actions
        if self.policy.simulation_mode:
            req.approval_state = ApprovalState.BYPASSED_SIMULATION
        else:
            req.approval_state = ApprovalState.APPROVED
        req.approved_at = time.time()
        req.approved_by = "auto"
        self.approved_requests[req.request_id] = req
        self._log(req)
        return req

    def approve_request(self, request_id: str, approved_by: str = "human") -> bool:
        """Human approves a pending request."""
        req = self.pending_requests.get(request_id)
        if not req:
            return False
        req.approval_state = ApprovalState.APPROVED
        req.approved_by = approved_by
        req.approved_at = time.time()
        self.approved_requests[request_id] = req
        del self.pending_requests[request_id]
        self._log(req)
        return True

    def reject_request(self, request_id: str, reason: str = "") -> bool:
        """Human rejects a pending request."""
        req = self.pending_requests.get(request_id)
        if not req:
            return False
        req.approval_state = ApprovalState.REJECTED
        req.result = {"error": reason or "Rejected by operator"}
        self.rejected_requests[request_id] = req
        del self.pending_requests[request_id]
        self._log(req)
        return True

    def record_execution(self, request_id: str, result: dict, actual_cost_usd: float = 0.0):
        """Record that an approved action was executed and its result."""
        req = self.approved_requests.get(request_id)
        if not req:
            return False
        req.executed_at = time.time()
        req.result = result
        self.daily_spent_usd += actual_cost_usd
        self._log(req)
        return True

    def halt(self, reason: str):
        """Emergency halt — stop all non-safe actions immediately."""
        self._halted = True
        self._halt_reason = reason
        self._log_audit("HALT", {"reason": reason, "timestamp": time.time()})

    def resume(self):
        """Resume from halt after human review."""
        self._halted = False
        self._halt_reason = None
        self._log_audit("RESUME", {"timestamp": time.time()})

    def is_halted(self) -> bool:
        return self._halted

    def get_status(self) -> dict:
        self._reset_daily_if_needed()
        return {
            "policy": self.policy.name,
            "simulation_mode": self.policy.simulation_mode,
            "halted": self._halted,
            "halt_reason": self._halt_reason,
            "daily_spent_usd": self.daily_spent_usd,
            "daily_limit_usd": self.policy.daily_cost_limit_usd,
            "pending_approvals": len(self.pending_requests),
            "approved_today": len([r for r in self.approved_requests.values()
                                    if r.approved_at and r.approved_at > self.day_start]),
            "rejected_today": len([r for r in self.rejected_requests.values()
                                    if r.requested_at > self.day_start]),
        }

    def _log(self, req: ActionRequest):
        entry = {
            "timestamp": time.time(),
            "request_id": req.request_id,
            "action_type": req.action_type,
            "action_class": req.action_class.value,
            "actor": req.actor,
            "estimated_cost": req.estimated_cost_usd,
            "state": req.approval_state.value,
            "hash": req.hash(),
        }
        self._log_audit("ACTION", entry)

    def _log_audit(self, event_type: str, data: dict):
        entry = {"event_type": event_type, "data": data}
        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass
