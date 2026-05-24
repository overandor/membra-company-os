#include "oms.hpp"
#include "config.hpp"
#include "rest_client.hpp"
#include "risk.hpp"
#include "auth.hpp"
#include "logger.hpp"
#include <iostream>
#include <thread>

namespace depthos {

// ContractOrders implementation
double ContractOrders::bid_age() const {
    if (bid_order_id == 0) return 0.0;
    return epoch_s() - bid_placed_ts;
}

double ContractOrders::ask_age() const {
    if (ask_order_id == 0) return 0.0;
    return epoch_s() - ask_placed_ts;
}

bool ContractOrders::bid_ttl_expired(double ttl) const {
    return bid_order_id != 0 && bid_age() > ttl;
}

bool ContractOrders::ask_ttl_expired(double ttl) const {
    return ask_order_id != 0 && ask_age() > ttl;
}

// OMS implementation
OMS::OMS() {
}

OMS oms;

ContractOrders& OMS::get_or_create(const std::string& contract) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (state_.find(contract) == state_.end()) {
        state_[contract] = ContractOrders();
        state_[contract].contract = contract;
    }
    return state_[contract];
}

void OMS::quote(
    RestClient& client,
    const std::string& contract,
    const Decimal& bid_price,
    const Decimal& ask_price,
    int bid_size,
    int ask_size
) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    ContractOrders& s = get_or_create(contract);
    
    auto it_spec = mm_config.contracts.find(contract);
    if (it_spec == mm_config.contracts.end()) {
        LOG_ERROR("quote: unknown contract {}", contract);
        return;
    }
    
    const Decimal& tick = it_spec->second.tick_size;
    
    // BID side
    if (bid_price > Decimal("0") && bid_size > 0) {
        refresh_side(client, s, contract, "bid", bid_price, bid_size, tick, bid_size);
    } else if (s.bid_order_id != 0 && !s.bid_cancelling) {
        cancel_side(client, s, contract, "bid");
    }
    
    // ASK side
    if (ask_price > Decimal("0") && ask_size > 0) {
        refresh_side(client, s, contract, "ask", ask_price, ask_size, tick, -ask_size);
    } else if (s.ask_order_id != 0 && !s.ask_cancelling) {
        cancel_side(client, s, contract, "ask");
    }
}

void OMS::refresh_side(
    RestClient& client,
    ContractOrders& s,
    const std::string& contract,
    const std::string& side,
    const Decimal& target_price,
    int target_size,
    const Decimal& tick,
    int positive_size
) {
    int live_id = (side == "bid") ? s.bid_order_id : s.ask_order_id;
    Decimal live_price = (side == "bid") ? s.bid_price : s.ask_price;
    
    if (live_id != 0 && live_price > Decimal("0")) {
        // Calculate ticks moved
        Decimal ticks_moved = abs(target_price - live_price) / tick;
        bool ttl_expired = (side == "bid") ? s.bid_ttl_expired(mm_config.order_ttl_s) 
                                          : s.ask_ttl_expired(mm_config.order_ttl_s);
        
        bool needs_reprice = (ticks_moved >= Decimal(mm_config.reprice_tick_threshold) || ttl_expired);
        
        if (!needs_reprice) {
            return;  // Order is still good
        }
        
        // Cancel existing
        cancel_side(client, s, contract, side);
    }
    
    // Place new order
    std::string order_id = client.place_order(
        contract, positive_size, target_price, "poc", false, "t-mm"
    );
    
    if (!order_id.empty() && order_id != "-1") {
        int id = std::stoi(order_id);
        double now = epoch_s();
        
        if (side == "bid") {
            s.bid_order_id = id;
            s.bid_price = target_price;
            s.bid_size = target_size;
            s.bid_placed_ts = now;
        } else {
            s.ask_order_id = id;
            s.ask_price = target_price;
            s.ask_size = target_size;
            s.ask_placed_ts = now;
        }
        
        LOG_INFO("Placed {} order contract={} id={} price={} size={}", side, contract, id, target_price.str(), positive_size);
    } else {
        LOG_ERROR("place_order returned no valid id");
    }
}

