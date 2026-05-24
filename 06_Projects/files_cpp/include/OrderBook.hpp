#pragma once

#include <vector>
#include <unordered_map>
#include <cstdint>
#include <string>

namespace depthos {

struct OrderBookLevel {
    double price;
    int64_t size;
    
    OrderBookLevel() : price(0.0), size(0) {}
    OrderBookLevel(double p, int64_t s) : price(p), size(s) {}
};

struct OrderBook {
    std::vector<OrderBookLevel> bids;
    std::vector<OrderBookLevel> asks;
    uint64_t sequence;
    int64_t timestamp_ms;
    std::string contract;
    
    OrderBook() : sequence(0), timestamp_ms(0) {}
    
    double mid_price() const {
        if (bids.empty() || asks.empty()) return 0.0;
        return (bids[0].price + asks[0].price) / 2.0;
    }
    
    double spread() const {
        if (bids.empty() || asks.empty()) return 0.0;
        return asks[0].price - bids[0].price;
    }
    
    double spread_bps() const {
        double mid = mid_price();
        if (mid == 0.0) return 0.0;
        return (spread() / mid) * 10000.0;
    }
};

class OrderBookManager {
public:
    OrderBookManager();
    ~OrderBookManager();
    
    // Update orderbook from exchange message
    void update_from_snapshot(const std::string& contract,
                             const std::vector<OrderBookLevel>& bids,
                             const std::vector<OrderBookLevel>& asks,
                             uint64_t sequence,
                             int64_t timestamp_ms);
    
    void apply_delta(const std::string& contract,
                     const std::vector<OrderBookLevel>& bid_changes,
                     const std::vector<OrderBookLevel>& ask_changes,
                     uint64_t sequence,
                     int64_t timestamp_ms);
    
    // Get current orderbook
    const OrderBook* get_orderbook(const std::string& contract) const;
    
    // Check for sequence gaps
    bool has_gap(const std::string& contract, uint64_t expected_seq) const;
    
    // Clear orderbook (for resync)
    void clear(const std::string& contract);
    
private:
    std::unordered_map<std::string, OrderBook> orderbooks_;
    std::unordered_map<std::string, uint64_t> last_sequences_;
};

} // namespace depthos
