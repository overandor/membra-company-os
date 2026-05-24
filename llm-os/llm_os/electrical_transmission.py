"""Electrical Transmission — Estimate energy cost of compute workloads.

Used by the Treasury to translate compute-hours into electricity cost,
and by the Economic Engine to price inference/training jobs.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TransmissionEstimate:
    """Energy and cost estimate for a compute workload."""
    watts: float
    hours: float
    kwh: float
    cost_usd: float
    rate_usd_per_kwh: float
    source: str = "estimate"


class ElectricalTransmitter:
    """Estimates outgoing energy cost for workloads this node runs."""

    DEFAULT_RATE_USD_PER_KWH = float(os.environ.get("ELECTRICITY_RATE", "0.12"))

    def __init__(self, rate_usd_per_kwh: float = 0.0):
        self.rate = rate_usd_per_kwh or self.DEFAULT_RATE_USD_PER_KWH

    def estimate(self, watts: float, hours: float) -> TransmissionEstimate:
        kwh = (watts * hours) / 1000.0
        return TransmissionEstimate(
            watts=watts, hours=hours, kwh=kwh,
            cost_usd=kwh * self.rate,
            rate_usd_per_kwh=self.rate,
        )

    def estimate_gpu_training(self, gpu_watts: float = 250.0,
                              hours: float = 1.0) -> TransmissionEstimate:
        return self.estimate(gpu_watts, hours)

    def estimate_inference(self, requests: int,
                           ms_per_request: float = 50.0,
                           watts: float = 80.0) -> TransmissionEstimate:
        hours = (requests * ms_per_request) / 3_600_000.0
        return self.estimate(watts, hours)


class ElectricalReceiver:
    """Tracks energy received (e.g. from solar/battery) to offset costs."""

    def __init__(self):
        self.received_kwh: float = 0.0
        self.history: list = []

    def record(self, kwh: float, source: str = "grid") -> None:
        self.received_kwh += kwh
        self.history.append({"kwh": kwh, "source": source, "ts": time.time()})

    @property
    def total_kwh(self) -> float:
        return self.received_kwh


def get_transmission_estimate(watts: float = 80.0, hours: float = 1.0,
                              rate: float = 0.0) -> TransmissionEstimate:
    """Quick helper for callers that just need a number."""
    return ElectricalTransmitter(rate).estimate(watts, hours)
