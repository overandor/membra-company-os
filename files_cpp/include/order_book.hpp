#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <memory>
#include <cstdint>
#include <chrono>
#include "config.hpp"

namespace depthos {

// Price level in the order book
struct Level {
    Decimal price;
    int size;
    
    Level() : size(0) {}
    Level(const Decimal& p, int s) : price(p), size(s) {}
};

// Best bid/offer
struct BBO {
    Decimal bid_price;
    int bid_size;
    Decimal ask_price;
    int ask_size;
    int64_t ts_ms;
    
    BBO() : bid_size(0), ask_size(0), ts_ms(0) {}
    
    Decimal mid() const;
    Decimal spread() const;
    int64_t age_ms() const;
    bool valid() const;
};

// Per-contract order book
class OrderBook {
public:
    explicit OrderBook(const std::string& contract);
    
    // BBO accessors
    std::shared_ptr<BBO> bbo() const { return bbo_; }
    Decimal best_bid() const;
    Decimal best_ask() const;
    bool is_stale() const;
    
    // Update handlers
    std::shared_ptr<BBO> on_book_ticker(const std::unordered_map<std::string, std::string>& data);
    void on_order_book_snapshot(const std::unordered_map<std::string, std::string>& data);
    void on_order_book_update(const std::unordered_map<std::string, std::string>& data);
    
    // Depth utilities
    std::vector<std::pair<Decimal, int>> bid_depth(int n = 5) const;
    std::vector<std::pair<Decimal, int>> ask_depth(int n = 5) const;
    int cumulative_bid_depth(int levels = 3) const;
    int cumulative_ask_depth(int levels = 3) const;
    
private:
    std::string contract_;
    std::shared_ptr<BBO> bbo_;
    std::unordered_map<Decimal, int> bids_;  // price -> size
    std::unordered_map<Decimal, int> asks_;
    int ob_seq_ = 0;
    int64_t last_update_ms_ = 0;
    int64_t stale_threshold_ms_ = 3000;  // 3 seconds
    
    void sync_bbo_from_l2();
};

// Registry holding one OrderBook per contract
class OrderBookRegistry {
public:
    std::shared_ptr<OrderBook> get_or_create(const std::string& contract);
    std::shared_ptr<OrderBook> operator[](const std::string& contract);
    std::vector<std::string> contracts() const;
    
private:
    std::unordered_map<std::string, std::shared_ptr<OrderBook>> books_;
};

// Global registry
extern OrderBookRegistry registry;

} // namespace depthos
