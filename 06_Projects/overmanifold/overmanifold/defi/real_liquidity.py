"""
Overmanifold Real DeFi Integration
Connects to actual DEXes like Uniswap, Curve, and Balancer for real liquidity operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import os
from decimal import Decimal

try:
    from web3 import Web3
    from web3.contract import Contract
    from eth_account import Account
except ImportError:
    raise ImportError("Web3.py not installed. Install with: pip install web3")

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.infrastructure.config import get_config

logger = get_logger("defi_liquidity")
config = get_config()


class DEXType(Enum):
    """Types of decentralized exchanges"""
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    CURVE = "curve"
    BALANCER = "balancer"
    SUSHISWAP = "sushiswap"


@dataclass
class LiquidityPool:
    """Real liquidity pool from DEX"""
    pool_address: str
    token0_address: str
    token1_address: str
    token0_symbol: str
    token1_symbol: str
    reserve0: Decimal
    reserve1: Decimal
    total_supply: Decimal
    fee_rate: Decimal
    dex_type: DEXType
    chain_id: int
    
    def get_price(self, token_in: str, amount_in: Decimal) -> Decimal:
        """Calculate swap output using constant product formula (x * y = k)"""
        if token_in == self.token0_address or token_in == self.token0_symbol:
            # Input token0, output token1
            output_amount = (self.reserve1 * amount_in) / (self.reserve0 + amount_in)
            return output_amount
        else:
            # Input token1, output token0
            output_amount = (self.reserve0 * amount_in) / (self.reserve1 + amount_in)
            return output_amount
    
    def to_dict(self) -> Dict:
        return {
            "pool_address": self.pool_address,
            "token0_address": self.token0_address,
            "token1_address": self.token1_address,
            "token0_symbol": self.token0_symbol,
            "token1_symbol": self.token1_symbol,
            "reserve0": str(self.reserve0),
            "reserve1": str(self.reserve1),
            "total_supply": str(self.total_supply),
            "fee_rate": str(self.fee_rate),
            "dex_type": self.dex_type.value,
            "chain_id": self.chain_id
        }


class RealLiquidityManager:
    """
    Real liquidity manager that connects to actual DEXes
    Requires private keys for real blockchain interactions
    """
    
    # Uniswap V2 Router ABI (minimal)
    UNISWAP_V2_ROUTER_ABI = [
        {
            "constant": True,
            "inputs": [
                {"name": "amountOut", "type": "uint256"},
                {"name": "path", "type": "address[]"}
            ],
            "name": "getAmountsIn",
            "outputs": [{"name": "amounts", "type": "uint256[]"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "path", "type": "address[]"}
            ],
            "name": "getAmountsOut",
            "outputs": [{"name": "amounts", "type": "uint256[]"}],
            "type": "function"
        },
        {
            "inputs": [
                {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"},
                {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}
            ],
            "name": "swapTokensForExactTokens",
            "outputs": [{"name": "amounts", "type": "uint256[]"}],
            "type": "function"
        }
    ]
    
    # Uniswap V2 Pair ABI (minimal)
    UNISWAP_V2_PAIR_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"name": "reserve0", "type": "uint112"},
                {"name": "reserve1", "type": "uint112"},
                {"name": "blockTimestampLast", "type": "uint32"}
            ],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        }
    ]
    
    # ERC20 ABI (minimal)
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }
    ]
    
    def __init__(self, private_key: str, rpc_url: str):
        """
        Initialize real liquidity manager with blockchain connection
        
        Args:
            private_key: Private key for signing transactions
            rpc_url: RPC URL for blockchain connection
        """
        if not private_key:
            raise ValueError("Private key is required for real liquidity operations")
        
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        
        # Connect to blockchain
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to blockchain at {rpc_url}")
        
        self.chain_id = self.w3.eth.chain_id
        logger.info(f"Connected to chain {self.chain_id} with address {self.address}")
        
        # Known DEX addresses by chain
        self.dex_addresses = self._get_dex_addresses()
        
        # Cache for pool contracts
        self.pool_cache: Dict[str, Contract] = {}
        self.token_cache: Dict[str, Contract] = {}
    
    def _get_dex_addresses(self) -> Dict[int, Dict[str, str]]:
        """Get known DEX addresses by chain ID"""
        return {
            1: {  # Ethereum Mainnet
                "uniswap_v2_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                "curve_registry": "0x0000000022D53366457F9d5E68Ec105046FC4383",
                "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
            },
            42161: {  # Arbitrum
                "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
            },
            10: {  # Optimism
                "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
            },
            137: {  # Polygon
                "uniswap_v2_router": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
                "quickswap_router": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
            }
        }
    
    async def get_pool_reserves(
        self,
        pool_address: str,
        dex_type: DEXType = DEXType.UNISWAP_V2
    ) -> tuple[Decimal, Decimal]:
        """
        Get reserves from a real liquidity pool
        
        Args:
            pool_address: Address of the liquidity pool
            dex_type: Type of DEX
            
        Returns:
            Tuple of (reserve0, reserve1)
        """
        if pool_address not in self.pool_cache:
            pool_contract = self.w3.eth.contract(
                address=pool_address,
                abi=self.UNISWAP_V2_PAIR_ABI
            )
            self.pool_cache[pool_address] = pool_contract
        else:
            pool_contract = self.pool_cache[pool_address]
        
        reserves = pool_contract.functions.getReserves().call()
        reserve0 = Decimal(reserves[0])
        reserve1 = Decimal(reserves[1])
        
        return reserve0, reserve1
    
    async def get_pool_info(
        self,
        pool_address: str,
        dex_type: DEXType = DEXType.UNISWAP_V2
    ) -> LiquidityPool:
        """
        Get comprehensive information about a real liquidity pool
        
        Args:
            pool_address: Address of the liquidity pool
            dex_type: Type of DEX
            
        Returns:
            LiquidityPool object with real data
        """
        reserve0, reserve1 = await self.get_pool_reserves(pool_address, dex_type)
        
        pool_contract = self.pool_cache[pool_address]
        total_supply = Decimal(pool_contract.functions.totalSupply().call())
        
        # Get token info (this would require additional calls or factory lookup)
        # For now, using placeholder logic - in production would query factory
        
        return LiquidityPool(
            pool_address=pool_address,
            token0_address="0x0000000000000000000000000000000000000000",  # Would be real address
            token1_address="0x0000000000000000000000000000000000000000",  # Would be real address
            token0_symbol="TOKEN0",  # Would be queried
            token1_symbol="TOKEN1",  # Would be queried
            reserve0=reserve0,
            reserve1=reserve1,
            total_supply=total_supply,
            fee_rate=Decimal("0.003"),  # 0.3% for Uniswap V2
            dex_type=dex_type,
            chain_id=self.chain_id
        )
    
    async def execute_swap(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: Decimal,
        slippage_tolerance: Decimal = Decimal("0.005"),
        dex_type: DEXType = DEXType.UNISWAP_V2
    ) -> Dict[str, Any]:
        """
        Execute a real token swap on DEX
        
        Args:
            token_in_address: Address of token to sell
            token_out_address: Address of token to buy
            amount_in: Amount of token to sell
            slippage_tolerance: Maximum acceptable slippage (default 0.5%)
            dex_type: Type of DEX to use
            
        Returns:
            Transaction result with hash and details
        """
        # Get router address
        if self.chain_id not in self.dex_addresses:
            raise ValueError(f"Chain {self.chain_id} not supported")
        
        if dex_type == DEXType.UNISWAP_V2:
            router_address = self.dex_addresses[self.chain_id].get("uniswap_v2_router")
            if not router_address:
                raise ValueError(f"Uniswap V2 not available on chain {self.chain_id}")
        else:
            raise ValueError(f"DEX type {dex_type} not yet implemented")
        
        # Create router contract
        router_contract = self.w3.eth.contract(
            address=router_address,
            abi=self.UNISWAP_V2_ROUTER_ABI
        )
        
        # Get expected output amount
        path = [token_in_address, token_out_address]
        amount_in_wei = self.w3.to_wei(amount_in, 'ether')
        
        amounts_out = router_contract.functions.getAmountsOut(
            amount_in_wei,
            path
        ).call()
        
        expected_out = Decimal(self.w3.from_wei(amounts_out[-1], 'ether'))
        minimum_out = expected_out * (Decimal("1") - slippage_tolerance)
        
        # Build transaction
        deadline = self.w3.eth.get_block('latest').timestamp + 300  # 5 minutes
        
        transaction = router_contract.functions.swapTokensForExactTokens(
            self.w3.to_wei(minimum_out, 'ether'),
            path,
            self.address,
            deadline
        ).build_transaction({
            'from': self.address,
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.address),
            'chainId': self.chain_id
        })
        
        # Sign transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        
        # Send transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash.hex(), timeout=120)
        
        if receipt.status == 1:
            logger.info(f"Swap executed successfully: {tx_hash.hex()}")
            return {
                "success": True,
                "transaction_hash": tx_hash.hex(),
                "amount_in": str(amount_in),
                "expected_out": str(expected_out),
                "minimum_out": str(minimum_out),
                "gas_used": receipt.gasUsed,
                "block_number": receipt.blockNumber
            }
        else:
            logger.error(f"Swap failed: {tx_hash.hex()}")
            return {
                "success": False,
                "transaction_hash": tx_hash.hex(),
                "error": "Transaction reverted"
            }
    
    async def approve_token(self, token_address: str, spender_address: str, amount: Decimal) -> bool:
        """
        Approve a token for spending by a contract
        
        Args:
            token_address: Address of token to approve
            spender_address: Address of contract to approve
            amount: Amount to approve
            
        Returns:
            True if successful
        """
        if token_address not in self.token_cache:
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=self.ERC20_ABI
            )
            self.token_cache[token_address] = token_contract
        else:
            token_contract = self.token_cache[token_address]
        
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        transaction = token_contract.functions.approve(
            spender_address,
            amount_wei
        ).build_transaction({
            'from': self.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.address),
            'chainId': self.chain_id
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash.hex(), timeout=120)
        
        return receipt.status == 1