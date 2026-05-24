"""
Quick system test - verifies core components work
"""

import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("QUICK SYSTEM TEST")
print("=" * 60)

# Test 1: Import core modules
print("\n[1/5] Testing imports...")
try:
    from app.core.config import mm_config, ContractSpec
    from app.connectors.rest_client import place_order
    from app.backtest.l2_replay import L2Snapshot, RecordedTrade
    from app.backtest.queue_model import QueueModel, QueueMetrics
    from app.backtest.edge_decomposition import EdgeDecomposition
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Test ContractSpec
print("\n[2/5] Testing ContractSpec...")
try:
    spec = ContractSpec(
        name="SHIB_USDT",
        tick_size=Decimal("0.000000001"),
        lot_size=1,
        quanto_multiplier=Decimal("1")
    )
    print(f"✅ ContractSpec created: {spec.name}")
    print(f"   tick_size: {spec.tick_size}")
    print(f"   lot_size: {spec.lot_size}")
except Exception as e:
    print(f"❌ ContractSpec test failed: {e}")
    sys.exit(1)

# Test 3: Test QueueModel
print("\n[3/5] Testing QueueModel...")
try:
    model = QueueModel()
    
    from app.backtest.queue_model import FillProbabilityFactors
    factors = FillProbabilityFactors(
        queue_ahead=10,
        queue_behind=5,
        trade_intensity=2.0,
        cancel_rate=1.0,
        toxicity_score=0.3,
        latency_ms=10.0
    )
    
    fill_prob = model.calculate_fill_probability(factors)
    print(f"✅ QueueModel working")
    print(f"   fill_probability: {fill_prob:.4f}")
except Exception as e:
    print(f"❌ QueueModel test failed: {e}")
    sys.exit(1)

# Test 4: Test EdgeDecomposition
print("\n[4/5] Testing EdgeDecomposition...")
try:
    edge = EdgeDecomposition()
    print(f"✅ EdgeDecomposition initialized")
except Exception as e:
    print(f"❌ EdgeDecomposition test failed: {e}")
    sys.exit(1)

# Test 5: Test L2 data structures
print("\n[5/5] Testing L2 data structures...")
try:
    snapshot = L2Snapshot(
        timestamp_ms=1234567890,
        exchange_ts_ms=1234567890,
        contract="SHIB_USDT",
        bids=[(0.000045, 1000), (0.000044, 2000)],
        asks=[(0.000046, 1000), (0.000047, 2000)],
        message_type="snapshot",
        local_sequence=1
    )
    
    print(f"✅ L2Snapshot created: {snapshot.contract}")
    print(f"   bids: {len(snapshot.bids)}")
    print(f"   asks: {len(snapshot.asks)}")
    
    trade = RecordedTrade(
        timestamp_ms=1234567891,
        exchange_ts_ms=1234567891,
        contract="SHIB_USDT",
        side="buy",
        price="0.000045",
        size=1000,
        message_type="trade",
        local_sequence=2
    )
    
    print(f"✅ RecordedTrade created: {trade.contract}")
    print(f"   side: {trade.side}")
    print(f"   size: {trade.size}")
except Exception as e:
    print(f"❌ L2 data structures test failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✅")
print("=" * 60)
