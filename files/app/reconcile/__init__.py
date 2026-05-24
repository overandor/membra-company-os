"""
Reconciliation daemon for DepthOS.

Continuously compares local state against exchange state and repairs drift.

Critical for production MM systems to prevent state divergence.
"""

from .reconcile import ReconciliationEngine, get_reconciler

__all__ = [
    'ReconciliationEngine',
    'get_reconciler',
]
