"""
Simple Python Performance Benchmark
"""

import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("PYTHON PERFORMANCE BENCHMARK")
print("=" * 60)

# Test 1: OrderBook snapshot creation
print("\n[1/3] Benchmarking OrderBook snapshot creation...")
try:
    from app.backtest.l2_replay import L2Snapshot
    
    iterations = 10000
    start = time.time()
    
    for i in range(iterations):
        snapshot = L2Snapshot(
            timestamp_ms=1234567890 + i,
            exchange_ts_ms=1234567890 + i,
            contract="SHIB_USDT",
            bids=[(0.000045 + j * 0.000001, 1000 - j * 100) for j in range(20)],
            asks=[(0.000046 + j * 0.000001, 1000 - j * 100) for j in range(20)],
            message_type="snapshot",
            local_sequence=i
        )
    
    end = time.time()
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    latency_ms = (elapsed / iterations) * 1000
    
    print(f"✅ OrderBook snapshot creation")
    print(f"   Time: {elapsed:.4f}s for {iterations} iterations")
    print(f"   Ops/sec: {ops_per_sec:,.0f}")
    print(f"   Latency: {latency_ms:.4f}ms")
    
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 2: JSON parsing
print("\n[2/3] Benchmarking JSON parsing...")
try:
    import json
    
    sample_data = {
        "contract": "SHIB_USDT",
        "bids": [[0.000045 + i * 0.000001, 1000 - i * 100] for i in range(20)],
        "asks": [[0.000046 + i * 0.000001, 1000 - i * 100] for i in range(20)],
        "timestamp": 1234567890
    }
    
    json_str = json.dumps(sample_data)
    
    iterations = 10000
    start = time.time()
    
    for _ in range(iterations):
        data = json.loads(json_str)
    
    end = time.time()
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    latency_ms = (elapsed / iterations) * 1000
    
    print(f"✅ JSON parsing")
    print(f"   Time: {elapsed:.4f}s for {iterations} iterations")
    print(f"   Ops/sec: {ops_per_sec:,.0f}")
    print(f"   Latency: {latency_ms:.4f}ms")
    
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 3: Dictionary operations
print("\n[3/3] Benchmarking Dictionary operations...")
try:
    iterations = 10000
    start = time.time()
    
    for i in range(iterations):
        data = {
            "contract": f"SHIB_USDT_{i}",
            "price": 0.000045 + i * 0.000001,
            "size": 1000 + i,
            "timestamp": 1234567890 + i
        }
        _ = data["contract"]
        _ = data["price"]
        _ = data["size"]
    
    end = time.time()
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    latency_ms = (elapsed / iterations) * 1000
    
    print(f"✅ Dictionary operations")
    print(f"   Time: {elapsed:.4f}s for {iterations} iterations")
    print(f"   Ops/sec: {ops_per_sec:,.0f}")
    print(f"   Latency: {latency_ms:.4f}ms")
    
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "=" * 60)
print("BENCHMARK COMPLETE")
print("=" * 60)
print("\nPython performance is excellent for most operations.")
print("C++ would provide benefit for:")
print("  - WebSocket message processing (high frequency)")
print("  - Order placement (latency sensitive)")
print("  - Risk checks (deterministic timing)")
