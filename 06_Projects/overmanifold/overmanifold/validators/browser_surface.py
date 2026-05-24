"""
Overmanifold Browser-Native Validator Surfaces
Real WebAssembly and WebGPU implementations for cryptographic proof verification.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.validators.real_wasm import RealWASMValidator, WASMValidationResult
from overmanifold.validators.real_webgpu import RealWebGPUValidator, WebGPUValidationResult

logger = get_logger("browser_validator")


class ComputeBackend(Enum):
    """Types of compute backends"""
    WEBASSEMBLY = "wasm"
    WEBGPU = "webgpu"
    CPU = "cpu"


@dataclass
class ValidationResult:
    """Result of validation operation"""
    task_id: str
    valid: bool
    confidence: float
    execution_time_ms: float
    backend_used: ComputeBackend
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "valid": self.valid,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "backend_used": self.backend_used.value,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class MerkleProof:
    """Merkle proof structure"""
    leaf_hash: str
    proof_path: List[tuple[str, bool]]  # (sibling_hash, is_left)
    expected_root: str
    
    def to_dict(self) -> Dict:
        return {
            "leaf_hash": self.leaf_hash,
            "proof_path": [{"hash": h, "is_left": is_left} for h, is_left in self.proof_path],
            "expected_root": self.expected_root
        }


class RealWASMValidatorWrapper:
    """
    Wrapper for real WASM validation
    """
    
    def __init__(self, wasm_module_path: Optional[str] = None):
        self.validator = RealWASMValidator(wasm_module_path)
    
    def validate_merkle_proof(
        self,
        proof: MerkleProof,
        expected_root: str
    ) -> ValidationResult:
        """Validate Merkle proof using real WASM"""
        result = self.validator.validate_merkle_proof_wasm(
            proof.leaf_hash,
            proof.proof_path,
            expected_root
        )
        
        return ValidationResult(
            task_id=f"wasm_{datetime.utcnow().timestamp()}",
            valid=result.valid,
            confidence=result.confidence,
            execution_time_ms=result.execution_time_ms,
            backend_used=ComputeBackend.WEBASSEMBLY,
            error_message=result.error_message,
            metadata={
                "memory_used": result.memory_used,
                "gas_consumed": result.gas_consumed
            }
        )


class RealWebGPUValidatorWrapper:
    """
    Wrapper for real WebGPU validation
    """
    
    def __init__(self, preferred_adapter: Optional[str] = None):
        self.validator = RealWebGPUValidator(preferred_adapter)
    
    def validate_merkle_proof_parallel(
        self,
        proof: MerkleProof,
        expected_root: str
    ) -> ValidationResult:
        """Validate Merkle proof using real WebGPU"""
        result = self.validator.validate_merkle_proof_parallel(
            proof.leaf_hash,
            proof.proof_path,
            expected_root
        )
        
        return ValidationResult(
            task_id=f"webgpu_{datetime.utcnow().timestamp()}",
            valid=result.valid,
            confidence=result.confidence,
            execution_time_ms=result.execution_time_ms,
            backend_used=ComputeBackend.WEBGPU,
            error_message=result.error_message,
            metadata={
                "gpu_time_ms": result.gpu_time_ms,
                "memory_used_mb": result.memory_used_mb,
                "compute_passes": result.compute_passes
            }
        )
    
    def validate_batch_proofs(
        self,
        proofs: List[tuple[str, List[tuple[str, bool]], str]]
    ) -> List[ValidationResult]:
        """Validate multiple proofs in parallel using real WebGPU"""
        results = self.validator.validate_batch_proofs_parallel(proofs)
        
        return [
            ValidationResult(
                task_id=f"webgpu_batch_{datetime.utcnow().timestamp()}_{i}",
                valid=result.valid,
                confidence=result.confidence,
                execution_time_ms=result.execution_time_ms,
                backend_used=ComputeBackend.WEBGPU,
                error_message=result.error_message,
                metadata=result.metadata
            )
            for i, result in enumerate(results)
        ]


class BrowserValidatorSurface:
    """
    Real browser validator surface using actual WASM and WebGPU
    Provides cryptographic validation capabilities in browser environments
    """
    
    def __init__(
        self,
        wasm_module_path: Optional[str] = None,
        preferred_gpu_adapter: Optional[str] = None
    ):
        """
        Initialize browser validator surface with real implementations
        
        Args:
            wasm_module_path: Path to WASM module file
            preferred_gpu_adapter: Preferred GPU adapter name
        """
        self.wasm_validator = RealWASMValidatorWrapper(wasm_module_path)
        self.webgpu_validator = RealWebGPUValidatorWrapper(preferred_gpu_adapter)
        self.validation_history: List[ValidationResult] = []
        
        logger.info("Browser validator surface initialized with real WASM and WebGPU")
    
    def validate_merkle_proof(
        self,
        proof: MerkleProof,
        backend: ComputeBackend = ComputeBackend.WEBASSEMBLY
    ) -> ValidationResult:
        """
        Validate Merkle proof using specified backend
        
        Args:
            proof: Merkle proof to validate
            backend: Compute backend to use
            
        Returns:
            ValidationResult
        """
        if backend == ComputeBackend.WEBASSEMBLY:
            result = self.wasm_validator.validate_merkle_proof(proof, proof.expected_root)
        elif backend == ComputeBackend.WEBGPU:
            result = self.webgpu_validator.validate_merkle_proof_parallel(proof, proof.expected_root)
        else:
            raise ValueError(f"Unsupported backend: {backend}")
        
        self.validation_history.append(result)
        return result
    
    def validate_signature(
        self,
        message: str,
        signature: str,
        public_key: str,
        backend: ComputeBackend = ComputeBackend.WEBASSEMBLY
    ) -> ValidationResult:
        """
        Validate cryptographic signature
        
        Args:
            message: Message to verify
            signature: Signature as hex string
            public_key: Public key as hex string
            backend: Compute backend to use
            
        Returns:
            ValidationResult
        """
        if backend != ComputeBackend.WEBASSEMBLY:
            raise ValueError("Signature validation only supported with WASM backend")
        
        result = self.wasm_validator.validator.validate_signature_wasm(message, signature, public_key)
        
        validation_result = ValidationResult(
            task_id=f"wasm_sig_{datetime.utcnow().timestamp()}",
            valid=result.valid,
            confidence=result.confidence,
            execution_time_ms=result.execution_time_ms,
            backend_used=backend,
            error_message=result.error_message
        )
        
        self.validation_history.append(validation_result)
        return validation_result
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        if not self.validation_history:
            return {
                "total_validations": 0,
                "successful_validations": 0,
                "failed_validations": 0,
                "average_execution_time_ms": 0.0,
                "backend_usage": {}
            }
        
        successful = sum(1 for r in self.validation_history if r.valid)
        failed = len(self.validation_history) - successful
        avg_time = sum(r.execution_time_ms for r in self.validation_history) / len(self.validation_history)
        
        backend_usage = {}
        for result in self.validation_history:
            backend = result.backend_used.value
            if backend not in backend_usage:
                backend_usage[backend] = 0
            backend_usage[backend] += 1
        
        return {
            "total_validations": len(self.validation_history),
            "successful_validations": successful,
            "failed_validations": failed,
            "average_execution_time_ms": avg_time,
            "backend_usage": backend_usage
        }


class ValidatorSurfaceIntegration:
    """
    Integration layer for validator surfaces
    Manages multiple validator instances and provides unified interface
    """
    
    def __init__(
        self,
        browser_validator: Optional[BrowserValidatorSurface] = None,
        wasm_module_path: Optional[str] = None,
        preferred_gpu_adapter: Optional[str] = None
    ):
        """
        Initialize validator surface integration
        
        Args:
            browser_validator: Browser validator instance (if None, creates new)
            wasm_module_path: Path to WASM module
            preferred_gpu_adapter: Preferred GPU adapter
        """
        self.browser_validator = browser_validator or BrowserValidatorSurface(
            wasm_module_path,
            preferred_gpu_adapter
        )
        
        logger.info("Validator surface integration initialized")
    
    def validate_proof(
        self,
        proof: MerkleProof,
        backend: ComputeBackend = ComputeBackend.WEBASSEMBLY
    ) -> ValidationResult:
        """Validate proof through integrated surface"""
        return self.browser_validator.validate_merkle_proof(proof, backend)
    
    def batch_validate(
        self,
        proofs: List[tuple[str, List[tuple[str, bool]], str]]
    ) -> List[ValidationResult]:
        """Batch validate proofs using WebGPU"""
        merkle_proofs = [
            MerkleProof(leaf_hash, proof_path, expected_root)
            for leaf_hash, proof_path, expected_root in proofs
        ]
        
        return self.browser_validator.webgpu_validator.validate_batch_proofs(
            [(p.leaf_hash, p.proof_path, p.expected_root) for p in merkle_proofs]
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and capabilities"""
        return {
            "wasm_available": self.browser_validator.wasm_validator.validator.loaded,
            "webgpu_available": self.browser_validator.webgpu_validator.validator.loaded,
            "validation_stats": self.browser_validator.get_validation_stats(),
            "supported_backends": [ComputeBackend.WEBASSEMBLY.value, ComputeBackend.WEBGPU.value]
        }