"""
Overmanifold Transaction Endpoint Workers
Converts blockchain transactions into Merkle-provable endpoint workers.
Implements V2 capsule specification for transaction-as-endpoint paradigm.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import hashlib

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.types import Hash, EndpointID, StateTransition
from merkle.proof import MerkleTree, MerkleProof


class LifecycleState(Enum):
    """Transaction lifecycle states."""
    MEMPOOL_SEEN = "mempool_seen"
    PENDING = "pending"
    INCLUDED = "included"
    CONFIRMED = "confirmed"
    FINALIZED = "finalized"
    FAILED = "failed"
    REORGED = "reorged"


class EventType(Enum):
    """Transaction event types."""
    TRANSFER = "transfer"
    SWAP = "swap"
    MINT = "mint"
    BURN = "burn"
    DEPLOY = "deploy"
    BRIDGE = "bridge"
    STAKE = "stake"
    UNSTAKE = "unstake"
    ATTEST = "attest"
    ORACLE_UPDATE = "oracle_update"
    GOVERNANCE = "governance"
    UNKNOWN = "unknown"


class FinalityType(Enum):
    """Finality types for confirmation clocks."""
    OPTIMISTIC = "optimistic"
    PROBABILISTIC = "probabilistic"
    DETERMINISTIC = "deterministic"
    ECONOMIC = "economic"


class WorkerMode(Enum):
    """Worker execution modes."""
    ONE_SHOT = "one_shot"
    CONFIRMATION_TRIGGERED = "confirmation_triggered"
    CRON = "cron"
    REORG_WATCH = "reorg_watch"
    ARBITRAGE_WATCH = "arbitrage_watch"


class PushTarget(Enum):
    """Push targets for transaction events."""
    OVERMANIFOLD = "overmanifold"
    IPFS = "ipfs"
    GITHUB = "github"
    ORACLE = "oracle"
    SMS = "sms"
    EMAIL = "email"
    ANOTHER_CHAIN = "another_chain"


@dataclass
class ConfirmationClock:
    """Confirmation clock for transaction finality."""
    min_confirmations: int
    finality_type: FinalityType
    current_confirmations: int = 0
    confirmation_timestamp: Optional[datetime] = None
    finality_timestamp: Optional[datetime] = None
    
    def is_finalized(self) -> bool:
        """Check if transaction is finalized."""
        return self.current_confirmations >= self.min_confirmations
    
    def update_confirmations(self, count: int) -> None:
        """Update confirmation count."""
        self.current_confirmations = count
        if self.is_finalized() and self.finality_timestamp is None:
            self.finality_timestamp = datetime.utcnow()


@dataclass
class KPIVector:
    """Key Performance Indicators for transaction endpoint."""
    confirmation_latency_ms: float = 0.0
    finality_confidence: float = 0.0
    volatility_impact: float = 0.0
    liquidity_impact: float = 0.0
    arbitrage_signal: float = 0.0
    provenance_score: float = 0.0
    execution_risk: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert KPI vector to dictionary."""
        return {
            "confirmation_latency_ms": self.confirmation_latency_ms,
            "finality_confidence": self.finality_confidence,
            "volatility_impact": self.volatility_impact,
            "liquidity_impact": self.liquidity_impact,
            "arbitrage_signal": self.arbitrage_signal,
            "provenance_score": self.provenance_score,
            "execution_risk": self.execution_risk
        }


