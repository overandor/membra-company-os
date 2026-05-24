"""
Overmanifold Key Management System
Securely manages API keys, private keys, and sensitive credentials.
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("key_manager")


class KeyManager:
    """
    Secure key management system for production use
    Handles encryption, storage, and retrieval of sensitive keys
    """
    
    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize key manager
        
        Args:
            master_password: Master password for encryption (if None, uses environment variable)
        """
        self.master_password = master_password or os.getenv("KEY_MANAGER_PASSWORD", "")
        if not self.master_password:
            raise ValueError("KEY_MANAGER_PASSWORD environment variable must be set")
        
        self.key_file = os.getenv("KEY_FILE_PATH", "keys.enc")
        self.salt_file = os.getenv("SALT_FILE_PATH", "salt.bin")
        
        # Generate or load salt
        self.salt = self._load_or_generate_salt()
        
        self.cipher_suite = self._create_cipher_suite()
        self.keys: Dict[str, str] = {}
        
        # Load existing keys if available
        if os.path.exists(self.key_file):
            self._load_keys()
    
    def _create_cipher_suite(self) -> Fernet:
        """Create encryption cipher suite from master password"""
        password_bytes = self.master_password.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def _load_or_generate_salt(self) -> bytes:
        """Load existing salt or generate new cryptographically secure salt"""
        if os.path.exists(self.salt_file):
            try:
                with open(self.salt_file, 'rb') as f:
                    salt = f.read()
                if len(salt) == 16:  # Validate salt length
                    logger.info("Loaded existing salt from file")
                    return salt
                else:
                    logger.warning("Invalid salt length, generating new salt")
            except Exception as e:
                logger.error(f"Failed to load salt: {e}, generating new salt")
        
        # Generate new cryptographically secure salt
        salt = secrets.token_bytes(16)  # 16 bytes (128 bits) for PBKDF2
        try:
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            # Set restrictive permissions
            os.chmod(self.salt_file, 0o600)
            logger.info("Generated and saved new cryptographically secure salt")
        except Exception as e:
            logger.error(f"Failed to save salt: {e}")
        
        return salt
    
    def _load_keys(self) -> None:
        """Load encrypted keys from storage"""
        try:
            with open(self.key_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            self.keys = json.loads(decrypted_data.decode())
            logger.info(f"Loaded {len(self.keys)} encrypted keys")
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            self.keys = {}
    
    def _save_keys(self) -> None:
        """Save encrypted keys to storage"""
        try:
            encrypted_data = self.cipher_suite.encrypt(
                json.dumps(self.keys).encode()
            )
            
            with open(self.key_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            logger.info(f"Saved {len(self.keys)} encrypted keys")
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            raise
    
    def set_key(self, key_name: str, key_value: str, encrypt: bool = True) -> None:
        """
        Store a key securely
        
        Args:
            key_name: Name/identifier for the key
            key_value: The actual key value
            encrypt: Whether to encrypt the key (default True)
        """
        if encrypt:
            self.keys[key_name] = key_value
            self._save_keys()
        else:
            # For non-encrypted storage (not recommended for production)
            self.keys[key_name] = key_value
        
        logger.info(f"Stored key: {key_name}")
    
    def get_key(self, key_name: str) -> Optional[str]:
        """
        Retrieve a key
        
        Args:
            key_name: Name/identifier for the key
            
        Returns:
            The key value or None if not found
        """
        return self.keys.get(key_name)
    
    def delete_key(self, key_name: str) -> bool:
        """
        Delete a key
        
        Args:
            key_name: Name/identifier for the key
            
        Returns:
            True if deleted, False if not found
        """
        if key_name in self.keys:
            del self.keys[key_name]
            self._save_keys()
            logger.info(f"Deleted key: {key_name}")
            return True
        return False
    
    def get_llm_api_key(self, provider: str = "openai") -> str:
        """
        Get LLM API key for specified provider
        
        Args:
            provider: LLM provider (openai, anthropic)
            
        Returns:
            API key for the provider
        """
        key_name = f"{provider}_api_key"
        api_key = self.get_key(key_name)
        
        if not api_key:
            # Try environment variable as fallback
            env_var = f"{provider.upper()}_API_KEY"
            api_key = os.getenv(env_var)
            
            if not api_key:
                raise ValueError(f"{provider} API key not found in key manager or environment")
        
        return api_key
    
    def get_blockchain_private_key(self, chain: str = "ethereum") -> str:
        """
        Get blockchain private key for specified chain
        
        Args:
            chain: Blockchain network (ethereum, solana)
            
        Returns:
            Private key for the blockchain
        """
        key_name = f"{chain}_private_key"
        private_key = self.get_key(key_name)
        
        if not private_key:
            # Try environment variable as fallback
            env_var = f"{chain.upper()}_PRIVATE_KEY"
            private_key = os.getenv(env_var)
            
            if not private_key:
                raise ValueError(f"{chain} private key not found in key manager or environment")
        
        return private_key
    
    def get_rpc_url(self, chain: str = "ethereum") -> str:
        """
        Get RPC URL for specified blockchain
        
        Args:
            chain: Blockchain network (ethereum, solana)
            
        Returns:
            RPC URL for the blockchain
        """
        key_name = f"{chain}_rpc_url"
        rpc_url = self.get_key(key_name)
        
        if not rpc_url:
            # Try environment variable as fallback
            env_var = f"{chain.upper()}_RPC_URL"
            rpc_url = os.getenv(env_var)
            
            if not rpc_url:
                raise ValueError(f"{chain} RPC URL not found in key manager or environment")
        
        return rpc_url
    
    def initialize_from_environment(self) -> None:
        """
        Initialize key manager with keys from environment variables
        Useful for initial setup
        """
        env_mappings = {
            "openai_api_key": "OPENAI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "ethereum_private_key": "ETHEREUM_PRIVATE_KEY",
            "ethereum_rpc_url": "ETHEREUM_RPC_URL",
            "solana_private_key": "SOLANA_PRIVATE_KEY",
            "solana_rpc_url": "SOLANA_RPC_URL",
            "github_token": "GITHUB_TOKEN",
        }
        
        for key_name, env_var in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value and env_value != "" and not env_value.startswith("your_"):
                self.set_key(key_name, env_value)
                logger.info(f"Initialized key from environment: {key_name}")
    
    def validate_required_keys(self) -> Dict[str, bool]:
        """
        Validate that all required keys are present
        
        Returns:
            Dictionary mapping key names to availability status
        """
        required_keys = [
            "openai_api_key",
            "ethereum_private_key",
            "ethereum_rpc_url"
        ]
        
        validation_results = {}
        for key_name in required_keys:
            validation_results[key_name] = self.get_key(key_name) is not None
        
        return validation_results
    
    def rotate_key(self, key_name: str, new_key_value: str, backup_old: bool = True) -> bool:
        """
        Rotate a key with optional backup of old value
        
        Args:
            key_name: Name of the key to rotate
            new_key_value: New key value
            backup_old: Whether to backup the old key value
            
        Returns:
            True if rotation successful, False otherwise
        """
        old_key_value = self.get_key(key_name)
        
        if old_key_value and backup_old:
            # Backup old key with timestamp
            backup_key_name = f"{key_name}_backup_{int(datetime.now().timestamp())}"
            self.set_key(backup_key_name, old_key_value)
            logger.info(f"Backed up old key as: {backup_key_name}")
        
        # Set new key
        self.set_key(key_name, new_key_value)
        logger.info(f"Rotated key: {key_name}")
        
        return True
    
    def rotate_all_keys(self) -> Dict[str, bool]:
        """
        Rotate all keys with new random values where applicable
        Note: This should be used with caution as it invalidates all existing keys
        
        Returns:
            Dictionary mapping key names to rotation success status
        """
        rotation_results = {}
        
        for key_name in list(self.keys.keys()):
            try:
                # For API keys, this would require calling the respective services
                # For now, we'll just mark them as needing manual rotation
                if key_name.endswith("_api_key"):
                    logger.warning(f"API key {key_name} requires manual rotation through service provider")
                    rotation_results[key_name] = False
                elif key_name.endswith("_private_key"):
                    # Generate new private key (simplified - in production use proper key generation)
                    new_key = secrets.token_hex(32)
                    self.rotate_key(key_name, new_key)
                    rotation_results[key_name] = True
                else:
                    rotation_results[key_name] = False
            except Exception as e:
                logger.error(f"Failed to rotate key {key_name}: {e}")
                rotation_results[key_name] = False
        
        return rotation_results
    
    def get_key_metadata(self, key_name: str) -> Dict[str, Any]:
        """
        Get metadata about a key (rotation history, age, etc.)
        
        Args:
            key_name: Name of the key
            
        Returns:
            Dictionary with key metadata
        """
        metadata = {
            "exists": key_name in self.keys,
            "has_backup": any(k.startswith(f"{key_name}_backup_") for k in self.keys.keys()),
            "backup_count": sum(1 for k in self.keys.keys() if k.startswith(f"{key_name}_backup_"))
        }
        
        return metadata


class HSMKeyManager(KeyManager):
    """
    HSM-backed key manager for production use
    Provides hardware security module integration for enhanced key protection
    """
    
    def __init__(self, master_password: Optional[str] = None, hsm_config: Optional[Dict] = None):
        """
        Initialize HSM-backed key manager
        
        Args:
            master_password: Master password for encryption (fallback if HSM unavailable)
            hsm_config: HSM configuration dictionary
        """
        super().__init__(master_password)
        self.hsm_config = hsm_config or {}
        self.hsm_available = self._initialize_hsm()
        
        if not self.hsm_available:
            logger.warning("HSM not available, falling back to software encryption")
    
    def _initialize_hsm(self) -> bool:
        """
        Initialize HSM connection
        
        Returns:
            True if HSM available, False otherwise
        """
        try:
            # Check for HSM library availability
            # This would typically use libraries like:
            # - PyKCS11 for PKCS#11 HSMs
            # - aws-kms for AWS CloudHSM
            # - azure-keyvault for Azure Dedicated HSM
            # - google-cloud-kms for Google Cloud HSM
            
            hsm_type = self.hsm_config.get("type", "pkcs11")
            
            if hsm_type == "pkcs11":
                # Placeholder for PKCS#11 HSM initialization
                # from PyKCS11 import PyKCS11
                # lib = PyKCS11.load_lib(self.hsm_config.get("library_path"))
                # self.hsm_slot = self.hsm_config.get("slot")
                # self.hsm_pin = self.hsm_config.get("pin")
                logger.info("PKCS#11 HSM support configured but not implemented")
                return False
            
            elif hsm_type == "aws_kms":
                # Placeholder for AWS KMS initialization
                # import boto3
                # self.kms_client = boto3.client('kms')
                logger.info("AWS KMS support configured but not implemented")
                return False
            
            elif hsm_type == "azure_keyvault":
                # Placeholder for Azure Key Vault initialization
                # from azure.identity import DefaultAzureCredential
                # from azure.keyvault.secrets import SecretClient
                logger.info("Azure Key Vault support configured but not implemented")
                return False
            
            elif hsm_type == "google_cloud_kms":
                # Placeholder for Google Cloud KMS initialization
                # from google.cloud import kms
                logger.info("Google Cloud KMS support configured but not implemented")
                return False
            
            else:
                logger.warning(f"Unknown HSM type: {hsm_type}")
                return False
                
        except ImportError as e:
            logger.warning(f"HSM library not available: {e}")
            return False
        except Exception as e:
            logger.error(f"HSM initialization failed: {e}")
            return False
    
    def set_key_hsm(self, key_name: str, key_value: str, hsm_protected: bool = True) -> None:
        """
        Store a key with HSM protection
        
        Args:
            key_name: Name/identifier for the key
            key_value: The actual key value
            hsm_protected: Whether to use HSM protection (default True)
        """
        if hsm_protected and self.hsm_available:
            # Store key in HSM
            self._store_key_in_hsm(key_name, key_value)
        else:
            # Fall back to software encryption
            self.set_key(key_name, key_value)
    
    def _store_key_in_hsm(self, key_name: str, key_value: str) -> None:
        """
        Store key in HSM (placeholder implementation)
        
        Args:
            key_name: Name of the key
            key_value: Key value to store
        """
        # This would implement actual HSM key storage
        # Example for PKCS#11:
        # self.hsm_session.generateKey(key_template)
        logger.warning("HSM key storage not implemented, using fallback")
        self.set_key(key_name, key_value)
    
    def get_key_hsm(self, key_name: str, hsm_protected: bool = True) -> Optional[str]:
        """
        Retrieve a key from HSM
        
        Args:
            key_name: Name/identifier for the key
            hsm_protected: Whether to use HSM protection (default True)
            
        Returns:
            The key value or None if not found
        """
        if hsm_protected and self.hsm_available:
            return self._get_key_from_hsm(key_name)
        else:
            return self.get_key(key_name)
    
    def _get_key_from_hsm(self, key_name: str) -> Optional[str]:
        """
        Retrieve key from HSM (placeholder implementation)
        
        Args:
            key_name: Name of the key
            
        Returns:
            Key value or None
        """
        # This would implement actual HSM key retrieval
        logger.warning("HSM key retrieval not implemented, using fallback")
        return self.get_key(key_name)


def create_production_key_manager() -> KeyManager:
    """
    Create a key manager for production use
    Requires KEY_MANAGER_PASSWORD environment variable to be set
    """
    master_password = os.getenv("KEY_MANAGER_PASSWORD")
    if not master_password:
        raise ValueError(
            "KEY_MANAGER_PASSWORD environment variable must be set for production key management"
        )
    
    key_manager = KeyManager(master_password)
    
    # Initialize from environment if keys are available
    key_manager.initialize_from_environment()
    
    # Validate required keys
    validation = key_manager.validate_required_keys()
    missing_keys = [k for k, v in validation.items() if not v]
    
    if missing_keys:
        logger.warning(f"Missing required keys: {missing_keys}")
    
    return key_manager