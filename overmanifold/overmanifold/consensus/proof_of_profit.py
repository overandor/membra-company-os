"""
Overmanifold Proof-of-Profit Consensus Mechanism
Rewards economically useful state transitions instead of brute-force hashing.
Integrates inverse mining with supply burn tied to verified development and participation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import math
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkType(Enum):
    """Types of economically useful work"""
    SOFTWARE_DEVELOPMENT = "software_development"
    CODE_COMMIT = "code_commit"
    PULL_REQUEST_REVIEW = "pull_request_review"
    DEPLOYMENT_SUCCESS = "deployment_success"
    TEST_PASSING = "test_passing"
    DOCUMENTATION_CONTRIBUTION = "documentation_contribution"
    BUG_FIX = "bug_fix"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    INFERENCE_CONTRIBUTION = "inference_contribution"
    VALIDATION_WORK = "validation_work"
    LIQUIDITY_PROVISION = "liquidity_provision"
    TRUST_ESTABLISHMENT = "trust_establishment"
    SEMANTIC_INTEROPERABILITY = "semantic_interoperability"


class ConsensusStatus(Enum):
    """Status of consensus participation"""
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REWARD_CLAIMED = "reward_claimed"
    SLASHED = "slashed"


@dataclass
class EconomicWork:
    """
    Representation of economically useful work
    """
    work_id: str
    work_type: WorkType
    endpoint_id: str
    description: str
    proof_hash: str
    economic_value: float
    difficulty_score: float  # Higher = more difficult/valuable
    impact_score: float  # Measured impact on network
    timestamp: str
    verification_count: int
    verification_results: List[Dict]
    status: ConsensusStatus
    metadata: Dict
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['work_type'] = self.work_type.value
        data['status'] = self.status.value
        return data


@dataclass
class ProofOfProfit:
    """
    Proof that work generated economic profit/utility
    """
    proof_id: str
    work_id: str
    profit_evidence: Dict
    merkle_root: str
    validator_signatures: List[str]
    consensus_threshold: float
    actual_consensus: float
    reward_amount: float
    burn_amount: float
    timestamp: str
    valid: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InverseMiningOperation:
    """
    Inverse mining operation that burns supply based on useful work
    """
    operation_id: str
    work_id: str
    burn_amount: float
    supply_before_burn: float
    supply_after_burn: float
    scarcity_increase: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TreasuryDeflation:
    """
    Treasury-controlled deflation tied to verified useful work
    """
    deflation_id: str
    work_id: str
    deflation_amount: float
    treasury_balance_before: float
    treasury_balance_after: float
    work_verification_score: float
    economic_multiplier: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ProofOfProfitConsensus:
    """
    Proof-of-Profit Consensus Mechanism
    Rewards economically useful state transitions instead of brute-force hashing
    """
    
    def __init__(
        self,
        initial_supply: float = 1_000_000_000,
        consensus_threshold: float = 0.67,
        verification_window_seconds: int = 3600
    ):
        self.initial_supply = initial_supply
        self.circulating_supply = initial_supply
        self.burned_supply = 0.0
        self.consensus_threshold = consensus_threshold
        self.verification_window = timedelta(seconds=verification_window_seconds)
        
        self.economic_work: Dict[str, EconomicWork] = {}
        self.profit_proofs: Dict[str, ProofOfProfit] = {}
        self.inverse_mining_ops: Dict[str, InverseMiningOperation] = {}
        self.treasury_deflations: Dict[str, TreasuryDeflation] = {}
        
        self.validators: Dict[str, Dict] = {}  # validator_id -> {stake, reputation, total_verifications}
        self.work_queue: List[str] = []
        self.verification_pool: Dict[str, Set[str]] = {}  # work_id -> set of validator_ids
        
        # Economic parameters
        self.base_reward_per_unit_value = 0.001
        self.difficulty_multiplier = 2.0
        self.impact_multiplier = 1.5
        self.burn_rate = 0.0001  # Burn per unit of economic value
        self.deflation_rate = 0.00005  # Treasury deflation per unit of verified work
        
    def register_validator(self, validator_id: str, stake: float = 1000.0):
        """Register a validator for the consensus mechanism"""
        self.validators[validator_id] = {
            'stake': stake,
            'reputation': 1.0,
            'total_verifications': 0,
            'successful_verifications': 0,
            'slashed_count': 0,
            'last_active': datetime.now().isoformat()
        }
        logger.info(f"Registered validator: {validator_id} with stake {stake}")
    
    def submit_economic_work(
        self,
        endpoint_id: str,
        work_type: WorkType,
        description: str,
        proof_data: Dict,
        metadata: Dict = None
    ) -> EconomicWork:
        """
        Submit economically useful work for consensus verification
        """
        work_id = hashlib.sha256(
            f"{endpoint_id}{work_type.value}{description}{json.dumps(proof_data)}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        # Calculate economic value and scores
        economic_value = self._calculate_economic_value(work_type, proof_data)
        difficulty_score = self._calculate_difficulty_score(work_type, proof_data)
        impact_score = self._calculate_impact_score(work_type, proof_data, metadata)
        
        # Generate proof hash
        proof_hash = hashlib.sha256(
            f"{work_id}{json.dumps(proof_data)}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        work = EconomicWork(
            work_id=work_id,
            work_type=work_type,
            endpoint_id=endpoint_id,
            description=description,
            proof_hash=proof_hash,
            economic_value=economic_value,
            difficulty_score=difficulty_score,
            impact_score=impact_score,
            timestamp=datetime.now().isoformat(),
            verification_count=0,
            verification_results=[],
            status=ConsensusStatus.PENDING_VERIFICATION,
            metadata=metadata or {}
        )
        
        self.economic_work[work_id] = work
        self.work_queue.append(work_id)
        self.verification_pool[work_id] = set()
        
        logger.info(f"Submitted economic work: {work_id} of type {work_type.value}")
        return work
    
    def _calculate_economic_value(self, work_type: WorkType, proof_data: Dict) -> float:
        """Calculate economic value of work based on type and evidence"""
        base_values = {
            WorkType.SOFTWARE_DEVELOPMENT: 100.0,
            WorkType.CODE_COMMIT: 50.0,
            WorkType.PULL_REQUEST_REVIEW: 30.0,
            WorkType.DEPLOYMENT_SUCCESS: 200.0,
            WorkType.TEST_PASSING: 25.0,
            WorkType.DOCUMENTATION_CONTRIBUTION: 20.0,
            WorkType.BUG_FIX: 150.0,
            WorkType.FEATURE_IMPLEMENTATION: 180.0,
            WorkType.SECURITY_AUDIT: 300.0,
            WorkType.PERFORMANCE_OPTIMIZATION: 120.0,
            WorkType.INFERENCE_CONTRIBUTION: 80.0,
            WorkType.VALIDATION_WORK: 40.0,
            WorkType.LIQUIDITY_PROVISION: 250.0,
            WorkType.TRUST_ESTABLISHMENT: 100.0,
            WorkType.SEMANTIC_INTEROPERABILITY: 90.0
        }
        
        base_value = base_values.get(work_type, 50.0)
        
        # Adjust based on proof data
        multiplier = 1.0
        if 'complexity' in proof_data:
            multiplier *= (1.0 + proof_data['complexity'] * 0.5)
        if 'lines_changed' in proof_data:
            multiplier *= (1.0 + min(proof_data['lines_changed'] / 1000.0, 1.0))
        if 'test_coverage' in proof_data:
            multiplier *= (1.0 + proof_data['test_coverage'] * 0.3)
        
        return base_value * multiplier
    
    def _calculate_difficulty_score(self, work_type: WorkType, proof_data: Dict) -> float:
        """Calculate difficulty score (0.0 to 1.0)"""
        base_difficulty = {
            WorkType.SOFTWARE_DEVELOPMENT: 0.7,
            WorkType.SECURITY_AUDIT: 0.9,
            WorkType.FEATURE_IMPLEMENTATION: 0.8,
            WorkType.BUG_FIX: 0.6,
            WorkType.PERFORMANCE_OPTIMIZATION: 0.75,
            WorkType.CODE_COMMIT: 0.4,
            WorkType.PULL_REQUEST_REVIEW: 0.5
        }
        
        difficulty = base_difficulty.get(work_type, 0.5)
        
        # Adjust based on proof data
        if 'complexity' in proof_data:
            difficulty = min(1.0, difficulty + proof_data['complexity'] * 0.2)
        if 'time_spent_hours' in proof_data:
            difficulty = min(1.0, difficulty + min(proof_data['time_spent_hours'] / 100.0, 0.2))
        
        return difficulty
    
    def _calculate_impact_score(self, work_type: WorkType, proof_data: Dict, metadata: Dict) -> float:
        """Calculate impact score (0.0 to 1.0)"""
        base_impact = {
            WorkType.DEPLOYMENT_SUCCESS: 0.9,
            WorkType.SECURITY_AUDIT: 0.85,
            WorkType.LIQUIDITY_PROVISION: 0.8,
            WorkType.BUG_FIX: 0.7,
            WorkType.FEATURE_IMPLEMENTATION: 0.75
        }
        
        impact = base_impact.get(work_type, 0.5)
        
        # Adjust based on metadata
        if metadata and 'users_affected' in metadata:
            impact = min(1.0, impact + min(metadata['users_affected'] / 10000.0, 0.3))
        if metadata and 'revenue_impact' in metadata:
            impact = min(1.0, impact + min(abs(metadata['revenue_impact']) / 100000.0, 0.2))
        
        return impact
    
    def verify_work(self, work_id: str, validator_id: str, signature: str, approved: bool, reasoning: str) -> bool:
        """
        Validator verifies economic work
        """
        if work_id not in self.economic_work:
            logger.error(f"Work {work_id} not found")
            return False
        
        if validator_id not in self.validators:
            logger.error(f"Validator {validator_id} not registered")
            return False
        
        work = self.economic_work[work_id]
        validator = self.validators[validator_id]
        
        # Check if validator already verified this work
        if validator_id in self.verification_pool[work_id]:
            logger.warning(f"Validator {validator_id} already verified work {work_id}")
            return False
        
        # Add verification
        work.verification_count += 1
        work.verification_results.append({
            'validator_id': validator_id,
            'signature': signature,
            'approved': approved,
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat()
        })
        
        self.verification_pool[work_id].add(validator_id)
        validator['total_verifications'] += 1
        
        if approved:
            validator['successful_verifications'] += 1
            validator['reputation'] = min(1.0, validator['reputation'] + 0.01)
        else:
            validator['reputation'] = max(0.0, validator['reputation'] - 0.05)
        
        validator['last_active'] = datetime.now().isoformat()
        
        # Check if consensus threshold reached
        self._check_consensus(work_id)
        
        logger.info(f"Validator {validator_id} verified work {work_id}: {approved}")
        return True
    
    def _check_consensus(self, work_id: str):
        """Check if work has reached consensus threshold"""
        work = self.economic_work[work_id]
        
        if work.verification_count == 0:
            return
        
        # Calculate approval ratio
        approvals = sum(1 for r in work.verification_results if r['approved'])
        approval_ratio = approvals / work.verification_count
        
        # Check if we have enough verifications for consensus
        required_verifications = max(3, int(len(self.validators) * self.consensus_threshold))
        
        if work.verification_count >= required_verifications:
            if approval_ratio >= self.consensus_threshold:
                self._finalize_work(work_id, approved=True)
            elif approval_ratio <= (1.0 - self.consensus_threshold):
                self._finalize_work(work_id, approved=False)
    
    def _finalize_work(self, work_id: str, approved: bool):
        """Finalize work after consensus"""
        work = self.economic_work[work_id]
        
        if approved:
            work.status = ConsensusStatus.VERIFIED
            
            # Generate proof of profit
            profit_proof = self._generate_profit_proof(work_id)
            if profit_proof:
                self.profit_proofs[profit_proof.proof_id] = profit_proof
                
                # Execute inverse mining (burn supply)
                self._execute_inverse_mining(work_id, profit_proof)
                
                # Execute treasury deflation
                self._execute_treasury_deflation(work_id, profit_proof)
        else:
            work.status = ConsensusStatus.REJECTED
            
            # Slash validators who approved erroneously
            self._slash_failed_validators(work_id)
        
        logger.info(f"Finalized work {work_id}: {work.status.value}")
    
    def _generate_profit_proof(self, work_id: str) -> Optional[ProofOfProfit]:
        """Generate proof that work generated economic profit"""
        work = self.economic_work[work_id]
        
        # Calculate reward amount
        base_reward = work.economic_value * self.base_reward_per_unit_value
        difficulty_bonus = work.difficulty_score * self.difficulty_multiplier
        impact_bonus = work.impact_score * self.impact_multiplier
        
        total_reward = base_reward * (1.0 + difficulty_bonus + impact_bonus)
        
        # Calculate burn amount (inverse mining)
        burn_amount = work.economic_value * self.burn_rate
        
        # Generate merkle root from verification results
        verification_hashes = [
            hashlib.sha256(
                f"{r['validator_id']}{r['signature']}{r['approved']}".encode()
            ).hexdigest()
            for r in work.verification_results
        ]
        
        # Simple merkle root calculation
        if verification_hashes:
            merkle_root = hashlib.sha256(''.join(verification_hashes).encode()).hexdigest()
        else:
            merkle_root = work.proof_hash
        
        # Collect validator signatures
        validator_signatures = [r['signature'] for r in work.verification_results if r['approved']]
        
        # Calculate actual consensus
        actual_consensus = (
            sum(1 for r in work.verification_results if r['approved']) / 
            max(work.verification_count, 1)
        )
        
        proof_id = hashlib.sha256(
            f"{work_id}{merkle_root}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        profit_proof = ProofOfProfit(
            proof_id=proof_id,
            work_id=work_id,
            profit_evidence={
                'economic_value': work.economic_value,
                'difficulty_score': work.difficulty_score,
                'impact_score': work.impact_score,
                'verification_count': work.verification_count
            },
            merkle_root=merkle_root,
            validator_signatures=validator_signatures,
            consensus_threshold=self.consensus_threshold,
            actual_consensus=actual_consensus,
            reward_amount=total_reward,
            burn_amount=burn_amount,
            timestamp=datetime.now().isoformat(),
            valid=True
        )
        
        return profit_proof
    
    def _execute_inverse_mining(self, work_id: str, profit_proof: ProofOfProfit):
        """Execute inverse mining by burning supply"""
        if self.circulating_supply <= profit_proof.burn_amount:
            logger.warning(f"Insufficient supply to burn {profit_proof.burn_amount}")
            return
        
        operation_id = hashlib.sha256(
            f"{work_id}{profit_proof.burn_amount}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        supply_before = self.circulating_supply
        self.circulating_supply -= profit_proof.burn_amount
        self.burned_supply += profit_proof.burn_amount
        
        # Calculate scarcity increase
        scarcity_increase = profit_proof.burn_amount / self.initial_supply
        
        inverse_mining = InverseMiningOperation(
            operation_id=operation_id,
            work_id=work_id,
            burn_amount=profit_proof.burn_amount,
            supply_before_burn=supply_before,
            supply_after_burn=self.circulating_supply,
            scarcity_increase=scarcity_increase,
            timestamp=datetime.now().isoformat()
        )
        
        self.inverse_mining_ops[operation_id] = inverse_mining
        
        logger.info(f"Inverse mining: burned {profit_proof.burn_amount} tokens, scarcity increased by {scarcity_increase:.6f}")
    
    def _execute_treasury_deflation(self, work_id: str, profit_proof: ProofOfProfit):
        """Execute treasury-controlled deflation tied to useful work"""
        work = self.economic_work[work_id]
        
        # Calculate deflation amount based on work quality
        work_score = (work.difficulty_score + work.impact_score) / 2.0
        deflation_amount = work.economic_value * self.deflation_rate * (1.0 + work_score)
        
        deflation_id = hashlib.sha256(
            f"{work_id}{deflation_amount}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        treasury_balance = self._get_treasury_balance()
        treasury_before = treasury_balance
        
        # Simulate treasury burn (in production, would be actual treasury operation)
        treasury_after = treasury_before - deflation_amount
        
        treasury_deflation = TreasuryDeflation(
            deflation_id=deflation_id,
            work_id=work_id,
            deflation_amount=deflation_amount,
            treasury_balance_before=treasury_before,
            treasury_balance_after=treasury_after,
            work_verification_score=work_score,
            economic_multiplier=1.0 + work_score,
            timestamp=datetime.now().isoformat()
        )
        
        self.treasury_deflations[deflation_id] = treasury_deflation
        
        logger.info(f"Treasury deflation: {deflation_amount} tokens burned based on work score {work_score:.2f}")
    
    def _get_treasury_balance(self) -> float:
        """Get current treasury balance (simplified)"""
        return self.initial_supply * 0.1  # Assume 10% of initial supply in treasury
    
    def _slash_failed_validators(self, work_id: str):
        """Slash validators who approved rejected work"""
        work = self.economic_work[work_id]
        
        for result in work.verification_results:
            if result['approved']:
                validator_id = result['validator_id']
                if validator_id in self.validators:
                    validator = self.validators[validator_id]
                    validator['reputation'] = max(0.0, validator['reputation'] - 0.1)
                    validator['slashed_count'] += 1
                    
                    # Slash stake
                    slash_amount = validator['stake'] * 0.01
                    validator['stake'] -= slash_amount
                    
                    logger.warning(f"Slashed validator {validator_id}: {slash_amount} stake, reputation decreased")
    
    def claim_reward(self, work_id: str, endpoint_id: str) -> Optional[float]:
        """Claim reward for verified work"""
        if work_id not in self.economic_work:
            return None
        
        work = self.economic_work[work_id]
        
        if work.status != ConsensusStatus.VERIFIED:
            logger.warning(f"Work {work_id} not verified, cannot claim reward")
            return None
        
        if work.endpoint_id != endpoint_id:
            logger.warning(f"Endpoint {endpoint_id} not authorized to claim reward for work {work_id}")
            return None
        
        # Find profit proof
        profit_proof = next(
            (p for p in self.profit_proofs.values() if p.work_id == work_id),
            None
        )
        
        if not profit_proof:
            return None
        
        # Mark as claimed
        work.status = ConsensusStatus.REWARD_CLAIMED
        
        logger.info(f"Reward claimed for work {work_id}: {profit_proof.reward_amount}")
        return profit_proof.reward_amount
    
    def get_supply_metrics(self) -> Dict:
        """Get current supply metrics"""
        scarcity = 1.0 - (self.circulating_supply / self.initial_supply)
        
        return {
            'initial_supply': self.initial_supply,
            'circulating_supply': self.circulating_supply,
            'burned_supply': self.burned_supply,
            'scarcity_ratio': scarcity,
            'deflation_rate': self.burned_supply / self.initial_supply if self.initial_supply > 0 else 0.0,
            'total_work_verified': len([w for w in self.economic_work.values() if w.status == ConsensusStatus.VERIFIED]),
            'total_work_rejected': len([w for w in self.economic_work.values() if w.status == ConsensusStatus.REJECTED]),
            'pending_work': len([w for w in self.economic_work.values() if w.status == ConsensusStatus.PENDING_VERIFICATION])
        }
    
    def get_validator_stats(self) -> Dict:
        """Get validator statistics"""
        total_reputation = sum(v['reputation'] for v in self.validators.values())
        total_stake = sum(v['stake'] for v in self.validators.values())
        
        return {
            'total_validators': len(self.validators),
            'total_stake': total_stake,
            'average_reputation': total_reputation / len(self.validators) if self.validators else 0.0,
            'total_verifications': sum(v['total_verifications'] for v in self.validators.values()),
            'total_slashes': sum(v['slashed_count'] for v in self.validators.values())
        }


def main():
    """Example usage of Proof-of-Profit Consensus"""
    # Initialize consensus mechanism
    consensus = ProofOfProfitConsensus(
        initial_supply=1_000_000_000,
        consensus_threshold=0.67
    )
    
    # Register validators
    consensus.register_validator("validator_1", stake=5000.0)
    consensus.register_validator("validator_2", stake=3000.0)
    consensus.register_validator("validator_3", stake=2000.0)
    
    print("=== Registered Validators ===")
    print(json.dumps(consensus.get_validator_stats(), indent=2))
    
    # Submit economic work
    work = consensus.submit_economic_work(
        endpoint_id="endpoint_1",
        work_type=WorkType.FEATURE_IMPLEMENTATION,
        description="Implement new routing algorithm",
        proof_data={
            'complexity': 0.8,
            'lines_changed': 500,
            'test_coverage': 0.9,
            'time_spent_hours': 40
        },
        metadata={
            'users_affected': 1000,
            'revenue_impact': 50000.0
        }
    )
    
    print(f"\n=== Submitted Economic Work ===")
    print(f"Work ID: {work.work_id}")
    print(f"Economic Value: {work.economic_value:.2f}")
    print(f"Difficulty Score: {work.difficulty_score:.2f}")
    print(f"Impact Score: {work.impact_score:.2f}")
    
    # Validators verify the work
    print(f"\n=== Verifying Work ===")
    consensus.verify_work(work.work_id, "validator_1", "sig1", True, "Work is legitimate and valuable")
    consensus.verify_work(work.work_id, "validator_2", "sig2", True, "High quality implementation")
    consensus.verify_work(work.work_id, "validator_3", "sig3", True, "Good economic value")
    
    # Check work status
    print(f"\n=== Work Status ===")
    print(f"Status: {work.status.value}")
    print(f"Verifications: {work.verification_count}")
    
    # Get supply metrics
    print(f"\n=== Supply Metrics ===")
    print(json.dumps(consensus.get_supply_metrics(), indent=2))
    
    # Claim reward
    if work.status == ConsensusStatus.VERIFIED:
        reward = consensus.claim_reward(work.work_id, "endpoint_1")
        print(f"\n=== Reward Claimed ===")
        print(f"Reward Amount: {reward}")


if __name__ == '__main__':
    main()