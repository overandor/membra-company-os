# C++ Low-Latency Execution Architecture

## Porting Strategy

**Objective:** Port critical execution components from Python to C++ for low-latency trading.

## Components to Port

### Priority 1: Critical Path (Must be in C++)
1. **Order Placement** - Direct exchange interaction
2. **WebSocket Handler** - Real-time data ingestion
3. **Orderbook Manager** - State management
4. **Queue Model** - Fill probability calculation
5. **Risk Engine** - Position and risk limits

### Priority 2: Analytics (Can remain Python initially)
1. **Edge Decomposition** - Post-trade analysis
2. **Toxic Flow Detection** - Can be async
3. **Market Analytics** - Offline processing

## C++ Architecture

```
C++ Core (microsecond latency)
├── Order Management
│   ├── OrderBook.cpp
│   ├── OrderPlacement.cpp
│   ├── WebSocketClient.cpp
│   └── RiskEngine.cpp
├── Queue Model
│   ├── QueuePosition.cpp
│   ├── FillProbability.cpp
│   └── QueueEvolution.cpp
└── Exchange Interface
    ├── GateRestClient.cpp
    ├── GateWebSocket.cpp
    └── Auth.cpp

Python Layer (millisecond latency)
├── Strategy Engine
├── Analytics
├── Backtesting
└── Monitoring
```

## Performance Targets

| Component | Python | C++ | Speedup |
|-----------|--------|-----|---------|
| Order placement | ~50ms | ~1ms | 50x |
| WebSocket processing | ~10ms | ~0.1ms | 100x |
| Queue calculation | ~5ms | ~0.05ms | 100x |
| Risk check | ~2ms | ~0.01ms | 200x |

## Integration Strategy

**Phase 1:** C++ Order Placement Only
- Port order placement to C++
- Python calls C++ via FFI
- All other logic in Python

**Phase 2:** C++ WebSocket + Orderbook
- Port WebSocket handler
- Port orderbook manager
- Real-time processing in C++

**Phase 3:** Full C++ Core
- Port queue model
- Port risk engine
- Python only for strategy

## Dependencies

- **Boost.Asio** - Async I/O
- **Boost.Beast** - WebSocket
- **nlohmann/json** - JSON parsing
- **OpenSSL** - Cryptography for auth
- **libcurl** - HTTP client (optional)

## Build System

```cmake
cmake_minimum_required(VERSION 3.15)
project(DepthOS_CPP)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Boost REQUIRED COMPONENTS system filesystem)
find_package(OpenSSL REQUIRED)
find_package(nlohmann_json 3.2.0 REQUIRED)

add_library(depthos_core
    src/OrderBook.cpp
    src/OrderPlacement.cpp
    src/WebSocketClient.cpp
    src/RiskEngine.cpp
    src/QueueModel.cpp
    src/FillProbability.cpp
    src/GateRestClient.cpp
    src/GateWebSocket.cpp
    src/Auth.cpp
)

target_link_libraries(depthos_core
    PRIVATE
    Boost::system
    Boost::filesystem
    OpenSSL::SSL
    OpenSSL::Crypto
    nlohmann_json::nlohmann_json
)
```

## Python FFI Integration

```python
# Python calls C++
import ctypes

lib = ctypes.CDLL('./libdepthos_core.so')

lib.place_order.argtypes = [
    ctypes.c_char_p,  # contract
    ctypes.c_int,     # size
    ctypes.c_double,   # price
    ctypes.c_char_p,   # tif
]
lib.place_order.restype = ctypes.c_char_p  # JSON response
```

## Data Structures

```cpp
struct Order {
    std::string contract;
    int64_t size;
    double price;
    std::string tif;
    bool reduce_only;
};

struct OrderBookLevel {
    double price;
    int64_t size;
};

struct OrderBook {
    std::vector<OrderBookLevel> bids;
    std::vector<OrderBookLevel> asks;
    uint64_t sequence;
    int64_t timestamp_ms;
};

struct QueuePosition {
    double price;
    int64_t size;
    int rank;
    int64_t volume_ahead;
    int64_t volume_behind;
    int64_t time_in_queue_ms;
};
```

## Next Steps

1. **Create C++ project structure**
2. **Port order placement**
3. **Port WebSocket client**
4. **Port orderbook manager**
5. **Create Python FFI bindings**
6. **Test integration**
7. **Benchmark performance**
