"""
Analytics module for DepthOS.

Provides trading-grade metrics for performance analysis.
"""

from .performance import PerformanceAnalyzer
from .llm_accuracy import LLMAccuracyAnalytics

__all__ = [
    'PerformanceAnalyzer',
    'LLMAccuracyAnalytics',
]
