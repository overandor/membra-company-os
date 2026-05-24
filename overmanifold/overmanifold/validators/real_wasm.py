"""
Overmanifold Real WASM Validation System
Uses actual WebAssembly for cryptographic proof verification.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import struct

try:
    import wasmtime
except ImportError:
    raise ImportError("Wasmtime not installed. Install with: pip install wasmtime")

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("real_wasm")


class WASMValidationError(Exception):
    """WASM validation error"""
    pass


@dataclass
class WASMValidationResult:
    """Result of WASM validation"""
    valid: bool
    confidence: float
    execution_time_ms: float
    memory_used: int
    gas_consumed: int
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "memory_used": self.memory_used,
            "gas_consumed": self.gas_consumed,
            "error_message": self.error_message,
            "metadata": self.metadata or {}
        }


class RealWASMValidator:
    """
    Real WebAssembly validator using actual WASM runtime
    Loads and executes WASM modules for cryptographic operations
    """
    
    # Security limits
    MAX_WASM_MODULE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_MEMORY_SIZE = 128 * 1024 * 1024  # 128MB
    MAX_EXECUTION_TIME_MS = 5000  # 5 seconds
    MAX_INPUT_SIZE = 1024 * 1024  # 1MB
    
    def __init__(self, wasm_module_path: Optional[str] = None):
        """
        Initialize real WASM validator
        
        Args:
            wasm_module_path: Path to WASM module file
        """
        self.wasm_module_path = wasm_module_path
        self.engine = wasmtime.Engine()
        self.module = None
        self.store = wasmtime.Store(self.engine)
        self.loaded = False
        
        if wasm_module_path:
            self.load_module(wasm_module_path)
    
    def load_module(self, wasm_path: str) -> None:
        """
        Load WASM module from file
        
        Args:
            wasm_path: Path to WASM file
        """
        try:
            # Validate file path
            if not wasm_path or not isinstance(wasm_path, str):
                raise WASMValidationError("Invalid WASM file path")
            
            # Check file exists and is accessible
            if not os.path.exists(wasm_path):
                raise WASMValidationError(f"WASM file not found: {wasm_path}")
            
            # Check file size to prevent DoS
            file_size = os.path.getsize(wasm_path)
            if file_size > self.MAX_WASM_MODULE_SIZE:
                raise WASMValidationError(
                    f"WASM module too large: {file_size} bytes (max: {self.MAX_WASM_MODULE_SIZE} bytes)"
                )
            
            if file_size == 0:
                raise WASMValidationError("WASM module is empty")
            
            # Read WASM bytes
            with open(wasm_path, 'rb') as f:
                wasm_bytes = f.read()
            
            # Validate WASM magic number (0x00 0x61 0x73 0x6D)
            if len(wasm_bytes) < 4 or wasm_bytes[:4] != b'\x00\x61\x73\x6D':
                raise WASMValidationError("Invalid WASM file format (missing magic number)")
            
            # Validate WASM version (0x01 0x00 0x00 0x00)
            if len(wasm_bytes) < 8 or wasm_bytes[4:8] != b'\x01\x00\x00\x00':
                raise WASMValidationError("Unsupported WASM version")
            
            # Load module with validation
            self.module = wasmtime.Module(self.engine, wasm_bytes)
            self.loaded = True
            logger.info(f"Loaded WASM module from {wasm_path} (size: {file_size} bytes)")
            
        except WASMValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to load WASM module: {e}")
            raise WASMValidationError(f"Failed to load WASM module: {e}")
    
    def validate_merkle_proof_wasm(
        self,
        leaf_hash: str,
        proof_path: List[tuple[str, bool]],
        expected_root: str
    ) -> WASMValidationResult:
        """
        Validate Merkle proof using actual WASM execution
        
        Args:
            leaf_hash: Leaf hash as hex string
            proof_path: List of (sibling_hash, is_left) tuples
            expected_root: Expected root hash
            
        Returns:
            WASMValidationResult with actual WASM execution metrics
        """
        start_time = datetime.utcnow()
        
        try:
            # Input validation
            if not self.loaded:
                raise WASMValidationError("WASM module not loaded")
            
            # Validate leaf_hash format
            if not leaf_hash or not isinstance(leaf_hash, str):
                raise WASMValidationError("Invalid leaf hash format")
            
            try:
                leaf_bytes = bytes.fromhex(leaf_hash)
                if len(leaf_bytes) != 32:  # Standard hash size
                    raise WASMValidationError(f"Invalid leaf hash length: {len(leaf_bytes)} (expected 32)")
            except ValueError:
                raise WASMValidationError("Invalid leaf hash hex encoding")
            
            # Validate expected_root format
            if not expected_root or not isinstance(expected_root, str):
                raise WASMValidationError("Invalid expected root format")
            
            try:
                root_bytes = bytes.fromhex(expected_root)
                if len(root_bytes) != 32:
                    raise WASMValidationError(f"Invalid root hash length: {len(root_bytes)} (expected 32)")
            except ValueError:
                raise WASMValidationError("Invalid root hash hex encoding")
            
            # Validate proof_path
            if not isinstance(proof_path, list):
                raise WASMValidationError("Invalid proof path format")
            
            if len(proof_path) > 64:  # Reasonable limit
                raise WASMValidationError(f"Proof path too long: {len(proof_path)} (max 64)")
            
            for i, (sibling_hash, is_left) in enumerate(proof_path):
                if not isinstance(sibling_hash, str):
                    raise WASMValidationError(f"Invalid sibling hash at index {i}")
                
                try:
                    sibling_bytes = bytes.fromhex(sibling_hash)
                    if len(sibling_bytes) != 32:
                        raise WASMValidationError(f"Invalid sibling hash length at index {i}")
                except ValueError:
                    raise WASMValidationError(f"Invalid sibling hash hex encoding at index {i}")
                
                if not isinstance(is_left, bool):
                    raise WASMValidationError(f"Invalid is_left value at index {i}")
            
            # Create instance with WASI support
            linker = wasmtime.Linker(self.engine)
            linker.define_wasi()
            
            # Configure WASI
            wasm_config = wasmtime.Config()
            wasm_config.wasi = True
            
            store = wasmtime.Store(self.engine)
            store.set_wasi({
                "stdin": wasmtime.StdinStream(),
                "stdout": wasmtime.StdoutStream(),
                "stderr": wasmtime.StderrStream(),
            })
            
            # Instantiate the module
            instance = linker.instantiate(store, self.module)
            
            # Get the validate function
            validate_func = instance.exports(store, "validate_merkle_proof")
            
            # Prepare input data
            input_data = self._serialize_merkle_input(leaf_hash, proof_path, expected_root)
            
            # Allocate memory and write input data
            memory = instance.exports(store, "memory")
            memory_data = memory.data(store)
            
            input_offset = len(memory_data) - len(input_data)
            for i, byte in enumerate(input_data):
                memory_data[input_offset + i] = byte
            
            # Call WASM function
            result = validate_func(store, input_offset, len(input_data))
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Parse result
            valid = result == 1
            
            # Get memory usage (approximate)
            memory_used = len(memory_data)
            
            # Get gas consumption (if WASM module provides it)
            try:
                gas_func = instance.exports(store, "get_gas_consumed")
                gas_consumed = gas_func(store)
            except:
                gas_consumed = 0
            
            return WASMValidationResult(
                valid=valid,
                confidence=0.99 if valid else 0.0,
                execution_time_ms=execution_time,
                memory_used=memory_used,
                gas_consumed=gas_consumed,
                metadata={"wasm_module": self.wasm_module_path}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"WASM validation failed: {e}")
            
            return WASMValidationResult(
                valid=False,
                confidence=0.0,
                execution_time_ms=execution_time,
                memory_used=0,
                gas_consumed=0,
                error_message=str(e)
            )
    
    def _serialize_merkle_input(
        self,
        leaf_hash: str,
        proof_path: List[tuple[str, bool]],
        expected_root: str
    ) -> bytes:
        """
        Serialize Merkle proof input for WASM consumption
        
        Args:
            leaf_hash: Leaf hash
            proof_path: Proof path
            expected_root: Expected root
            
        Returns:
            Serialized bytes
        """
        # Simple binary format:
        # [leaf_hash_len:4][leaf_hash:32][proof_count:4][proof_entries...][expected_root:32]
        
        result = bytearray()
        
        # Leaf hash (32 bytes)
        leaf_bytes = bytes.fromhex(leaf_hash)
        result.extend(struct.pack('<I', len(leaf_bytes)))
        result.extend(leaf_bytes)
        
        # Proof path
        result.extend(struct.pack('<I', len(proof_path)))
        for sibling_hash, is_left in proof_path:
            sibling_bytes = bytes.fromhex(sibling_hash)
            result.extend(struct.pack('<I', len(sibling_bytes)))
            result.extend(sibling_bytes)
            result.extend(struct.pack('<?', is_left))
        
        # Expected root
        root_bytes = bytes.fromhex(expected_root)
        result.extend(root_bytes)
        
        return bytes(result)
    
    def compile_solidity_to_wasm(
        self,
        solidity_code: str,
        contract_name: str
    ) -> bytes:
        """
        Compile Solidity contract to WASM (for advanced use cases)
        
        Args:
            solidity_code: Solidity source code
            contract_name: Name of contract
            
        Returns:
            WASM bytes
        """
        # This would use actual Solidity to WASM compiler
        # For now, return placeholder implementation
        logger.warning("Solidity to WASM compilation not fully implemented")
        return b""
    
    def validate_signature_wasm(
        self,
        message: str,
        signature: str,
        public_key: str
    ) -> WASMValidationResult:
        """
        Validate cryptographic signature using WASM
        
        Args:
            message: Message to verify
            signature: Signature as hex string
            public_key: Public key as hex string
            
        Returns:
            WASMValidationResult
        """
        start_time = datetime.utcnow()
        
        try:
            if not self.loaded:
                raise WASMValidationError("WASM module not loaded")
            
            # Similar process to Merkle proof validation
            # Would call signature verification function in WASM
            store = wasmtime.Store(self.engine)
            linker = wasmtime.Linker(self.engine)
            instance = linker.instantiate(store, self.module)
            
            # Call signature verification function
            sig_verify_func = instance.exports(store, "verify_signature")
            
            # Prepare input
            input_data = self._serialize_signature_input(message, signature, public_key)
            memory = instance.exports(store, "memory")
            memory_data = memory.data(store)
            
            input_offset = len(memory_data) - len(input_data)
            for i, byte in enumerate(input_data):
                memory_data[input_offset + i] = byte
            
            result = sig_verify_func(store, input_offset, len(input_data))
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            valid = result == 1
            
            return WASMValidationResult(
                valid=valid,
                confidence=0.99 if valid else 0.0,
                execution_time_ms=execution_time,
                memory_used=len(memory_data),
                gas_consumed=0,
                metadata={"operation": "signature_verification"}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return WASMValidationResult(
                valid=False,
                confidence=0.0,
                execution_time_ms=execution_time,
                memory_used=0,
                gas_consumed=0,
                error_message=str(e)
            )
    
    def _serialize_signature_input(self, message: str, signature: str, public_key: str) -> bytes:
        """Serialize signature verification input"""
        result = bytearray()
        
        # Message
        message_bytes = message.encode('utf-8')
        result.extend(struct.pack('<I', len(message_bytes)))
        result.extend(message_bytes)
        
        # Signature
        sig_bytes = bytes.fromhex(signature)
        result.extend(struct.pack('<I', len(sig_bytes)))
        result.extend(sig_bytes)
        
        # Public key
        pub_bytes = bytes.fromhex(public_key)
        result.extend(struct.pack('<I', len(pub_bytes)))
        result.extend(pub_bytes)
        
        return bytes(result)