@dataclass
class TransactionEndpointWorker:
    """
    Transaction Endpoint Worker T = (χ, h, τ, φ, μ, κ, α)
    χ = chain
    h = tx hash
    τ = transaction lifecycle state
    φ = finality policy
    μ = Merkle commitment
    κ = KPI vector
    α = permitted action set
    """
    id: str
    chain_id: str
    tx_hash: str
    explorer_url: str
    lifecycle_state: LifecycleState
    event_type: EventType
    payload_hash: Hash
    merkle_leaf: str
    merkle_root: str
    confirmation_clock: ConfirmationClock
    worker_mode: WorkerMode
    push_targets: List[PushTarget]
    kpis: KPIVector
    permitted_actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert worker to dictionary."""
        return {
            "id": self.id,
            "chain_id": self.chain_id,
            "tx_hash": self.tx_hash,
            "explorer_url": self.explorer_url,
            "lifecycle_state": self.lifecycle_state.value,
            "event_type": self.event_type.value,
            "payload_hash": str(self.payload_hash),
            "merkle_leaf": self.merkle_leaf,
            "merkle_root": self.merkle_root,
            "confirmation_clock": {
                "min_confirmations": self.confirmation_clock.min_confirmations,
                "finality_type": self.confirmation_clock.finality_type.value,
                "current_confirmations": self.confirmation_clock.current_confirmations,
                "confirmation_timestamp": self.confirmation_clock.confirmation_timestamp.isoformat() if self.confirmation_clock.confirmation_timestamp else None,
                "finality_timestamp": self.confirmation_clock.finality_timestamp.isoformat() if self.confirmation_clock.finality_timestamp else None
            },
            "worker_mode": self.worker_mode.value,
            "push_targets": [target.value for target in self.push_targets],
            "kpis": self.kpis.to_dict(),
            "permitted_actions": self.permitted_actions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def transition_state(self, new_state: LifecycleState) -> None:
        """Transition lifecycle state."""
        self.lifecycle_state = new_state
        self.updated_at = datetime.utcnow()
    
    def update_kpis(self, kpi_updates: Dict[str, float]) -> None:
        """Update KPI vector."""
        for key, value in kpi_updates.items():
            if hasattr(self.kpis, key):
                setattr(self.kpis, key, value)
        self.updated_at = datetime.utcnow()


class TransactionObserver:
    """
    Observes blockchain transactions and converts them into endpoint workers.
    """
    
    def __init__(self):
        self.workers: Dict[str, TransactionEndpointWorker] = {}
        self.merkle_tree: Optional[MerkleTree] = None
        self.chain_observers: Dict[str, Any] = {}
    
    def observe_transaction(self, chain_id: str, tx_data: Dict) -> TransactionEndpointWorker:
        """
        Observe a blockchain transaction and convert it into an endpoint worker candidate.
        """
        tx_hash = tx_data.get("hash")
        if not tx_hash:
            raise ValueError("Transaction hash required")
        
        worker_id = f"{chain_id}:{tx_hash[:16]}"
        
        # Classify event type
        event_type = self._classify_event_type(tx_data)
        
        # Create payload hash
        payload_hash = Hash.from_data(tx_data)
        
        # Generate Merkle leaf
        merkle_leaf = self._generate_merkle_leaf(worker_id, tx_data)
        
        # Create confirmation clock
        confirmation_clock = ConfirmationClock(
            min_confirmations=self._get_min_confirmations(chain_id),
            finality_type=self._get_finality_type(chain_id)
        )
        
        # Determine worker mode
        worker_mode = self._determine_worker_mode(event_type, tx_data)
        
        # Create worker
        worker = TransactionEndpointWorker(
            id=worker_id,
            chain_id=chain_id,
            tx_hash=tx_hash,
            explorer_url=self._get_explorer_url(chain_id, tx_hash),
            lifecycle_state=LifecycleState.MEMPOOL_SEEN,
            event_type=event_type,
            payload_hash=payload_hash,
            merkle_leaf=merkle_leaf,
            merkle_root="",  # Will be set when Merkle tree is built
            confirmation_clock=confirmation_clock,
            worker_mode=worker_mode,
            push_targets=self._determine_push_targets(event_type),
            kpis=KPIVector(),
            permitted_actions=self._determine_permitted_actions(event_type)
        )
        
        self.workers[worker_id] = worker
        return worker
    
    def get_transaction_endpoint(self, chain_id: str, tx_hash: str) -> Optional[TransactionEndpointWorker]:
        """Retrieve transaction endpoint state."""
        worker_id = f"{chain_id}:{tx_hash[:16]}"
        return self.workers.get(worker_id)
    
    def update_transaction_state(self, chain_id: str, tx_hash: str, 
                                confirmations: int, state: LifecycleState) -> bool:
        """Update transaction state based on confirmations."""
        worker = self.get_transaction_endpoint(chain_id, tx_hash)
        if not worker:
            return False
        
        worker.confirmation_clock.update_confirmations(confirmations)
        worker.transition_state(state)
        
        return True
    
    def build_merkle_tree(self) -> str:
        """Build Merkle tree from all workers and return root."""
        leaves = [{"worker_id": worker.id, "leaf": worker.merkle_leaf} for worker in self.workers.values()]
        self.merkle_tree = MerkleTree()
        
        # Add leaves to tree
        for leaf_data in leaves:
            self.merkle_tree.add_leaf(leaf_data)
        
        # Build tree
        self.merkle_tree.build_tree()
        
        # Update all workers with the new root
        root_hash = self.merkle_tree.get_root_hash()
        root = str(root_hash) if root_hash else ""
        for worker in self.workers.values():
            worker.merkle_root = root
        
        return root
    
    def create_merkle_proof(self, chain_id: str, tx_hash: str) -> Optional[MerkleProof]:
        """Create a Merkle proof for a transaction endpoint."""
        if not self.merkle_tree:
            self.build_merkle_tree()
        
        worker = self.get_transaction_endpoint(chain_id, tx_hash)
        if not worker:
            return None
        
        leaf_index = list(self.workers.keys()).index(worker.id)
        return self.merkle_tree.generate_proof(leaf_index)
    
    def _classify_event_type(self, tx_data: Dict) -> EventType:
        """Classify transaction event type."""
        # Simplified classification - in production would use more sophisticated analysis
        tx_input = tx_data.get("input", "")
        method_id = tx_input[:10] if len(tx_input) >= 10 else ""
        
        if "transfer" in tx_input.lower():
            return EventType.TRANSFER
        elif "swap" in tx_input.lower() or method_id in ["0x38ed1739", "0x7ff36ab5"]:
            return EventType.SWAP
        elif "mint" in tx_input.lower():
            return EventType.MINT
        elif "burn" in tx_input.lower():
            return EventType.BURN
        elif tx_data.get("contract_creation"):
            return EventType.DEPLOY
        elif "bridge" in tx_input.lower():
            return EventType.BRIDGE
        elif "stake" in tx_input.lower():
            return EventType.STAKE
        elif "unstake" in tx_input.lower():
            return EventType.UNSTAKE
        else:
            return EventType.UNKNOWN
    
    def _generate_merkle_leaf(self, worker_id: str, tx_data: Dict) -> str:
        """Generate Merkle leaf from worker data."""
        leaf_data = {
            "worker_id": worker_id,
            "tx_hash": tx_data.get("hash"),
            "timestamp": datetime.utcnow().isoformat(),
            "data": tx_data
        }
        return hashlib.sha256(json.dumps(leaf_data, sort_keys=True).encode()).hexdigest()
    
    def _get_min_confirmations(self, chain_id: str) -> int:
        """Get minimum confirmations for chain."""
        confirmations = {
            "ethereum": 12,
            "bitcoin": 6,
            "solana": 32,
            "polygon": 10
        }
        return confirmations.get(chain_id.lower(), 6)
    
    def _get_finality_type(self, chain_id: str) -> FinalityType:
        """Get finality type for chain."""
        finality_types = {
            "ethereum": FinalityType.PROBABILISTIC,
            "bitcoin": FinalityType.PROBABILISTIC,
            "solana": FinalityType.OPTIMISTIC,
            "polygon": FinalityType.PROBABILISTIC
        }
        return finality_types.get(chain_id.lower(), FinalityType.PROBABILISTIC)
    
    def _get_explorer_url(self, chain_id: str, tx_hash: str) -> str:
        """Get explorer URL for transaction."""
        explorers = {
            "ethereum": f"https://etherscan.io/tx/{tx_hash}",
            "bitcoin": f"https://blockstream.info/tx/{tx_hash}",
            "solana": f"https://explorer.solana.com/tx/{tx_hash}",
            "polygon": f"https://polygonscan.com/tx/{tx_hash}"
        }
        return explorers.get(chain_id.lower(), f"https://explorer.example.com/tx/{tx_hash}")
    
    def _determine_worker_mode(self, event_type: EventType, tx_data: Dict) -> WorkerMode:
        """Determine worker mode based on event type."""
        if event_type in [EventType.SWAP, EventType.TRANSFER]:
            return WorkerMode.CONFIRMATION_TRIGGERED
        elif event_type == EventType.ORACLE_UPDATE:
            return WorkerMode.ONE_SHOT
        else:
            return WorkerMode.ONE_SHOT
    
    def _determine_push_targets(self, event_type: EventType) -> List[PushTarget]:
        """Determine push targets based on event type."""
        targets = [PushTarget.OVERMANIFOLD]
        
        if event_type in [EventType.TRANSFER, EventType.SWAP]:
            targets.extend([PushTarget.ORACLE, PushTarget.IPFS])
        elif event_type == EventType.ORACLE_UPDATE:
            targets.extend([PushTarget.IPFS, PushTarget.GITHUB])
        
        return targets
    
    def _determine_permitted_actions(self, event_type: EventType) -> List[str]:
        """Determine permitted actions based on event type."""
        actions = ["observe", "create_merkle_leaf"]
        
        if event_type in [EventType.TRANSFER, EventType.SWAP]:
            actions.extend(["push_to_oracle", "update_liquidity_state"])
        elif event_type == EventType.ORACLE_UPDATE:
            actions.extend(["push_to_ipfs", "attest_to_registry"])
        
        return actions


class TransactionWorkerScheduler:
    """
    Schedules and manages transaction endpoint workers.
    """
    
    def __init__(self, observer: TransactionObserver):
        self.observer = observer
        self.scheduled_workers: Dict[str, Dict] = {}
        self.worker_hooks: Dict[str, List[Callable]] = {}
    
    def schedule_worker(self, worker_id: str, schedule_config: Dict) -> bool:
        """Schedule a transaction endpoint as a recurring or confirmation-based worker."""
        worker = self.observer.workers.get(worker_id)
        if not worker:
            return False
        
        self.scheduled_workers[worker_id] = {
            "worker": worker,
            "schedule": schedule_config,
            "last_run": None,
            "next_run": self._calculate_next_run(schedule_config)
        }
        
        return True
    
    def push_transaction_event(self, chain_id: str, tx_hash: str, 
                              push_target: PushTarget, event_data: Dict) -> bool:
        """Push a transaction-derived event into another protocol."""
        worker = self.observer.get_transaction_endpoint(chain_id, tx_hash)
        if not worker:
            return False
        
        if push_target not in worker.push_targets:
            return False
        
        # Execute push based on target
        if push_target == PushTarget.OVERMANIFOLD:
            return self._push_to_overmanifold(worker, event_data)
        elif push_target == PushTarget.IPFS:
            return self._push_to_ipfs(worker, event_data)
        elif push_target == PushTarget.ORACLE:
            return self._push_to_oracle(worker, event_data)
        
        return False
    
    def attest_transaction_endpoint(self, chain_id: str, tx_hash: str, 
                                   registry: str) -> Optional[str]:
        """Attest a transaction endpoint to a protocol registry or public state layer."""
        worker = self.observer.get_transaction_endpoint(chain_id, tx_hash)
        if not worker:
            return None
        
        # Create attestation
        attestation = {
            "worker_id": worker.id,
            "chain_id": worker.chain_id,
            "tx_hash": worker.tx_hash,
            "merkle_root": worker.merkle_root,
            "lifecycle_state": worker.lifecycle_state.value,
            "registry": registry,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Create Merkle proof
        proof = self.observer.create_merkle_proof(chain_id, tx_hash)
        if proof:
            attestation["merkle_proof"] = proof.to_dict()
        
        return hashlib.sha256(json.dumps(attestation, sort_keys=True).encode()).hexdigest()
    
    def register_worker_hook(self, event_type: str, hook: Callable) -> None:
        """Register a hook for worker events."""
        if event_type not in self.worker_hooks:
            self.worker_hooks[event_type] = []
        self.worker_hooks[event_type].append(hook)
    
    def execute_hooks(self, event_type: str, worker: TransactionEndpointWorker) -> None:
        """Execute registered hooks for event type."""
        hooks = self.worker_hooks.get(event_type, [])
        for hook in hooks:
            try:
                hook(worker)
            except Exception as e:
                print(f"Hook execution failed: {e}")
    
    def _calculate_next_run(self, schedule_config: Dict) -> Optional[datetime]:
        """Calculate next run time for scheduled worker."""
        schedule_type = schedule_config.get("type")
        
        if schedule_type == "cron":
            # Simplified cron calculation
            interval = schedule_config.get("interval_seconds", 60)
            return datetime.utcnow() + timedelta(seconds=interval)
        elif schedule_type == "confirmation_triggered":
            return None  # Triggered by confirmations
        
        return None
    
    def _push_to_overmanifold(self, worker: TransactionEndpointWorker, 
                             event_data: Dict) -> bool:
        """Push event to Overmanifold network."""
        # Implementation would integrate with Overmanifold core
        print(f"Pushing worker {worker.id} to Overmanifold")
        return True
    
    def _push_to_ipfs(self, worker: TransactionEndpointWorker, 
                     event_data: Dict) -> bool:
        """Push event to IPFS."""
        # Implementation would integrate with IPFS
        print(f"Pushing worker {worker.id} to IPFS")
        return True
    
    def _push_to_oracle(self, worker: TransactionEndpointWorker, 
                       event_data: Dict) -> bool:
        """Push event to oracle system."""
        # Implementation would integrate with oracle system
        print(f"Pushing worker {worker.id} to oracle")
        return True