"""
Overmanifold Human Approval Gate System
Critical security component requiring explicit human approval for value transfer operations.
Testnet v0.1 - No autonomous fund movement without approval.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.infrastructure.config import get_config

logger = get_logger("approval_gate")
config = get_config()


class ApprovalStatus(Enum):
    """Approval status types."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalType(Enum):
    """Types of operations requiring approval."""
    TRANSACTION_WORKER_ACTION = "transaction_worker_action"
    REPO_TOKENIZATION = "repo_tokenization"
    GOVERNANCE_PROPOSAL = "governance_proposal"
    INTENT_EXECUTION = "intent_execution"
    TOKEN_MINT = "token_mint"
    LIQUIDITY_OPERATION = "liquidity_operation"
    TREASURY_OPERATION = "treasury_operation"


@dataclass
class ApprovalRequest:
    """Human approval request."""
    request_id: str
    approval_type: ApprovalType
    operation_data: Dict[str, Any]
    requester_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver_id: Optional[str] = None
    decision_at: Optional[datetime] = None
    decision_reason: Optional[str] = None
    risk_score: float = 0.0
    value_impact: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "approval_type": self.approval_type.value,
            "operation_data": self.operation_data,
            "requester_id": self.requester_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "approver_id": self.approver_id,
            "decision_at": self.decision_at.isoformat() if self.decision_at else None,
            "decision_reason": self.decision_reason,
            "risk_score": self.risk_score,
            "value_impact": self.value_impact
        }
    
    def is_expired(self) -> bool:
        """Check if approval request has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def requires_approval(self) -> bool:
        """Check if this request requires human approval."""
        # All requests require approval in testnet
        return True


class ApprovalGate:
    """
    Human approval gate system.
    Requires explicit human approval for operations that could affect value transfer.
    """
    
    def __init__(self):
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []
        self.auto_approve_threshold: float = 0.0  # No auto-approval in testnet
        self.expiration_hours: int = 24
        self.max_pending_requests: int = 100
        self.authorized_approvers: List[str] = []  # Set from environment
    
        self._load_authorized_approvers()
    
    def _load_authorized_approvers(self) -> None:
        """Load authorized approvers from environment."""
        approvers_env = os.getenv("AUTHORIZED_APPROVERS", "")
        if approvers_env:
            self.authorized_approvers = approvers_env.split(",")
        else:
            # Default to system admin for testnet
            self.authorized_approvers = ["admin@overmanifold.io"]
    
    def create_approval_request(
        self,
        approval_type: ApprovalType,
        operation_data: Dict[str, Any],
        requester_id: str,
        risk_score: float = 0.0,
        value_impact: float = 0.0
    ) -> ApprovalRequest:
        """
        Create a new approval request.
        """
        # Check if auto-approval is possible (should not happen in testnet)
        if risk_score < self.auto_approve_threshold and value_impact == 0.0:
            logger.warning(f"Auto-approval triggered for low-risk operation (should not happen in testnet)")
        
        # Check max pending requests
        if len(self.pending_requests) >= self.max_pending_requests:
            raise RuntimeError("Maximum pending approval requests reached")
        
        # Generate request ID
        request_id = self._generate_request_id(approval_type, operation_data)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=self.expiration_hours)
        
        # Create request
        request = ApprovalRequest(
            request_id=request_id,
            approval_type=approval_type,
            operation_data=operation_data,
            requester_id=requester_id,
            expires_at=expires_at,
            risk_score=risk_score,
            value_impact=value_impact
        )
        
        # Store request
        self.pending_requests[request_id] = request
        
        logger.info(f"Created approval request: {request_id} for {approval_type.value}")
        
        return request
    
    def approve_request(
        self,
        request_id: str,
        approver_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Approve a pending request.
        """
        if request_id not in self.pending_requests:
            logger.error(f"Approval request not found: {request_id}")
            return False
        
        request = self.pending_requests[request_id]
        
        # Check if approver is authorized
        if approver_id not in self.authorized_approvers:
            logger.error(f"Unauthorized approver: {approver_id}")
            return False
        
        # Check if request is expired
        if request.is_expired():
            request.status = ApprovalStatus.EXPIRED
            self._archive_request(request)
            return False
        
        # Approve request
        request.status = ApprovalStatus.APPROVED
        request.approver_id = approver_id
        request.decision_at = datetime.utcnow()
        request.decision_reason = reason
        
        # Archive request
        self._archive_request(request)
        
        logger.info(f"Approved request: {request_id} by {approver_id}")
        
        return True
    
    def reject_request(
        self,
        request_id: str,
        approver_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Reject a pending request.
        """
        if request_id not in self.pending_requests:
            logger.error(f"Approval request not found: {request_id}")
            return False
        
        request = self.pending_requests[request_id]
        
        # Check if approver is authorized
        if approver_id not in self.authorized_approvers:
            logger.error(f"Unauthorized approver: {approver_id}")
            return False
        
        # Reject request
        request.status = ApprovalStatus.REJECTED
        request.approver_id = approver_id
        request.decision_at = datetime.utcnow()
        request.decision_reason = reason
        
        # Archive request
        self._archive_request(request)
        
        logger.info(f"Rejected request: {request_id} by {approver_id}")
        
        return True
    
    def cancel_request(self, request_id: str, requester_id: str) -> bool:
        """
        Cancel a pending request.
        """
        if request_id not in self.pending_requests:
            logger.error(f"Approval request not found: {request_id}")
            return False
        
        request = self.pending_requests[request_id]
        
        # Only requester can cancel
        if request.requester_id != requester_id:
            logger.error(f"Only requester can cancel request")
            return False
        
        # Cancel request
        request.status = ApprovalStatus.CANCELLED
        request.decision_at = datetime.utcnow()
        request.decision_reason = "Cancelled by requester"
        
        # Archive request
        self._archive_request(request)
        
        logger.info(f"Cancelled request: {request_id}")
        
        return True
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID."""
        # Check pending requests
        if request_id in self.pending_requests:
            return self.pending_requests[request_id]
        
        # Check approval history
        for request in self.approval_history:
            if request.request_id == request_id:
                return request
        
        return None
    
    def get_pending_requests(self, approver_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests."""
        if approver_id and approver_id not in self.authorized_approvers:
            return []
        
        # Filter out expired requests
        self._cleanup_expired_requests()
        
        return list(self.pending_requests.values())
    
    def check_approval(self, request_id: str) -> bool:
        """
        Check if a request has been approved.
        """
        request = self.get_request(request_id)
        
        if not request:
            return False
        
        return request.status == ApprovalStatus.APPROVED
    
    def require_approval(
        self,
        approval_type: ApprovalType,
        operation_data: Dict[str, Any],
        requester_id: str
    ) -> str:
        """
        Create approval request and wait for approval.
        Returns request ID.
        """
        # Calculate risk and value impact
        risk_score = self._calculate_risk_score(approval_type, operation_data)
        value_impact = self._calculate_value_impact(approval_type, operation_data)
        
        # Create request
        request = self.create_approval_request(
            approval_type=approval_type,
            operation_data=operation_data,
            requester_id=requester_id,
            risk_score=risk_score,
            value_impact=value_impact
        )
        
        return request.request_id
    
    def _calculate_risk_score(self, approval_type: ApprovalType, operation_data: Dict) -> float:
        """Calculate risk score for approval request."""
        # Base risk by approval type
        risk_by_type = {
            ApprovalType.TRANSACTION_WORKER_ACTION: 0.3,
            ApprovalType.REPO_TOKENIZATION: 0.2,
            ApprovalType.GOVERNANCE_PROPOSAL: 0.4,
            ApprovalType.INTENT_EXECUTION: 0.5,
            ApprovalType.TOKEN_MINT: 0.8,
            ApprovalType.LIQUIDITY_OPERATION: 0.9,
            ApprovalType.TREASURY_OPERATION: 1.0
        }
        
        base_risk = risk_by_type.get(approval_type, 0.5)
        
        # Adjust based on operation data
        if "value" in operation_data:
            value = float(operation_data["value"])
            base_risk += min(value / 10000.0, 0.3)  # Cap at 0.3 additional risk
        
        return min(base_risk, 1.0)
    
    def _calculate_value_impact(self, approval_type: ApprovalType, operation_data: Dict) -> float:
        """Calculate value impact for approval request."""
        # Check if operation affects value
        if approval_type in [ApprovalType.TOKEN_MINT, ApprovalType.LIQUIDITY_OPERATION, 
                           ApprovalType.TREASURY_OPERATION]:
            if "value" in operation_data:
                return float(operation_data["value"])
        
        return 0.0
    
    def _generate_request_id(self, approval_type: ApprovalType, operation_data: Dict) -> str:
        """Generate unique request ID."""
        data = f"{approval_type.value}_{json.dumps(operation_data, sort_keys=True)}_{datetime.utcnow().timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _archive_request(self, request: ApprovalRequest) -> None:
        """Archive an approval request."""
        # Remove from pending
        if request.request_id in self.pending_requests:
            del self.pending_requests[request.request_id]
        
        # Add to history
        self.approval_history.append(request)
        
        # Keep only last 1000 in history
        if len(self.approval_history) > 1000:
            self.approval_history = self.approval_history[-1000:]
    
    def _cleanup_expired_requests(self) -> None:
        """Remove expired requests from pending."""
        expired_requests = [
            request_id for request_id, request in self.pending_requests.items()
            if request.is_expired()
        ]
        
        for request_id in expired_requests:
            request = self.pending_requests[request_id]
            request.status = ApprovalStatus.EXPIRED
            self._archive_request(request)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get approval gate statistics."""
        total_requests = len(self.approval_history) + len(self.pending_requests)
        approved = len([r for r in self.approval_history if r.status == ApprovalStatus.APPROVED])
        rejected = len([r for r in self.approval_history if r.status == ApprovalStatus.REJECTED])
        
        return {
            "total_requests": total_requests,
            "pending_requests": len(self.pending_requests),
            "approved_requests": approved,
            "rejected_requests": rejected,
            "approval_rate": approved / total_requests if total_requests > 0 else 0.0,
            "average_risk_score": sum(r.risk_score for r in self.approval_history) / len(self.approval_history) if self.approval_history else 0.0
        }


# Global approval gate instance
approval_gate = ApprovalGate()


def require_approval(approval_type: ApprovalType, operation_data: Dict, requester_id: str = "system") -> str:
    """
    Convenience function to require approval for an operation.
    Returns request ID.
    """
    return approval_gate.require_approval(approval_type, operation_data, requester_id)


def check_approval(request_id: str) -> bool:
    """
    Convenience function to check if a request has been approved.
    """
    return approval_gate.check_approval(request_id)


def get_approval_statistics() -> Dict[str, Any]:
    """
    Convenience function to get approval statistics.
    """
    return approval_gate.get_statistics()