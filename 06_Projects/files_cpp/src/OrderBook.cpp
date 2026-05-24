#include "OrderBook.hpp"
#include <algorithm>

namespace depthos {

OrderBookManager::OrderBookManager() {}

OrderBookManager::~OrderBookManager() {}

void OrderBookManager::update_from_snapshot(
    const std::string& contract,
    const std::vector<OrderBookLevel>& bids,
    const std::vector<OrderBookLevel>& asks,
    uint64_t sequence,
    int64_t timestamp_ms)
{
    OrderBook& ob = orderbooks_[contract];
    ob.bids = bids;
    ob.asks = asks;
    ob.sequence = sequence;
    ob.timestamp_ms = timestamp_ms;
    ob.contract = contract;
    
    last_sequences_[contract] = sequence;
}

void OrderBookManager::apply_delta(
    const std::string& contract,
    const std::vector<OrderBookLevel>& bid_changes,
    const std::vector<OrderBookLevel>& ask_changes,
    uint64_t sequence,
    int64_t timestamp_ms)
{
    // Check for gap
    auto it = last_sequences_.find(contract);
    if (it != last_sequences_.end() && sequence > it->second + 1) {
        // Gap detected - should trigger resync
        // For now, just log it
        // TODO: Implement resync logic
    }
    
    OrderBook& ob = orderbooks_[contract];
    
    // Apply bid changes
    for (const auto& change : bid_changes) {
        if (change.size == 0) {
            // Remove level
            ob.bids.erase(
                std::remove_if(ob.bids.begin(), ob.bids.end(),
                    [&change](const OrderBookLevel& level) {
                        return level.price == change.price;
                    }),
                ob.bids.end()
            );
        } else {
            // Update or insert level
            auto it = std::find_if(ob.bids.begin(), ob.bids.end(),
                [&change](const OrderBookLevel& level) {
                    return level.price == change.price;
                });
            
            if (it != ob.bids.end()) {
                it->size = change.size;
                if (it->size == 0) {
                    ob.bids.erase(it);
                }
            } else {
                ob.bids.push_back(change);
            }
        }
    }
    
    // Apply ask changes
    for (const auto& change : ask_changes) {
        if (change.size == 0) {
            // Remove level
            ob.asks.erase(
                std::remove_if(ob.asks.begin(), ob.asks.end(),
                    [&change](const OrderBookLevel& level) {
                        return level.price == change.price;
                    }),
                ob.asks.end()
            );
        } else {
            // Update or insert level
            auto it = std::find_if(ob.asks.begin(), ob.asks.end(),
                [&change](const OrderBookLevel& level) {
                    return level.price == change.price;
                });
            
            if (it != ob.asks.end()) {
                it->size = change.size;
                if (it->size == 0) {
                    ob.asks.erase(it);
                }
            } else {
                ob.asks.push_back(change);
            }
        }
    }
    
    // Sort bids (descending) and asks (ascending)
    std::sort(ob.bids.begin(), ob.bids.end(),
        [](const OrderBookLevel& a, const OrderBookLevel& b) {
            return a.price > b.price;
        });
    
    std::sort(ob.asks.begin(), ob.asks.end(),
        [](const OrderBookLevel& a, const OrderBookLevel& b) {
            return a.price < b.price;
        });
    
    ob.sequence = sequence;
    ob.timestamp_ms = timestamp_ms;
    last_sequences_[contract] = sequence;
}

const OrderBook* OrderBookManager::get_orderbook(const std::string& contract) const {
    auto it = orderbooks_.find(contract);
    if (it != orderbooks_.end()) {
        return &it->second;
    }
    return nullptr;
}

bool OrderBookManager::has_gap(const std::string& contract, uint64_t expected_seq) const {
    auto it = last_sequences_.find(contract);
    if (it == last_sequences_.end()) return false;
    return it->second > expected_seq + 1;
}

void OrderBookManager::clear(const std::string& contract) {
    orderbooks_.erase(contract);
    last_sequences_.erase(contract);
}

} // namespace depthos
