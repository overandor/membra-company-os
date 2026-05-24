#!/usr/bin/env python3
"""
Compute Marketplace for Mac Compute Node
Allows users to rent out their Mac's CPU, RAM, and GPU for token rewards.
"""
import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import psutil


@dataclass
class ComputeOffer:
    node_id: str
    cpu_cores: int
    memory_gb: float
    gpu_available: bool
    price_per_hour: float
    region: str = "local"
    reputation: float = 5.0
    active: bool = True


class ComputeMarket:
    """Manages compute supply/demand and pricing."""

    def __init__(self, config: Dict):
        self.config = config
        self.pricing = config.get("pricing", {})
        self.token_symbol = config.get("token_symbol", "COMPUTE")
        self.offers: Dict[str, ComputeOffer] = {}
        self.demand_queue: List[Dict] = []
        self.earnings_log: List[Dict] = []
        self.state_file = os.path.expanduser("~/.mac_compute_node/market_state.json")
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                state = json.load(f)
                self.earnings_log = state.get("earnings", [])

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump({"earnings": self.earnings_log}, f)

    def register_node(self, node_id: str, resources: Dict) -> ComputeOffer:
        """Register this Mac as a compute provider."""
        price = self._calculate_price(resources)
        offer = ComputeOffer(
            node_id=node_id,
            cpu_cores=resources.get("cpu_cores", 1),
            memory_gb=resources.get("memory_total_gb", 8),
            gpu_available=resources.get("gpu_available", False),
            price_per_hour=price,
            region=resources.get("region", "local"),
        )
        self.offers[node_id] = offer
        return offer

    def _calculate_price(self, resources: Dict) -> float:
        """Calculate hourly price based on resources."""
        cpu_price = resources.get("cpu_cores", 1) * self.pricing.get("cpu_per_core", 0.05)
        mem_price = resources.get("memory_total_gb", 8) * self.pricing.get("memory_per_gb", 0.02)
        gpu_price = 2.0 if resources.get("gpu_available") else 0.0
        return round(cpu_price + mem_price + gpu_price, 4)

    def request_compute(self, task: Dict, max_price: float = None) -> Optional[str]:
        """Find cheapest suitable node for a task."""
        candidates = [
            o for o in self.offers.values()
            if o.active and (max_price is None or o.price_per_hour <= max_price)
        ]
        if not candidates:
            return None
        best = min(candidates, key=lambda x: x.price_per_hour)
        return best.node_id

    def record_earning(self, node_id: str, task_type: str, amount: float, duration_sec: float):
        """Record an earning event."""
        entry = {
            "node_id": node_id,
            "task_type": task_type,
            "amount": amount,
            "duration_sec": duration_sec,
            "timestamp": time.time(),
        }
        self.earnings_log.append(entry)
        self._save_state()

    def get_node_earnings(self, node_id: str) -> Dict:
        """Get total earnings for a node."""
        node_earnings = [e for e in self.earnings_log if e["node_id"] == node_id]
        total = sum(e["amount"] for e in node_earnings)
        by_task = {}
        for e in node_earnings:
            by_task[e["task_type"]] = by_task.get(e["task_type"], 0) + e["amount"]
        return {
            "total": round(total, 6),
            "currency": self.token_symbol,
            "tasks_count": len(node_earnings),
            "by_task_type": by_task,
            "history": node_earnings[-50:],  # Last 50
        }

    def get_market_stats(self) -> Dict:
        """Return marketplace statistics."""
        active = [o for o in self.offers.values() if o.active]
        all_earnings = sum(e["amount"] for e in self.earnings_log)
        return {
            "active_nodes": len(active),
            "total_nodes": len(self.offers),
            "avg_price_per_hour": round(
                sum(o.price_per_hour for o in active) / max(len(active), 1), 4
            ),
            "total_earnings": round(all_earnings, 6),
            "currency": self.token_symbol,
            "demand_queue": len(self.demand_queue),
        }
