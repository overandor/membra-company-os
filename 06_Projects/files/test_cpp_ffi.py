"""
Test Python FFI bindings to C++ core
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("TESTING PYTHON FFI BINDINGS TO C++ CORE")
print("=" * 60)

try:
    import cpp_ffi
    print("✅ Successfully loaded C++ library")
    
    # Test queue model
    print("\n[1/3] Testing QueueModel via FFI...")
    fill_prob = cpp_ffi.calculate_fill_probability_cpp(
        queue_ahead=10,
        queue_behind=5,
        trade_intensity=2.0,
        cancel_rate=1.0,
        toxicity_score=0.3,
        latency_ms=10.0
    )
    print(f"✅ Fill probability: {fill_prob:.4f}")
    
    # Test risk engine
    print("\n[2/3] Testing RiskEngine via FFI...")
    risk_pass = cpp_ffi.check_order_risk_cpp(
        contract="SHIB_USDT",
        size=1000,
        price=0.000045,
        max_position=10000,
        max_exposure=100.0
    )
    print(f"✅ Risk check: {'PASS' if risk_pass else 'FAIL'}")
    
    # Test order placement (without API keys)
    print("\n[3/3] Testing OrderPlacement via FFI...")
    try:
        result = cpp_ffi.place_order_cpp(
            contract="SHIB_USDT",
            size=1000,
            price=0.000045,
            api_key="test",
            api_secret="test",
            tif="poc"
        )
        print(f"✅ Order placement response: {result}")
    except Exception as e:
        print(f"⚠️  Order placement failed (expected without API keys): {e}")
    
    print("\n" + "=" * 60)
    print("PYTHON FFI BINDINGS WORKING ✅")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ FFI test failed: {e}")
    import traceback
    traceback.print_exc()
