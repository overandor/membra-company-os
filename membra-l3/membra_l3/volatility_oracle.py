"""
MEMBRA Proof-of-Volatility Oracle

Monitors real market conditions and generates policy signals.
Signals are logged to ProofBook — they do NOT auto-execute.
Governance must authorize any tokenomic action.

Watches:
- MEMBRA TWAP
- Solana gas-fee conditions
- Liquidity depth
- Oracle freshness
- Treasury coverage ratio

Produces signals:
- VOLATILITY_DETECTED: real price movement confirmed
- VOLATILITY_PAUSED: market too flat for action
- GAS_SPIKE: Solana fees unusually high
- COVERAGE_WARNING: GasVault coverage below minimum
- ORACLE_STALE: data too old to trust
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .config import L3Config, DEFAULT_CONFIG
from .proof_book import proof_book, ProofType


class VolatilitySignal(Enum):
    VOLATILITY_DETECTED = "volatility_detected"
    VOLATILITY_PAUSED = "volatility_paused"
    GAS_SPIKE = "gas_spike"
    GAS_NORMAL = "gas_normal"
    COVERAGE_WARNING = "coverage_warning"
    COVERAGE_HEALTHY = "coverage_healthy"
    ORACLE_STALE = "oracle_stale"
    ORACLE_FRESH = "oracle_fresh"
    LIQUIDITY_LOW = "liquidity_low"
    LIQUIDITY_HEALTHY = "liquidity_healthy"


@dataclass
class PricePoint:
    price_usd: float
    timestamp: float
    source: str  # e.g., "jupiter", "pyth", "switchboard"
    volume_usd: float = 0.0


@dataclass
class GasConditions:
    base_fee_lamports: int
    priority_fee_lamports: int
    timestamp: float
    congested: bool = False


@dataclass
class LiquiditySnapshot:
    token_symbol: str
    pool_usd: float
    depth_2pct_usd: float  # USD to move price 2%
    timestamp: float


@dataclass
class VolatilityReport:
    signal: VolatilitySignal
    confidence: float  # 0.0 - 1.0
    membra_twap: float
    price_change_pct: float
    gas_conditions: GasConditions
    liquidity: LiquiditySnapshot
    coverage_ratio: float
    oracle_age_seconds: float
    timestamp: float
    details: Dict = field(default_factory=dict)


class VolatilityOracle:
    """
    Monitors market data and emits Proof-of-Volatility signals.

    Does NOT execute anything. Signals are logged to ProofBook.
    Governance reads signals to authorize capped actions.
    """

    def __init__(self, config: L3Config = DEFAULT_CONFIG):
        self.config = config
        self._price_history: List[PricePoint] = []
        self._gas_history: List[GasConditions] = []
        self._last_liquidity: Optional[LiquiditySnapshot] = None
        self._last_oracle_update: float = 0.0
        self._last_report: Optional[VolatilityReport] = None

    def feed_price(self, price_usd: float, source: str = "jupiter",
                   volume_usd: float = 0.0):
        """Ingest a price data point."""
        pp = PricePoint(
            price_usd=price_usd,
            timestamp=time.time(),
            source=source,
            volume_usd=volume_usd,
        )
        self._price_history.append(pp)
        self._last_oracle_update = pp.timestamp

        # Prune old data
        cutoff = time.time() - self.config.volatility_twap_window_seconds * 2
        self._price_history = [p for p in self._price_history if p.timestamp >= cutoff]

    def feed_gas(self, base_fee: int, priority_fee: int, congested: bool = False):
        """Ingest Solana gas conditions."""
        gc = GasConditions(
            base_fee_lamports=base_fee,
            priority_fee_lamports=priority_fee,
            timestamp=time.time(),
            congested=congested,
        )
        self._gas_history.append(gc)
        cutoff = time.time() - self.config.volatility_twap_window_seconds * 2
        self._gas_history = [g for g in self._gas_history if g.timestamp >= cutoff]

    def feed_liquidity(self, token_symbol: str, pool_usd: float, depth_2pct_usd: float):
        """Update liquidity snapshot."""
        self._last_liquidity = LiquiditySnapshot(
            token_symbol=token_symbol,
            pool_usd=pool_usd,
            depth_2pct_usd=depth_2pct_usd,
            timestamp=time.time(),
        )

    def assess(self, coverage_ratio: float) -> VolatilityReport:
        """
        Run all checks and produce a volatility report.
        Returns the primary signal + confidence.
        """
        now = time.time()

        # 1. Compute TWAP
        twap, price_change = self._compute_twap()

        # 2. Check oracle freshness
        oracle_age = now - self._last_oracle_update if self._last_oracle_update > 0 else 999999
        oracle_stale = oracle_age > self.config.oracle_staleness_seconds

        # 3. Check gas conditions
        gas = self._latest_gas() or GasConditions(5000, 0, now, False)
        gas_spike = gas.congested or gas.priority_fee_lamports > 100000

        # 4. Check liquidity
        liq = self._last_liquidity or LiquiditySnapshot("MEMBRA", 0, 0, now)
        liquidity_low = liq.pool_usd < 5000 or liq.depth_2pct_usd < 1000

        # 5. Check coverage
        coverage_low = coverage_ratio < self.config.gas_vault_min_coverage_ratio

        # Determine primary signal
        if oracle_stale:
            signal = VolatilitySignal.ORACLE_STALE
            confidence = 0.95
        elif coverage_low:
            signal = VolatilitySignal.COVERAGE_WARNING
            confidence = 0.9
        elif liquidity_low:
            signal = VolatilitySignal.LIQUIDITY_LOW
            confidence = 0.8
        elif gas_spike:
            signal = VolatilitySignal.GAS_SPIKE
            confidence = 0.85
        elif abs(price_change) >= self.config.volatility_signal_threshold:
            signal = VolatilitySignal.VOLATILITY_DETECTED
            confidence = min(0.95, 0.5 + abs(price_change) * 10)
        else:
            signal = VolatilitySignal.VOLATILITY_PAUSED
            confidence = 0.7

        report = VolatilityReport(
            signal=signal,
            confidence=confidence,
            membra_twap=twap,
            price_change_pct=price_change * 100,
            gas_conditions=gas,
            liquidity=liq,
            coverage_ratio=coverage_ratio,
            oracle_age_seconds=oracle_age,
            timestamp=now,
            details={
                "data_points": len(self._price_history),
                "oracle_stale": oracle_stale,
                "gas_spike": gas_spike,
                "liquidity_low": liquidity_low,
                "coverage_low": coverage_low,
            },
        )

        self._last_report = report

        # Log to ProofBook
        proof_book.append(ProofType.VOLATILITY, {
            "signal": signal.value,
            "confidence": confidence,
            "membra_twap": twap,
            "price_change_pct": round(price_change * 100, 4),
            "coverage_ratio": round(coverage_ratio, 4),
            "oracle_age_seconds": round(oracle_age, 1),
            "gas_priority_fee": gas.priority_fee_lamports,
            "liquidity_pool_usd": liq.pool_usd,
        })

        return report

    # ─── Internal ───────────────────────────────────────────

    def _compute_twap(self) -> Tuple[float, float]:
        """Returns (TWAP, price_change_pct)."""
        window = time.time() - self.config.volatility_twap_window_seconds
        recent = [p for p in self._price_history if p.timestamp >= window]

        if len(recent) < 2:
            return (0.0, 0.0)

        # Volume-weighted if volume data exists
        total_volume = sum(p.volume_usd for p in recent)
        if total_volume > 0:
            twap = sum(p.price_usd * p.volume_usd for p in recent) / total_volume
        else:
            twap = sum(p.price_usd for p in recent) / len(recent)

        oldest_price = recent[0].price_usd
        if oldest_price > 0:
            price_change = (recent[-1].price_usd - oldest_price) / oldest_price
        else:
            price_change = 0.0

        return (twap, price_change)

    def _latest_gas(self) -> Optional[GasConditions]:
        return self._gas_history[-1] if self._gas_history else None

    @property
    def last_report(self) -> Optional[VolatilityReport]:
        return self._last_report

    @property
    def can_unlock_rebase(self) -> bool:
        """Check if conditions allow rebase execution."""
        if not self._last_report:
            return False
        r = self._last_report
        return (
            r.signal == VolatilitySignal.VOLATILITY_DETECTED
            and r.confidence >= 0.7
            and not r.details.get("oracle_stale", True)
            and not r.details.get("coverage_low", True)
            and not r.details.get("liquidity_low", True)
        )


# Singleton
volatility_oracle = VolatilityOracle()
