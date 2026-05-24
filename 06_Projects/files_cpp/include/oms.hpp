#pragma once

#include <string>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <cstdint>
#include <chrono>
#include "config.hpp"

namespace depthos {

// Forward declarations
class RestClient;
struct Fill;

// Per-contract order state
struct ContractOrders {
    std::string contract;
    
    int bid_order_id = 0;
    Decimal bid_price;
    int bid_size = 0;
    double bid_placed_ts = 0.0;
    
    int ask_order_id = 0;
    Decimal ask_price;
    int ask_size = 0;
    double ask_placed_ts = 0.0;
    
    bool bid_cancelling = false;
    bool ask_cancelling = false;
    
    double bid_age() const;
    double ask_age() const;
    bool bid_ttl_expired(double ttl) const;
    bool ask_ttl_expired(double ttl) const;
};

// Order Management System
class OMS {
public:
    OMS();
    
    // Quote placement (idempotent)
    void quote(
        RestClient& client,
        const std::string& contract,
        const Decimal& bid_price,
        const Decimal& ask_price,
        int bid_size,
        int ask_size
    );
    
    // WS fill reconciliation
    void on_order_update(const std::unordered_map<std::string, std::string>& event);
    
    // Cleanup
    void cancel_all(RestClient& client);
    int live_order_count() const;
    
private:
    std::unordered_map<std::string, ContractOrders> state_;
    mutable std::mutex mutex_;
    
    ContractOrders& get_or_create(const std::string& contract);
    void refresh_side(
        RestClient& client,
        ContractOrders& s,
        const std::string& contract,
        const std::string& side,
        const Decimal& target_price,
        int target_size,
        const Decimal& tick,
        int positive_size
    );
    void cancel_side(
        RestClient& client,
        ContractOrders& s,
        const std::string& contract,
        const std::string& side
    );
    void record_fill(
        const std::string& contract,
        int size,
        const Decimal& price,
        const Decimal& fee
    );
};

// Global OMS instance
extern OMS oms;

} // namespace depthos
