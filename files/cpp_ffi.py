"""
Python FFI Bindings for C++ Core

Provides Python interface to C++ trading components:
- Order placement
- Queue model
- Risk engine
- Book reconciliation
"""

import ctypes
import os
from pathlib import Path

# Load the C++ library
lib_path = Path(__file__).parent.parent / "files_cpp" / "build" / "libdepthos_core.dylib"

if not lib_path.exists():
    lib_path = Path(__file__).parent.parent / "files_cpp" / "build" / "libdepthos_core.so"

if not lib_path.exists():
    raise FileNotFoundError(f"C++ library not found at {lib_path}")

lib = ctypes.CDLL(str(lib_path))


# Order Placement
class OrderPlacement(ctypes.Structure):
    _fields_ = [
        ("contract", ctypes.c_char_p),
        ("size", ctypes.c_int64),
        ("price", ctypes.c_double),
        ("tif", ctypes.c_int),  # 0=GTC, 1=IOC, 2=POC
        ("reduce_only", ctypes.c_bool),
        ("text", ctypes.c_char_p),
    ]


class OrderResponse(ctypes.Structure):
    _fields_ = [
        ("order_id", ctypes.c_int64),
        ("status", ctypes.c_char_p),
        ("error", ctypes.c_char_p),
        ("success", ctypes.c_bool),
    ]


# Queue Model
class FillProbabilityFactors(ctypes.Structure):
    _fields_ = [
        ("queue_ahead", ctypes.c_int),
        ("queue_behind", ctypes.c_int),
        ("trade_intensity", ctypes.c_double),
        ("cancel_rate", ctypes.c_double),
        ("toxicity_score", ctypes.c_double),
        ("latency_ms", ctypes.c_double),
    ]


# Risk Engine
class PositionLimits(ctypes.Structure):
    _fields_ = [
        ("max_position", ctypes.c_int64),
        ("max_order_size", ctypes.c_int64),
        ("max_exposure_usdt", ctypes.c_double),
    ]


class PositionState(ctypes.Structure):
    _fields_ = [
        ("current_position", ctypes.c_int64),
        ("current_exposure_usdt", ctypes.c_double),
        ("unrealized_pnl_usdt", ctypes.c_double),
    ]


# Define C functions
lib.place_order.argtypes = [
    ctypes.c_char_p,  # contract
    ctypes.c_int64,    # size
    ctypes.c_double,   # price
    ctypes.c_int,      # tif
    ctypes.c_bool,     # reduce_only
    ctypes.c_char_p,   # text
]
lib.place_order.restype = OrderResponse

lib.cancel_order.argtypes = [ctypes.c_int64, ctypes.c_char_p]  # order_id, contract
lib.cancel_order.restype = ctypes.c_bool

lib.calculate_fill_probability.argtypes = [ctypes.POINTER(FillProbabilityFactors)]
lib.calculate_fill_probability.restype = ctypes.c_double

lib.check_order_risk.argtypes = [
    ctypes.c_char_p,  # contract
    ctypes.c_int64,    # size
    ctypes.c_double,   # price
]
lib.check_order_risk.restype = ctypes.c_int  # 0=Pass, 1=Fail


class CppOrderPlacement:
    """Python wrapper for C++ OrderPlacement."""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Initialize C++ OrderPlacement
        lib.init_order_placement(api_key.encode(), api_secret.encode())
    
    def place_order(
        self,
        contract: str,
        size: int,
        price: float,
        tif: str = "poc",
        reduce_only: bool = False,
        text: str = "python_ffi",
    ) -> dict:
        """Place an order via C++."""
        tif_map = {"gtc": 0, "ioc": 1, "poc": 2}
        tif_int = tif_map.get(tif.lower(), 2)
        
        response = lib.place_order(
            contract.encode(),
            size,
            price,
            tif_int,
            reduce_only,
            text.encode(),
        )
        
        return {
            "order_id": response.order_id,
            "status": response.status.decode(),
            "error": response.error.decode(),
            "success": response.success,
        }
    
    def cancel_order(self, order_id: int, contract: str) -> bool:
        """Cancel an order via C++."""
        return lib.cancel_order(order_id, contract.encode())


class CppQueueModel:
    """Python wrapper for C++ QueueModel."""
    
    def calculate_fill_probability(
        self,
        queue_ahead: int,
        queue_behind: int,
        trade_intensity: float,
        cancel_rate: float,
        toxicity_score: float,
        latency_ms: float,
    ) -> float:
        """Calculate fill probability via C++."""
        factors = FillProbabilityFactors(
            queue_ahead=queue_ahead,
            queue_behind=queue_behind,
            trade_intensity=trade_intensity,
            cancel_rate=cancel_rate,
            toxicity_score=toxicity_score,
            latency_ms=latency_ms,
        )
        
        return lib.calculate_fill_probability(factors)


class CppRiskEngine:
    """Python wrapper for C++ RiskEngine."""
    
    def __init__(self):
        # Initialize C++ RiskEngine
        lib.init_risk_engine()
    
    def set_position_limits(
        self,
        contract: str,
        max_position: int,
        max_order_size: int,
        max_exposure_usdt: float,
    ):
        """Set position limits via C++."""
        limits = PositionLimits(
            max_position=max_position,
            max_order_size=max_order_size,
            max_exposure_usdt=max_exposure_usdt,
        )
        
        lib.set_position_limits(contract.encode(), limits)
    
    def check_order(self, contract: str, size: int, price: float) -> bool:
        """Check if order is allowed via C++."""
        result = lib.check_order_risk(contract.encode(), size, price)
        return result == 0  # 0 = Pass
    
    def set_kill_switch(self, enabled: bool):
        """Enable/disable kill switch via C++."""
        lib.set_kill_switch(enabled)
    
    def get_total_exposure(self) -> float:
        """Get total exposure via C++."""
        return lib.get_total_exposure()


# Convenience functions
def place_order_cpp(
    contract: str,
    size: int,
    price: float,
    api_key: str,
    api_secret: str,
    tif: str = "poc",
) -> dict:
    """Convenience function to place order via C++."""
    placement = CppOrderPlacement(api_key, api_secret)
    return placement.place_order(contract, size, price, tif)


def calculate_fill_probability_cpp(
    queue_ahead: int,
    queue_behind: int,
    trade_intensity: float,
    cancel_rate: float,
    toxicity_score: float,
    latency_ms: float,
) -> float:
    """Convenience function to calculate fill probability via C++."""
    model = CppQueueModel()
    return model.calculate_fill_probability(
        queue_ahead,
        queue_behind,
        trade_intensity,
        cancel_rate,
        toxicity_score,
        latency_ms,
    )


def check_order_risk_cpp(
    contract: str,
    size: int,
    price: float,
    max_position: int,
    max_exposure: float,
) -> bool:
    """Convenience function to check order risk via C++."""
    risk = CppRiskEngine()
    risk.set_position_limits(contract, max_position, 1000, max_exposure)
    return risk.check_order(contract, size, price)