void OMS::cancel_side(
    RestClient& client,
    ContractOrders& s,
    const std::string& contract,
    const std::string& side
) {
    int order_id = (side == "bid") ? s.bid_order_id : s.ask_order_id;
    if (order_id == 0) return;
    
    if (side == "bid") {
        s.bid_cancelling = true;
    } else {
        s.ask_cancelling = true;
    }
    
    bool ok = client.cancel_order(order_id, contract);
    
    // Always clear state regardless of result
    if (side == "bid") {
        s.bid_order_id = 0;
        s.bid_price = Decimal("0");
        s.bid_size = 0;
        s.bid_cancelling = false;
    } else {
        s.ask_order_id = 0;
        s.ask_price = Decimal("0");
        s.ask_size = 0;
        s.ask_cancelling = false;
    }
    
    LOG_INFO("Cleared {} order id={} for {}", side, order_id, contract);
}

void OMS::on_order_update(const std::unordered_map<std::string, std::string>& event) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::string contract = event.at("contract");
    int order_id = std::stoi(event.at("id"));
    std::string status = event.at("status");
    int left = std::stoi(event.at("left"));
    int size = std::stoi(event.at("size"));
    std::string fill_price_str = event.count("fill_price") ? event.at("fill_price") : "";
    Decimal fill_price = fill_price_str.empty() ? Decimal("0") : Decimal(fill_price_str);
    
    auto it = state_.find(contract);
    if (it == state_.end()) return;
    
    ContractOrders& s = it->second;
    
    if (status == "finished") {
        // Determine which side filled
        if (s.bid_order_id == order_id) {
            int filled_size = s.bid_size - left;
            if (filled_size > 0 && fill_price > Decimal("0")) {
                std::string fee_str = event.count("fee") ? event.at("fee") : "0";
                Decimal fee = fee_str.empty() ? Decimal("0") : Decimal(fee_str);
                record_fill(contract, filled_size, fill_price, fee);
            }
            s.bid_order_id = 0;
            s.bid_price = Decimal("0");
            s.bid_size = 0;
            s.bid_placed_ts = 0.0;
        } else if (s.ask_order_id == order_id) {
            int filled_size = s.ask_size - left;
            if (filled_size > 0 && fill_price > Decimal("0")) {
                std::string fee_str = event.count("fee") ? event.at("fee") : "0";
                Decimal fee = fee_str.empty() ? Decimal("0") : Decimal(fee_str);
                record_fill(contract, -filled_size, fill_price, fee);
            }
            s.ask_order_id = 0;
            s.ask_price = Decimal("0");
            s.ask_size = 0;
            s.ask_placed_ts = 0.0;
        }
    }
}

void OMS::record_fill(
    const std::string& contract,
    int size,
    const Decimal& price,
    const Decimal& fee
) {
    Fill fill;
    fill.contract = contract;
    fill.size = size;
    fill.price = price;
    fill.fee = fee;
    fill.ts_ms = epoch_ms();
    
    risk.on_fill(fill);
    
    LOG_INFO("Fill: {} size={} price={} fee={} net_pos={}", contract, size, price.str(), fee.str(), risk.net_position(contract));
}

void OMS::cancel_all(RestClient& client) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    for (auto& [contract, s] : state_) {
        if (s.bid_order_id || s.ask_order_id) {
            int n = client.cancel_all_orders(contract);
            LOG_INFO("Emergency cancel: {} -> {} orders killed", contract, n);
            s.bid_order_id = 0;
            s.ask_order_id = 0;
            s.bid_price = Decimal("0");
            s.ask_price = Decimal("0");
        }
    }
}

int OMS::live_order_count() const {
    std::lock_guard<std::mutex> lock(mutex_);
    int count = 0;
    for (const auto& [contract, s] : state_) {
        if (s.bid_order_id) count++;
        if (s.ask_order_id) count++;
    }
    return count;
}

} // namespace depthos
