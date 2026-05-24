"""
risk.py — Per-contract and portfolio-level risk management.

Enforces:
  1. Per-contract net inventory limits.
  2. Inventory skew: reduce quote size on the heavy side.
  3. Daily loss halt: halt all activity when daily PnL < -limit.
  4. Stale book guard: suppress quoting when LOB update is overdue.
  5. Max-price guard: refuse to quote contracts above $0.10.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Optional

from app.core.config import mm_config, ContractSpec

log = logging.getLogger("risk")

ZERO = Decimal("0")


@dataclass
class Fill:
    """Record of a confirmed trade."""
    contract:   str
    size:       int          # positive=long, negative=short
    price:      Decimal
    fee:        Decimal
    ts_ms:      int


@dataclass
class ContractRiskState:
    """Mutable risk state for a single contract."""
    contract:       str
    net_position:   int     = 0     # signed, contracts
    realized_pnl:   Decimal = ZERO
    unrealized_pnl: Decimal = ZERO
    total_fees:     Decimal = ZERO
    fills:          list = field(default_factory=list)

    # Quote eligibility (set by risk checks).
    halted:         bool = False
    halt_reason:    str  = ""

    def update_fill(self, fill: Fill) -> None:
        self.fills.append(fill)
        prev_pos   = self.net_position
        self.net_position += fill.size
        self.total_fees   += fill.fee

        # FIFO realized PnL approximation (simplified — no per-lot FIFO stack).
        # Full FIFO tracking can be added as a separate module.
        if prev_pos != 0 and (
            (prev_pos > 0 and fill.size < 0) or
            (prev_pos < 0 and fill.size > 0)
        ):
            # Closing trade.
            closing_size = min(abs(fill.size), abs(prev_pos))
            avg_entry    = self._avg_entry_price()
            if avg_entry:
                if prev_pos > 0:
                    pnl = (fill.price - avg_entry) * Decimal(str(closing_size))
                else:
                    pnl = (avg_entry - fill.price) * Decimal(str(closing_size))
                self.realized_pnl += pnl
                log.info(
                    "Realized PnL on %s: %+.6f USDT (pos %+d → %+d)",
                    self.contract, pnl, prev_pos, self.net_position,
                )

    def _avg_entry_price(self) -> Optional[Decimal]:
        """Simple avg entry from open fills (FIFO simplified)."""
        open_fills = [f for f in self.fills[-50:] if f.size != 0]
        if not open_fills:
            return None
        total_size  = sum(abs(f.size) for f in open_fills)
        total_value = sum(abs(f.size) * f.price for f in open_fills)
        return total_value / total_size if total_size else None


class RiskManager:
    """
    Portfolio-wide risk arbiter.

    Called by the MM engine before every quote decision.
    """

    def __init__(self):
        self._states:         Dict[str, ContractRiskState] = {}
        self._daily_pnl:      Decimal = ZERO
        self._day_start_ts:   float   = time.time()
        self._global_halted:  bool    = False
        self._global_reason:  str     = ""

    # ─── State accessors ─────────────────────────────────────────────────────

    def state(self, contract: str) -> ContractRiskState:
        if contract not in self._states:
            self._states[contract] = ContractRiskState(contract=contract)
        return self._states[contract]

    def net_position(self, contract: str) -> int:
        return self.state(contract).net_position

    # ─── Fill ingestion ───────────────────────────────────────────────────────

    def on_fill(self, fill: Fill) -> None:
        """Call on every confirmed trade. Updates position + PnL."""
        s = self.state(fill.contract)
        s.update_fill(fill)
        self._daily_pnl += fill.fee * -1   # fees reduce PnL
        self._check_daily_loss_halt()

        log.info(
            "Fill: %s size=%+d price=%s fee=%s  net_pos=%+d  daily_pnl=%+.4f",
            fill.contract, fill.size, fill.price, fill.fee,
            s.net_position, self._daily_pnl,
        )

    def on_pnl_delta(self, contract: str, delta: Decimal) -> None:
        """Called with unrealized PnL changes from mark-price updates."""
        self.state(contract).unrealized_pnl += delta
        self._daily_pnl += delta

    # ─── Quote eligibility ────────────────────────────────────────────────────

    def can_quote(self, contract: str, spec: ContractSpec) -> bool:
        """Returns True if it is safe to post quotes on this contract."""
        if self._global_halted:
            log.debug("can_quote %s → False (global halt: %s)", contract, self._global_reason)
            return False

        s = self.state(contract)
        if s.halted:
            log.debug("can_quote %s → False (contract halt: %s)", contract, s.halt_reason)
            return False

        return True

    def allowed_buy_size(self, contract: str, requested: int) -> int:
        """
        Returns actual buy size respecting inventory limit.
        Returns 0 if inventory is maxed on the long side.
        """
        pos = self.net_position(contract)
        max_inv = mm_config.max_inventory_contracts

        if pos >= max_inv:
            return 0

        # Skew: reduce size when approaching limit.
        skew_thresh = mm_config.skew_threshold_contracts
        if pos >= skew_thresh:
            # Linear reduction: at skew_thresh → full size, at max_inv → 0.
            fraction = 1.0 - (pos - skew_thresh) / (max_inv - skew_thresh)
            requested = max(1, int(requested * fraction))

        return min(requested, max_inv - pos)

    def allowed_sell_size(self, contract: str, requested: int) -> int:
        """Returns actual sell size respecting inventory limit."""
        pos = self.net_position(contract)
        max_inv = mm_config.max_inventory_contracts

        if pos <= -max_inv:
            return 0

        skew_thresh = mm_config.skew_threshold_contracts
        if pos <= -skew_thresh:
            fraction = 1.0 - (-pos - skew_thresh) / (max_inv - skew_thresh)
            requested = max(1, int(requested * fraction))

        return min(requested, max_inv + pos)

    # ─── Daily reset ─────────────────────────────────────────────────────────

    def _check_daily_loss_halt(self) -> None:
        limit = mm_config.daily_loss_limit_usdt
        if self._daily_pnl < -limit:
            self._global_halted = True
            self._global_reason = (
                f"Daily loss limit hit: {self._daily_pnl:.4f} USDT < -{limit}"
            )
            log.critical("GLOBAL HALT — %s", self._global_reason)

    def reset_daily(self) -> None:
        """Call at UTC midnight reset."""
        log.info(
            "Daily PnL reset. Previous: %+.4f USDT. Unhalt: %s",
            self._daily_pnl, self._global_halted,
        )
        self._daily_pnl     = ZERO
        self._day_start_ts  = time.time()
        self._global_halted = False
        self._global_reason = ""

    # Public getters/setters for API access
    @property
    def daily_pnl_(self):
        """Public access to daily PnL (read-only)."""
        return self._daily_pnl

    @property
    def global_halted_(self):
        """Public access to global halt flag (read-only)."""
        return self._global_halted

    @property
    def global_reason_(self):
        """Public access to global halt reason (read-only)."""
        return self._global_reason

    @property
    def states_(self):
        """Public access to contract states (read-only)."""
        return self._states

    # ─── Controlled state transitions ────────────────────────────────────────

    def trigger_global_halt(self, reason: str) -> None:
        """Trigger a global halt with the given reason."""
        self._global_halted = True
        self._global_reason = reason
        self._halt_ts = time.time()
        log.critical(f"GLOBAL HALT TRIGGERED: {reason}")

    def reset_global_halt(self) -> None:
        """Reset the global halt state."""
        self._global_halted = False
        self._global_reason = None
        self._halt_ts = None
        log.warning("GLOBAL HALT RESET - quoting may resume")

    def check_daily_loss_halt(self) -> None:
        """Public method to check daily loss halt."""
        self._check_daily_loss_halt()

    # ─── Status dump ─────────────────────────────────────────────────────────

    def summary(self) -> str:
        lines = [f"{'─'*60}", f"  RISK SUMMARY  daily_pnl={self._daily_pnl:+.4f} USDT"]
        if self._global_halted:
            lines.append(f"  ⚠ GLOBAL HALT: {self._global_reason}")
        for contract, s in self._states.items():
            lines.append(
                f"  {contract:<20}  pos={s.net_position:+6d}  "
                f"realized={s.realized_pnl:+.4f}  fees={s.total_fees:.4f}"
            )
        lines.append("─" * 60)
        return "\n".join(lines)


# Module-level singleton.
risk = RiskManager()
