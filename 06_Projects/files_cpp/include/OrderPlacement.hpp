#pragma once

#include <string>
#include <cstdint>
#include <memory>

namespace depthos {

enum class TimeInForce {
    GTC,  // Good Till Cancelled
    IOC,  // Immediate Or Cancel
    POC   // Post-Only Cancel (maker-only)
};

struct Order {
    std::string contract;
    int64_t size;  // positive = buy, negative = sell
    double price;
    TimeInForce tif;
    bool reduce_only;
    std::string text;  // Order text/label
    
    Order() : size(0), price(0.0), tif(TimeInForce::GTC), reduce_only(false) {}
};

struct OrderResponse {
    int64_t order_id;
    std::string status;
    std::string error;
    bool success;
    
    OrderResponse() : order_id(0), success(false) {}
};

class OrderPlacement {
public:
    OrderPlacement(const std::string& api_key, const std::string& api_secret);
    ~OrderPlacement();
    
    // Place a single order
    OrderResponse place_order(const Order& order);
    
    // Cancel an order
    bool cancel_order(int64_t order_id, const std::string& contract);
    
    // Cancel all orders for a contract
    int cancel_all_orders(const std::string& contract);
    
    // Query order status
    OrderResponse query_order(int64_t order_id, const std::string& contract);
    
private:
    std::string api_key_;
    std::string api_secret_;
    
    // Generate signature for REST API
    std::string generate_signature(const std::string& method,
                                   const std::string& path,
                                   const std::string& body,
                                   int64_t timestamp);
    
    // Make HTTP request to Gate.io
    std::string make_request(const std::string& method,
                            const std::string& path,
                            const std::string& body = "");
    
    // Round price to tick size
    double round_to_tick(double price, double tick_size);
};

} // namespace depthos
