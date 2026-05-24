"""
MEMBRA Bridge Ecosystem - Main Package Initialization
A comprehensive Solana bridging system with hierarchical merkle root taxonomy,
IPFS backup, phone-based wallet addresses, SMS mining, and oracle integration.
"""

from .file_tokenizer import FileTokenizer, HierarchicalMerkleTree, FileMetadata
from .ipfs_manager import IPFSManager, IPFSBackupResult, IPFSRetrievalResult
from .phone_wallet import PhoneWalletMapper, SMSMiningEngine, PhoneWalletBridge
from .oracle_system import OracleSystem, OracleEndpoint, OracleDataPoint
from .kpi_tracker import AdvancedKPITracker, ArbitrageEngine, ArbitrageOpportunity
from .zk_verifier import (
    DeviceProfiler, ZKProofGenerator, ZKProofVerifier, 
    ValidatorNetwork, ZKVerificationCoordinator
)
from .llm_validator import (
    LLMValidatorNetwork, LLMOracle, LLMProvider, 
    OllamaProvider, MockLLMProvider
)
from .liquidity_layer import (
    LiquidityPoolManager, CrossChainBridge, ArbitrageEngine as LiquidityArbitrageEngine,
    AutomatedMarketMaker, LiquidityLayerCoordinator
)

__version__ = "0.1.0"
__author__ = "MEMBRA Network"
__description__ = "Hierarchical Merkle Root Taxonomy with Solana Bridging"

__all__ = [
    # File Tokenization
    'FileTokenizer',
    'HierarchicalMerkleTree', 
    'FileMetadata',
    
    # IPFS Integration
    'IPFSManager',
    'IPFSBackupResult',
    'IPFSRetrievalResult',
    
    # Phone Wallet System
    'PhoneWalletMapper',
    'SMSMiningEngine',
    'PhoneWalletBridge',
    
    # Oracle System
    'OracleSystem',
    'OracleEndpoint',
    'OracleDataPoint',
    
    # KPI Tracking
    'AdvancedKPITracker',
    'ArbitrageEngine',
    'ArbitrageOpportunity',
    
    # ZK Verification
    'DeviceProfiler',
    'ZKProofGenerator',
    'ZKProofVerifier',
    'ValidatorNetwork',
    'ZKVerificationCoordinator',
    
    # LLM Validation
    'LLMValidatorNetwork',
    'LLMOracle',
    'LLMProvider',
    'OllamaProvider',
    'MockLLMProvider',
    
    # Liquidity Layer
    'LiquidityPoolManager',
    'CrossChainBridge',
    'LiquidityArbitrageEngine',
    'AutomatedMarketMaker',
    'LiquidityLayerCoordinator',
]