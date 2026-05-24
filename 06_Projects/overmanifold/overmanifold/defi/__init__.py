"""
Overmanifold DeFi Integration Module
Real connections to decentralized exchanges and liquidity protocols.
"""

from .real_liquidity import (
    RealLiquidityManager,
    LiquidityPool,
    DEXType
)

__all__ = [
    "RealLiquidityManager",
    "LiquidityPool", 
    "DEXType"
]