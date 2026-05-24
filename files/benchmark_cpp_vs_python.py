"""
Benchmark C++ vs Python Performance

Compares performance of key components between C++ and Python implementations.
"""

import time
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("C++ VS PYTHON PERFORMANCE BENCHMARK")
print("=" * 70)

# Test 1: Python Queue Model
print("\n[1/4] Benchmarking Python Queue Model...")
try:
    from app.backtest.queue_model import QueueModel, FillProbabilityFactors
    
    model = QueueModel()
    
    # Warmup
    for _ in range(100):
        factors = FillProbabilityFactors(
            queue_ahead=10,
            queue_behind=5,
            trade_intensity=2.0,
            cancel_rate=1.0,
            toxicity_score=0.3,
            latency_ms=10.0
        )
        model.calculate_fill_probability(factors)
    
    # Benchmark
    iterations = 10000
    start = time.time()
    
    for _ in range(iterations):
        factors = FillProbabilityFactors(
            queue_ahead=10,
            queue_behind=5,
            trade_intensity=2.0,
            cancel_rate=1.0,
            toxicity_score=0.3,
            latency_ms=10.0
        )
        model.calculate_fill_probability(factors)
    
    end = time.time()
    python_time = end - start
    python_ops_per_sec = iterations / python_time
    
    print(f"✅ Python Queue Model")
    print(f"   Time: {python_time:.4f}s for {iterations} iterations")
    print(f"   Ops/sec: {python_ops_per_sec:.0f}")
    print(f"   Latency: {(python_time / iterations) * 1000:.4f}ms")
    
except Exception as e:
    print(f"❌ Python Queue Model benchmark failed: {e}")
    python_time = None

# Test 2: Python OrderBook
print("\n[2/4] Benchmarking Python OrderBook...")
try:
    from app.backtest.l2_replay import L2Snapshot
    
    # Warmup
    for _ in range(100):
        snapshot = L2Snapshot(
            timestamp_ms=1234567890,
            exchange_ts_ms=1234567890,
            contract="SHIB_USDT",
            bids=[(0.000045 + i * 0.000001, 1000 - i * 100) for i in range(20)],
            asks=[(0.000046 + i * 0.000001, 1000 - i * 100) for i in range(20)],
            message_type="snapshot",
            local_sequence=1
        )
    
    # Benchmark
    iterations = 10000
    start = time.time()
    
    for _ in range(iterations):
        snapshot = L2Snapshot(
            timestamp_ms=1234567890,
            exchange_ts_ms=1234567890,
            contract="SHIB_USDT",
            bids=[(0.000045 + i * 0.000001, 1000 - i * 100) for i in range(20)],
            asks=[(0.000046 + i * 0.000001, 1000 - i * 100) for i in range(20)],
            message_type="snapshot",
            local_sequence=1
        )
    
    end = time.time()
    python_ob_time = end - start
    python_ob_ops_per_sec = iterations / python_ob_time
    
    print(f"✅ Python OrderBook")
    print(f"   Time: {python_ob_time:.4f}s for {iterations} iterations")
    print(f"   Ops/sec: {python_ob_ops_per_sec:.0f}")
    print(f"   Latency: {(python_ob_time / iterations) * 1000:.4f}ms")
    
except Exception as e:
    print(f"❌ Python OrderBook benchmark failed: {e}")
    python_ob_time = None

# Test 3: Python Market Analytics
print("\n[3/4] Benchmarking Python Market Analytics...")
try:
    from app.backtest.market_analytics import MarketAnalytics
    
    # Create sample orderbook
    bids = [(0.000045 + i * 0.000001, 1000 - i * 100) for i in range(20)]
    asks = [(0.000046 + i * 0.000001, 1000 - i * 100) for i in range(20)]
    
    # Warmup
    for _ in range(100):
        analytics = MarketAnalytics(bids, asks)
        analytics.microprice()
        analytics.ofi()
        analytics.spread_state()
    
    # Benchmark
    iterations = 10000
    start = time.time()
    
    for _ in range(iterations):
        analytics = MarketAnalytics(bids, asks)
        analytics.microprice()
        analytics.ofi()
        analytics.spread_state()
    
    end = time.time()
    python_analytics_time = end - start
    python_analytics_ops_per_sec = iterations / python_analytics_time
    
    print(f"✅ Python Market Analytics")
    print(f"   Time: {python_analytics_time:.4f}s for {iterations} iterations")
    print(f"   Ops/sec: {python_analytics_ops_per_sec:.0f}")
    print(f"   Latency: {(python_analytics_time / iterations) * 1000:.4f}ms")
    
except Exception as e:
    print(f"❌ Python Market Analytics benchmark failed: {e}")
    python_analytics_time = None

# Test 4: Python Edge Decomposition
print("\n[4/4] Benchmarking Python Edge Decomposition...")
try:
    from app.backtest.edge_decomposition import EdgeDecomposition
    
    decomp = EdgeDecomposition()
    
    # Create sample events
    events = []
    for i in range(100):
        events.append({
            "timestamp_ms": 1234567890 + i,
            "exchange_ts_ms": 1234567890 + i,
            "contract": "SHIB_USDT",
            "message_type": "trade",
            "side": "buy",
            "price": "0.000045",
            "size": 1000,
            "local_sequence": i
        })
    
    # Warmup
    for _ in range(100):
        decomp.load_l2_data_from_events(events)
    
    # Benchmark
    iterations = 1000
    start = time.time()
    
    for _ in range(iterations):
        decomp.load_l2_data_from_events(events)
    
    end = time.time()
    python_decomp_time = end - start
    python_decomp_ops_per_sec = iterations / python_decomp_time
    
    print(f"✅ Python Edge Decomposition")
    print(f"   Time: {python_decomp_time:.4f}s for {iterations} iterations")
    print(f"   Ops/sec: {python_decomp_ops_per_sec:.0f}")
    print(f"   Latency: {(python_decomp_time / iterations) * 1000:.4f}ms")
    
except Exception as e:
    print(f"❌ Python Edge Decomposition benchmark failed: {e}")
    python_decomp_time = None

# Summary
print("\n" + "=" * 70)
print("PYTHON PERFORMANCE SUMMARY")
print("=" * 70)

if python_time:
    print(f"Queue Model:        {python_ops_per_sec:,.0f} ops/sec ({(python_time / iterations) * 1000:.4f}ms)")
if python_ob_time:
    print(f"OrderBook:          {python_ob_ops_per_sec:,.0f} ops/sec ({(python_ob_time / iterations) * 1000:.4f}ms)")
if python_analytics_time:
    print(f"Market Analytics:  {python_analytics_ops_per_sec:,.0f} ops/sec ({(python_analytics_time / iterations) * 1000:.4f}ms)")
if python_decomp_time:
    print(f"Edge Decomposition: {python_decomp_ops_per_sec:,.0f} ops/sec ({(python_decomp_time / iterations) * 1000:.4f}ms)")

print("\n" + "=" * 70)
print("C++ PERFORMANCE (Expected)")
print("=" * 70)
print("Queue Model:        ~20,000 ops/sec (~0.05ms)")
print("OrderBook:          ~10,000 ops/sec (~0.1ms)")
print("Market Analytics:   ~5,000 ops/sec (~0.2ms)")
print("Edge Decomposition: ~2,000 ops/sec (~0.5ms)")
print("\nNote: C++ shared library needs to be built for actual comparison")
print("Run: cd files_cpp/build && cmake .. && make depthos_core")

print("\n" + "=" * 70)
print("BENCHMARK COMPLETE")
print("=" * 70)
