"""
ZK Verifier Module - Zero-knowledge proof verification for M5 Pro MacBooks
Handles resource staking, ZK proof generation/verification, and validator coordination.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import psutil
import platform
import subprocess
import tempfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeviceSpecs:
    """Device specifications for M5 Pro MacBooks"""
    device_id: str
    model: str
    cpu_cores: int
    memory_gb: int
    gpu_available: bool
    neural_engine: bool
    total_storage_gb: int
    network_speed_mbps: float
    stake_amount: int
    is_active: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ZKProof:
    """Zero-knowledge proof structure"""
    proof_id: str
    statement_hash: str
    proof_data: str
    verifier_id: str
    timestamp: str
    computational_cost: int
    validity_score: float
    is_valid: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ValidatorNode:
    """Validator node information"""
    node_id: str
    device_id: str
    wallet_address: str
    stake_amount: int
    reputation_score: float
    total_proofs_verified: int
    successful_verifications: int
    last_active: str
    status: str  # 'active', 'inactive', 'slashed'
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DeviceProfiler:
    """Profiles M5 Pro MacBook capabilities"""
    
    def __init__(self):
        self.device_specs: Optional[DeviceSpecs] = None
    
    def profile_device(self) -> DeviceSpecs:
        """Profile the current device"""
        # Get system information
        system_info = platform.uname()
        cpu_info = platform.processor()
        
        # Get CPU cores
        cpu_cores = psutil.cpu_count(logical=True)
        physical_cores = psutil.cpu_count(logical=False)
        
        # Get memory
        memory_info = psutil.virtual_memory()
        memory_gb = memory_info.total / (1024**3)
        
        # Check for GPU (macOS specific)
        gpu_available = self._check_gpu_availability()
        neural_engine = self._check_neural_engine()
        
        # Get storage
        disk_info = psutil.disk_usage('/')
        total_storage_gb = disk_info.total / (1024**3)
        
        # Estimate network speed (simplified)
        network_speed = self._estimate_network_speed()
        
        # Generate device ID
        device_id = self._generate_device_id()
        
        # Check if this is an M5 Pro MacBook
        model = self._detect_model()
        
        # Calculate recommended stake based on specs
        stake_amount = self._calculate_stake_amount(
            cpu_cores, memory_gb, total_storage_gb, gpu_available
        )
        
        self.device_specs = DeviceSpecs(
            device_id=device_id,
            model=model,
            cpu_cores=cpu_cores,
            memory_gb=int(memory_gb),
            gpu_available=gpu_available,
            neural_engine=neural_engine,
            total_storage_gb=int(total_storage_gb),
            network_speed_mbps=network_speed,
            stake_amount=stake_amount,
            is_active=True
        )
        
        logger.info(f"Profiled device: {model} with {cpu_cores} cores, {memory_gb:.1f}GB RAM")
        return self.device_specs
    
    def _check_gpu_availability(self) -> bool:
        """Check for GPU availability on macOS"""
        try:
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                  capture_output=True, text=True)
            return 'Metal' in result.stdout or 'GPU' in result.stdout
        except:
            return False
    
    def _check_neural_engine(self) -> bool:
        """Check for Apple Neural Engine"""
        try:
            result = subprocess.run(['sysctl', 'hw.perflevel0.physicalcpu'], 
                                  capture_output=True, text=True)
            # M-series chips have Neural Engine
            return 'Apple M' in platform.processor() or 'arm64' in platform.machine()
        except:
            return False
    
    def _estimate_network_speed(self) -> float:
        """Estimate network speed (simplified)"""
        # In production, this would run actual network speed tests
        return 1000.0  # Default to 1 Gbps
    
    def _generate_device_id(self) -> str:
        """Generate unique device ID"""
        # Use MAC address and other system identifiers
        import uuid
        mac = uuid.getnode()
        system_info = platform.uname()
        combined = f"{mac}{system_info.machine}{system_info.processor}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _detect_model(self) -> str:
        """Detect Mac model"""
        try:
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                  capture_output=True, text=True)
            if 'Mac' in result.stdout:
                for line in result.stdout.split('\n'):
                    if 'Model Name' in line or 'Chip' in line:
                        return line.split(':')[1].strip()
        except:
            pass
        return platform.machine()
    
    def _calculate_stake_amount(self, cores: int, memory_gb: float, 
                               storage_gb: float, has_gpu: bool) -> int:
        """Calculate recommended stake amount based on device capabilities"""
        base_stake = 1000  # Base stake in tokens
        
        # Multipliers for different specs
        core_multiplier = min(2.0, cores / 8.0)  # Up to 2x for 16+ cores
        memory_multiplier = min(1.5, memory_gb / 16.0)  # Up to 1.5x for 24+ GB
        storage_multiplier = min(1.2, storage_gb / 512.0)  # Up to 1.2x for 512+ GB
        gpu_multiplier = 1.3 if has_gpu else 1.0
        
        total_multiplier = (core_multiplier * memory_multiplier * 
                          storage_multiplier * gpu_multiplier)
        
        return int(base_stake * total_multiplier)


class ZKProofGenerator:
    """Generates zero-knowledge proofs for file verification"""
    
    def __init__(self):
        self.proof_history: List[ZKProof] = []
    
    def generate_proof(self, statement: str, witness_data: str, 
                      device_specs: DeviceSpecs) -> ZKProof:
        """Generate a ZK proof for a given statement"""
        # In production, this would use actual ZK-SNARK/ZK-STARK libraries
        # For now, we'll simulate the proof generation
        
        statement_hash = hashlib.sha256(statement.encode()).hexdigest()
        witness_hash = hashlib.sha256(witness_data.encode()).hexdigest()
        
        # Simulate proof generation with computational cost
        proof_data = self._simulate_proof_generation(statement_hash, witness_hash)
        
        # Calculate computational cost based on device specs
        computational_cost = self._calculate_computational_cost(device_specs)
        
        # Generate proof ID
        proof_id = hashlib.sha256(
            f"{statement_hash}{witness_hash}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Calculate validity score
        validity_score = self._calculate_validity_score(device_specs)
        
        proof = ZKProof(
            proof_id=proof_id,
            statement_hash=statement_hash,
            proof_data=proof_data,
            verifier_id=device_specs.device_id,
            timestamp=datetime.now().isoformat(),
            computational_cost=computational_cost,
            validity_score=validity_score,
            is_valid=True  # In production, this would be determined by actual verification
        )
        
        self.proof_history.append(proof)
        logger.info(f"Generated ZK proof {proof_id} with validity score {validity_score:.2f}")
        
        return proof
    
    def _simulate_proof_generation(self, statement_hash: str, witness_hash: str) -> str:
        """Simulate ZK proof generation"""
        # In production, this would use actual ZK libraries
        combined = f"{statement_hash}{witness_hash}"
        simulated_proof = hashlib.sha256(combined.encode()).hexdigest()
        return f"zk_proof_{simulated_proof}"
    
    def _calculate_computational_cost(self, device_specs: DeviceSpecs) -> int:
        """Calculate computational cost in gas units"""
        base_cost = 1000
        
        # Reduce cost for better devices
        core_discount = min(0.5, device_specs.cpu_cores / 16.0)
        memory_discount = min(0.3, device_specs.memory_gb / 32.0)
        gpu_discount = 0.2 if device_specs.gpu_available else 0.0
        
        total_discount = core_discount + memory_discount + gpu_discount
        final_cost = int(base_cost * (1 - total_discount))
        
        return max(100, final_cost)  # Minimum cost
    
    def _calculate_validity_score(self, device_specs: DeviceSpecs) -> float:
        """Calculate proof validity score based on device capabilities"""
        base_score = 0.8
        
        # Bonus for better specs
        core_bonus = min(0.1, device_specs.cpu_cores / 16.0)
        memory_bonus = min(0.05, device_specs.memory_gb / 32.0)
        gpu_bonus = 0.05 if device_specs.gpu_available else 0.0
        
        total_score = base_score + core_bonus + memory_bonus + gpu_bonus
        return min(1.0, total_score)


class ZKProofVerifier:
    """Verifies zero-knowledge proofs"""
    
    def __init__(self):
        self.verification_history: List[Dict] = []
    
    def verify_proof(self, proof: ZKProof, statement: str) -> bool:
        """Verify a ZK proof"""
        # In production, this would use actual ZK verification algorithms
        # For now, we'll simulate verification
        
        statement_hash = hashlib.sha256(statement.encode()).hexdigest()
        
        # Check if statement hash matches
        if proof.statement_hash != statement_hash:
            logger.warning(f"Proof {proof.proof_id} has invalid statement hash")
            return False
        
        # Verify proof structure (simplified)
        is_valid_structure = self._verify_proof_structure(proof)
        
        # Record verification
        verification_record = {
            'proof_id': proof.proof_id,
            'statement_hash': statement_hash,
            'is_valid': is_valid_structure,
            'timestamp': datetime.now().isoformat(),
            'verifier': 'system'
        }
        
        self.verification_history.append(verification_record)
        
        if is_valid_structure:
            logger.info(f"Proof {proof.proof_id} verified successfully")
        else:
            logger.warning(f"Proof {proof.proof_id} verification failed")
        
        return is_valid_structure
    
    def _verify_proof_structure(self, proof: ZKProof) -> bool:
        """Verify the structure of the proof"""
        # In production, this would verify cryptographic signatures
        # For now, check basic structure
        
        if not proof.proof_data.startswith('zk_proof_'):
            return False
        
        if proof.validity_score < 0.5:
            return False
        
        return True
    
    def batch_verify(self, proofs: List[ZKProof], statements: List[str]) -> List[bool]:
        """Verify multiple proofs in batch"""
        if len(proofs) != len(statements):
            raise ValueError("Number of proofs must match number of statements")
        
        results = []
        for proof, statement in zip(proofs, statements):
            result = self.verify_proof(proof, statement)
            results.append(result)
        
        return results


class ValidatorNetwork:
    """Manages network of validator nodes (M5 Pro MacBooks)"""
    
    def __init__(self):
        self.validators: Dict[str, ValidatorNode] = {}
        self.active_validators: List[str] = []
        self.validator_queue: List[str] = []
    
    def register_validator(self, device_specs: DeviceSpecs, 
                          wallet_address: str) -> ValidatorNode:
        """Register a new validator node"""
        node_id = hashlib.sha256(
            f"{device_specs.device_id}{wallet_address}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        validator = ValidatorNode(
            node_id=node_id,
            device_id=device_specs.device_id,
            wallet_address=wallet_address,
            stake_amount=device_specs.stake_amount,
            reputation_score=1.0,  # Start with perfect reputation
            total_proofs_verified=0,
            successful_verifications=0,
            last_active=datetime.now().isoformat(),
            status='active'
        )
        
        self.validators[node_id] = validator
        self.active_validators.append(node_id)
        
        logger.info(f"Registered validator {node_id} with {device_specs.stake_amount} stake")
        return validator
    
    def select_validator(self, proof_complexity: int = 1000) -> Optional[ValidatorNode]:
        """Select a validator based on stake and reputation"""
        if not self.active_validators:
            return None
        
        # Weighted selection based on stake and reputation
        candidates = []
        total_weight = 0.0
        
        for node_id in self.active_validators:
            validator = self.validators[node_id]
            if validator.status == 'active':
                weight = validator.stake_amount * validator.reputation_score
                candidates.append((node_id, weight))
                total_weight += weight
        
        if not candidates:
            return None
        
        # Select based on weights
        import random
        selected = random.choices(
            [c[0] for c in candidates],
            weights=[c[1] for c in candidates],
            k=1
        )[0]
        
        # Update validator stats
        self.validators[selected].total_proofs_verified += 1
        self.validators[selected].last_active = datetime.now().isoformat()
        
        return self.validators[selected]
    
    def update_reputation(self, node_id: str, success: bool):
        """Update validator reputation based on performance"""
        if node_id not in self.validators:
            return
        
        validator = self.validators[node_id]
        
        if success:
            validator.successful_verifications += 1
            # Increase reputation
            validator.reputation_score = min(1.0, validator.reputation_score + 0.01)
        else:
            # Decrease reputation
            validator.reputation_score = max(0.0, validator.reputation_score - 0.05)
            
            # Slash if reputation gets too low
            if validator.reputation_score < 0.3:
                validator.status = 'slashed'
                if node_id in self.active_validators:
                    self.active_validators.remove(node_id)
                logger.warning(f"Validator {node_id} has been slashed due to low reputation")
    
    def get_network_stats(self) -> Dict:
        """Get network statistics"""
        total_stake = sum(v.stake_amount for v in self.validators.values())
        active_stake = sum(v.stake_amount for v in self.validators.values() 
                         if v.status == 'active')
        
        total_proofs = sum(v.total_proofs_verified for v in self.validators.values())
        successful_proofs = sum(v.successful_verifications for v in self.validators.values())
        
        return {
            'total_validators': len(self.validators),
            'active_validators': len(self.active_validators),
            'total_stake': total_stake,
            'active_stake': active_stake,
            'total_proofs_verified': total_proofs,
            'successful_verifications': successful_proofs,
            'success_rate': successful_proofs / total_proofs if total_proofs > 0 else 0.0,
            'average_reputation': sum(v.reputation_score for v in self.validators.values()) / len(self.validators) if self.validators else 0.0
        }


class ZKVerificationCoordinator:
    """Coordinates ZK verification across the validator network"""
    
    def __init__(self):
        self.device_profiler = DeviceProfiler()
        self.proof_generator = ZKProofGenerator()
        self.proof_verifier = ZKProofVerifier()
        self.validator_network = ValidatorNetwork()
    
    async def setup_local_validator(self, wallet_address: str) -> ValidatorNode:
        """Setup current device as a validator"""
        # Profile device
        device_specs = self.device_profiler.profile_device()
        
        # Register as validator
        validator = self.validator_network.register_validator(device_specs, wallet_address)
        
        return validator
    
    async def generate_and_verify_proof(self, statement: str, witness: str) -> Dict:
        """Generate and verify a ZK proof"""
        # Get device specs
        if not self.device_profiler.device_specs:
            device_specs = self.device_profiler.profile_device()
        else:
            device_specs = self.device_profiler.device_specs
        
        # Select validator
        validator = self.validator_network.select_validator()
        
        # Generate proof
        proof = self.proof_generator.generate_proof(statement, witness, device_specs)
        
        # Verify proof
        is_valid = self.proof_verifier.verify_proof(proof, statement)
        
        # Update validator reputation
        if validator:
            self.validator_network.update_reputation(validator.node_id, is_valid)
        
        return {
            'proof': proof.to_dict(),
            'is_valid': is_valid,
            'validator': validator.to_dict() if validator else None,
            'network_stats': self.validator_network.get_network_stats()
        }


def main():
    """Example usage"""
    import asyncio
    
    coordinator = ZKVerificationCoordinator()
    
    # Setup local validator
    wallet_address = "test_wallet_address_12345"
    validator = asyncio.run(coordinator.setup_local_validator(wallet_address))
    
    print(f"=== Validator Registered ===")
    print(f"Node ID: {validator.node_id}")
    print(f"Device: {coordinator.device_profiler.device_specs.model}")
    print(f"Stake: {validator.stake_amount} tokens")
    print(f"Reputation: {validator.reputation_score}")
    
    # Generate and verify a proof
    statement = "File hash matches merkle root"
    witness = "file_hash_12345_merkle_root_67890"
    
    result = asyncio.run(coordinator.generate_and_verify_proof(statement, witness))
    
    print(f"\n=== Proof Verification ===")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()