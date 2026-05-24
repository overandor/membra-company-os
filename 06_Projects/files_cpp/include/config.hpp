#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <boost/multiprecision/cpp_dec_float.hpp>
#include <chrono>
#include <functional>
#include <sstream>

namespace depthos {

// Use high-precision decimal type (50 decimal places)
using Decimal = boost::multiprecision::number<boost::multiprecision::backends::cpp_dec_float<50>>;

// Network configuration
constexpr const char* FUTURES_REST_URL = "https://fx-api.gateio.ws/api/v4";
constexpr const char* FUTURES_WS_URL = "wss://fx-ws.gateio.ws/v4/ws/usdt";
constexpr const char* SETTLE = "usdt";

// Micro-price contracts to trade
inline std::vector<std::string> MICRO_CONTRACTS = {
    "SHIB_USDT",
    "PEPE_USDT",
    "FLOKI_USDT",
    "BONK_USDT",
    "1000RATS_USDT",
    "XEC_USDT"
};

// Contract specification
struct ContractSpec {
    std::string name;
    Decimal tick_size;              // minimum price increment
    int lot_size;                  // minimum order size in contracts
    Decimal quanto_multiplier;     // value per contract in USDT
    Decimal max_price = Decimal("0.10");  // hard ceiling - micro only
};

// Market maker configuration
struct MMConfig {
    // Quoting
    int order_size = 1;                    // contracts per side
    int reprice_tick_threshold = 1;       // ticks moved before reprice
    
    // Inventory / risk
    int max_inventory_contracts = 50;     // hard position limit
    int skew_threshold_contracts = 20;    // begin reducing size at this threshold
    
    // Daily loss halt
    Decimal daily_loss_limit_usdt = Decimal("5.00");
    
    // Timing
    double heartbeat_interval_s = 30.0;
    double order_ttl_s = 10.0;            // cancel and re-post after this age
    double reconnect_delay_s = 2.0;
    int max_reconnect_attempts = 10;
    
    // Account mode
    std::string account_mode = "single";   // "single" or "dual"
    
    // Misc
    bool dry_run = true;
    
    // Contract specs populated at runtime
    std::unordered_map<std::string, ContractSpec> contracts;
};

// Global configuration instance
extern MMConfig mm_config;

// API credentials (loaded from environment)
extern std::string API_KEY;
extern std::string API_SECRET;

// Load environment variables
void load_environment();

} // namespace depthos

namespace std {
    template<>
    struct hash<depthos::Decimal> {
        size_t operator()(const depthos::Decimal& d) const noexcept {
            return hash<std::string>{}(d.str());
        }
    };
}
