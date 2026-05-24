"""Treasury — Cost tracking, profit calculation, and budget allocation.

The Treasury is the OS accounting department. It tracks:
1. All costs (compute, API calls, trading losses, training time)
2. All revenue (marketplace sales, trading profits, service fees)
3. Profit/loss per subsystem and per activity
4. Budget allocation for autonomous decision-making
5. Runway calculation (how long current funds last at current burn)

All subsystems MUST report costs and revenue to the Treasury.
No subsystem may spend money without Treasury awareness.
"""

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class LedgerEntryType(Enum):
    COST = "cost"
    REVENUE = "revenue"
    TRANSFER = "transfer"
    RESERVE = "reserve"
    YIELD = "yield"


@dataclass
class LedgerEntry:
    entry_id: str
    timestamp: float
    entry_type: LedgerEntryType
    subsystem: str  # "trading", "llm_factory", "marketplace", "system_builder", etc.
    activity: str     # Specific activity within subsystem
    amount_usd: float
    description: str
    metadata: dict = field(default_factory=dict)
    confirmed: bool = True  # False for estimated, True for verified


class Treasury:
    """Central accounting and budget management for the LLM OS."""

    def __init__(self, storage_path: str = None, starting_balance_usd: float = 0.0):
        self.storage_path = storage_path or "/tmp/llm_os_treasury.json"
        self.ledger: List[LedgerEntry] = []
        self.balance_usd = starting_balance_usd
        self.reserves_usd: Dict[str, float] = {
            "risk": 0.0,
            "infrastructure": 0.0,
            "treasury": 0.0,
        }
        self.daily_stats: Dict[str, dict] = {}
        self._load()

    def record_cost(self, subsystem: str, activity: str, amount_usd: float,
                    description: str, metadata: dict = None) -> LedgerEntry:
        """Record a cost incurred by a subsystem."""
        entry = LedgerEntry(
            entry_id=f"cost-{int(time.time()*1000)}",
            timestamp=time.time(),
            entry_type=LedgerEntryType.COST,
            subsystem=subsystem,
            activity=activity,
            amount_usd=-abs(amount_usd),
            description=description,
            metadata=metadata or {},
            confirmed=True,
        )
        self.ledger.append(entry)
        self.balance_usd += entry.amount_usd
        self._update_daily_stats(entry)
        self._persist()
        return entry

    def record_revenue(self, subsystem: str, activity: str, amount_usd: float,
                       description: str, metadata: dict = None) -> LedgerEntry:
        """Record revenue earned by a subsystem."""
        entry = LedgerEntry(
            entry_id=f"rev-{int(time.time()*1000)}",
            timestamp=time.time(),
            entry_type=LedgerEntryType.REVENUE,
            subsystem=subsystem,
            activity=activity,
            amount_usd=abs(amount_usd),
            description=description,
            metadata=metadata or {},
            confirmed=True,
        )
        self.ledger.append(entry)
        self.balance_usd += entry.amount_usd
        self._update_daily_stats(entry)
        self._persist()
        return entry

    def record_estimate(self, subsystem: str, activity: str, estimated_cost_usd: float,
                        description: str) -> LedgerEntry:
        """Record an estimated cost (not yet realized). Does not affect balance."""
        entry = LedgerEntry(
            entry_id=f"est-{int(time.time()*1000)}",
            timestamp=time.time(),
            entry_type=LedgerEntryType.COST,
            subsystem=subsystem,
            activity=activity,
            amount_usd=-abs(estimated_cost_usd),
            description=f"[ESTIMATE] {description}",
            confirmed=False,
        )
        self.ledger.append(entry)
        self._persist()
        return entry

    def allocate_to_reserve(self, reserve_name: str, amount_usd: float) -> bool:
        """Move funds from balance to a named reserve."""
        if amount_usd > self.balance_usd:
            return False
        self.reserves_usd[reserve_name] = self.reserves_usd.get(reserve_name, 0.0) + amount_usd
        self.balance_usd -= amount_usd
        self.ledger.append(LedgerEntry(
            entry_id=f"alloc-{int(time.time()*1000)}",
            timestamp=time.time(),
            entry_type=LedgerEntryType.RESERVE,
            subsystem="treasury",
            activity="reserve_allocation",
            amount_usd=-amount_usd,
            description=f"Allocated ${amount_usd:.2f} to {reserve_name} reserve",
        ))
        self._persist()
        return True

    def get_pnl(self, subsystem: str = None, days: int = 7) -> dict:
        """Calculate profit/loss for a subsystem or overall."""
        cutoff = time.time() - (days * 86400)
        entries = [e for e in self.ledger if e.timestamp > cutoff and e.confirmed]
        if subsystem:
            entries = [e for e in entries if e.subsystem == subsystem]

        revenue = sum(e.amount_usd for e in entries if e.amount_usd > 0)
        costs = sum(abs(e.amount_usd) for e in entries if e.amount_usd < 0)
        profit = revenue - costs

        return {
            "period_days": days,
            "subsystem": subsystem or "all",
            "revenue_usd": round(revenue, 4),
            "costs_usd": round(costs, 4),
            "profit_usd": round(profit, 4),
            "roi_percent": round((profit / costs * 100), 2) if costs > 0 else 0.0,
            "entries_count": len(entries),
        }

    def get_subsystem_breakdown(self, days: int = 7) -> Dict[str, dict]:
        """Get P&L breakdown by subsystem."""
        subsystems = set(e.subsystem for e in self.ledger if e.confirmed)
        return {sub: self.get_pnl(sub, days) for sub in subsystems}

    def get_runway_days(self) -> Optional[float]:
        """How many days until balance reaches zero at current burn rate."""
        daily_burn = self._calculate_daily_burn()
        if daily_burn <= 0:
            return float("inf")
        return self.balance_usd / daily_burn

    def get_budget_for(self, subsystem: str, activity_type: str = None) -> float:
        """Get recommended budget allocation for a subsystem based on historical ROI."""
        pnl = self.get_pnl(subsystem, days=30)
        if pnl["profit_usd"] > 0:
            # Profitable subsystem gets more budget
            return min(pnl["profit_usd"] * 0.5, self.balance_usd * 0.3)
        elif pnl["costs_usd"] > 0:
            # Unprofitable subsystem gets minimal budget
            return min(10.0, self.balance_usd * 0.05)
        return min(25.0, self.balance_usd * 0.1)

    def _calculate_daily_burn(self) -> float:
        """Calculate average daily cost over last 7 days."""
        cutoff = time.time() - (7 * 86400)
        recent_costs = [abs(e.amount_usd) for e in self.ledger
                        if e.timestamp > cutoff and e.amount_usd < 0 and e.confirmed]
        if not recent_costs:
            return 0.0
        return sum(recent_costs) / 7.0

    def _update_daily_stats(self, entry: LedgerEntry):
        """Update daily aggregation stats."""
        day_key = time.strftime("%Y-%m-%d", time.localtime(entry.timestamp))
        if day_key not in self.daily_stats:
            self.daily_stats[day_key] = {"revenue": 0.0, "costs": 0.0, "entries": 0}
        self.daily_stats[day_key]["entries"] += 1
        if entry.amount_usd > 0:
            self.daily_stats[day_key]["revenue"] += entry.amount_usd
        else:
            self.daily_stats[day_key]["costs"] += abs(entry.amount_usd)

    def get_status(self) -> dict:
        return {
            "balance_usd": round(self.balance_usd, 4),
            "reserves_usd": {k: round(v, 4) for k, v in self.reserves_usd.items()},
            "runway_days": round(self.get_runway_days(), 2) if self.get_runway_days() != float("inf") else "inf",
            "daily_burn_7d": round(self._calculate_daily_burn(), 4),
            "total_entries": len(self.ledger),
            "confirmed_entries": len([e for e in self.ledger if e.confirmed]),
            "pnl_7d": self.get_pnl(days=7),
            "pnl_30d": self.get_pnl(days=30),
        }

    def _persist(self):
        try:
            data = {
                "balance_usd": self.balance_usd,
                "reserves_usd": self.reserves_usd,
                "daily_stats": self.daily_stats,
                "ledger": [
                    {
                        "entry_id": e.entry_id,
                        "timestamp": e.timestamp,
                        "entry_type": e.entry_type.value,
                        "subsystem": e.subsystem,
                        "activity": e.activity,
                        "amount_usd": e.amount_usd,
                        "description": e.description,
                        "metadata": e.metadata,
                        "confirmed": e.confirmed,
                    }
                    for e in self.ledger
                ],
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass

    def _load(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            self.balance_usd = data.get("balance_usd", 0.0)
            self.reserves_usd = data.get("reserves_usd", {})
            self.daily_stats = data.get("daily_stats", {})
            # Ledger is append-only; we don't reload it to avoid duplication
        except Exception:
            pass
