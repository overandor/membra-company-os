"""
MEMBRA Universal Token Routing Network

Verified adapters for cross-token and cross-chain routing.
Only approved tokens through verified routes.
Does NOT claim automatic support for every coin.
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from abc import ABC, abstractmethod

from .config import L3Config, DEFAULT_CONFIG, RouteConfig, TokenConfig, Chain
from .proof_book import proof_book, ProofType


@dataclass
class RouteQuote:
    from_token: str
    to_token: str
    from_amount: int
    to_amount: int
    fee_amount: int
    fee_bps: int
    adapter: str
    route_hash: str
    expires_at: float
    slippage_bps: int = 100  # 1% default


class TokenAdapter(ABC):
    """Base class for verified token routing adapters."""

    @abstractmethod
    def adapter_name(self) -> str:
        ...

    @abstractmethod
    def get_quote(self, from_token: TokenConfig, to_token: TokenConfig,
                  amount: int, fee_bps: int) -> Optional[RouteQuote]:
        ...

    @abstractmethod
    def execute_route(self, quote: RouteQuote, sender: str,
                      receiver: str) -> Optional[str]:
        """Execute route, return tx signature or None."""
        ...

    @abstractmethod
    def validate_liquidity(self, from_token: TokenConfig, to_token: TokenConfig,
                           amount: int) -> bool:
        ...


class SplSwapAdapter(TokenAdapter):
    """Adapter for Solana SPL token swaps (Jupiter/Orca abstraction)."""

    def adapter_name(self) -> str:
        return "SplSwapAdapter"

    def get_quote(self, from_token: TokenConfig, to_token: TokenConfig,
                  amount: int, fee_bps: int) -> Optional[RouteQuote]:
        # In production: call Jupiter API or Orca SDK
        # Simulated quote for demo
        if amount <= 0:
            return None

        # Simulated exchange rate (1:1 for demo, real would use oracle)
        rate = 1.0
        if from_token.symbol == "SOL" and to_token.symbol == "USDC":
            rate = 150.0  # 1 SOL = 150 USDC
        elif from_token.symbol == "USDC" and to_token.symbol == "SOL":
            rate = 1.0 / 150.0
        elif from_token.symbol == "MEMBRA" and to_token.symbol == "USDC":
            rate = 0.01  # 1 MEMBRA = 0.01 USDC
        elif from_token.symbol == "USDC" and to_token.symbol == "MEMBRA":
            rate = 100.0

        fee = int(amount * fee_bps / 10000)
        to_amount = int((amount - fee) * rate)

        import hashlib, uuid
        route_hash = hashlib.sha256(
            f"{from_token.symbol}:{to_token.symbol}:{amount}:{time.time()}".encode()
        ).hexdigest()[:16]

        return RouteQuote(
            from_token=from_token.symbol,
            to_token=to_token.symbol,
            from_amount=amount,
            to_amount=to_amount,
            fee_amount=fee,
            fee_bps=fee_bps,
            adapter=self.adapter_name(),
            route_hash=route_hash,
            expires_at=time.time() + 30,  # 30 second quote expiry
        )

    def execute_route(self, quote: RouteQuote, sender: str,
                      receiver: str) -> Optional[str]:
        # In production: build and submit Solana tx via Jupiter/Orca
        # Simulated tx signature
        import uuid
        tx_sig = uuid.uuid4().hex[:44]  # simulates base58 tx sig
        proof_book.append(ProofType.ROUTE_VALIDATION, {
            "adapter": self.adapter_name(),
            "from_token": quote.from_token,
            "to_token": quote.to_token,
            "amount": quote.from_amount,
            "sender": sender,
            "receiver": receiver,
            "tx_signature": tx_sig,
        })
        return tx_sig

    def validate_liquidity(self, from_token: TokenConfig, to_token: TokenConfig,
                           amount: int) -> bool:
        # In production: check pool liquidity
        return True


class WormholeBridgeAdapter(TokenAdapter):
    """Adapter for cross-chain transfers via Wormhole."""

    def adapter_name(self) -> str:
        return "WormholeBridgeAdapter"

    def get_quote(self, from_token: TokenConfig, to_token: TokenConfig,
                  amount: int, fee_bps: int) -> Optional[RouteQuote]:
        if amount <= 0:
            return None
        if from_token.chain == to_token.chain:
            return None  # Same chain, use SplSwapAdapter

        fee = int(amount * fee_bps / 10000)
        to_amount = amount - fee  # 1:1 for bridged stablecoins

        import hashlib
        route_hash = hashlib.sha256(
            f"bridge:{from_token.chain.value}:{to_token.chain.value}:{amount}:{time.time()}".encode()
        ).hexdigest()[:16]

        return RouteQuote(
            from_token=from_token.symbol,
            to_token=to_token.symbol,
            from_amount=amount,
            to_amount=to_amount,
            fee_amount=fee,
            fee_bps=fee_bps,
            adapter=self.adapter_name(),
            route_hash=route_hash,
            expires_at=time.time() + 60,
        )

    def execute_route(self, quote: RouteQuote, sender: str,
                      receiver: str) -> Optional[str]:
        import uuid
        tx_sig = uuid.uuid4().hex[:44]
        proof_book.append(ProofType.ROUTE_VALIDATION, {
            "adapter": self.adapter_name(),
            "from_token": quote.from_token,
            "to_token": quote.to_token,
            "amount": quote.from_amount,
            "sender": sender,
            "receiver": receiver,
            "tx_signature": tx_sig,
        })
        return tx_sig

    def validate_liquidity(self, from_token: TokenConfig, to_token: TokenConfig,
                           amount: int) -> bool:
        return True


class TokenRouter:
    """
    Routes token transfers through verified adapters.

    Registry of approved tokens + routes.
    Only routes through verified adapters.
    """

    def __init__(self, config: L3Config = DEFAULT_CONFIG):
        self.config = config
        self._adapters: Dict[str, TokenAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self):
        self.register_adapter(SplSwapAdapter())
        self.register_adapter(WormholeBridgeAdapter())

    def register_adapter(self, adapter: TokenAdapter):
        self._adapters[adapter.adapter_name()] = adapter

    def get_quote(self, from_symbol: str, to_symbol: str,
                  amount: int) -> Optional[RouteQuote]:
        """Get a route quote between two approved tokens."""
        from_token = self.config.get_token(from_symbol)
        to_token = self.config.get_token(to_symbol)
        if not from_token or not to_token:
            return None

        route = self.config.get_route(from_symbol, to_symbol)
        if not route:
            return None

        adapter = self._adapters.get(route.adapter)
        if not adapter:
            return None

        if not adapter.validate_liquidity(from_token, to_token, amount):
            return None

        return adapter.get_quote(from_token, to_token, amount, route.fee_bps)

    def execute_route(self, quote: RouteQuote, sender: str,
                      receiver: str) -> Optional[str]:
        """Execute a quoted route, return tx signature."""
        adapter = self._adapters.get(quote.adapter)
        if not adapter:
            return None
        return adapter.execute_route(quote, sender, receiver)

    def get_supported_tokens(self) -> List[str]:
        return [s for s, t in self.config.tokens.items()
                if t.status.value == "approved"]

    def get_routes_for_token(self, symbol: str) -> List[str]:
        """Get all tokens that can be routed to/from this token."""
        destinations = set()
        for r in self.config.routes:
            if r.from_token == symbol and r.enabled:
                destinations.add(r.to_token)
        return sorted(destinations)


# Singleton
token_router = TokenRouter()
