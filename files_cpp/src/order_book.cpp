#include "order_book.hpp"
#include "auth.hpp"
#include <algorithm>
#include <sstream>
#include <iomanip>

namespace depthos {

// BBO implementation
Decimal BBO::mid() const {
    if (bid_price == Decimal("0") || ask_price == Decimal("0")) return Decimal("0");
    return (bid_price + ask_price) / Decimal("2");
}

Decimal BBO::spread() const {
    if (bid_price == Decimal("0") || ask_price == Decimal("0")) return Decimal("0");
    return ask_price - bid_price;
}

int64_t BBO::age_ms() const {
    return epoch_ms() - ts_ms;
}

bool BBO::valid() const {
    return bid_price > Decimal("0") && ask_price > Decimal("0") && ask_price > bid_price;
}

// OrderBook implementation
OrderBook::OrderBook(const std::string& contract) 
    : contract_(contract), bbo_(std::make_shared<BBO>()) {
}

Decimal OrderBook::best_bid() const {
    return bbo_ ? bbo_->bid_price : Decimal("0");
}

Decimal OrderBook::best_ask() const {
    return bbo_ ? bbo_->ask_price : Decimal("0");
}

bool OrderBook::is_stale() const {
    if (last_update_ms_ == 0) return true;
    return (epoch_ms() - last_update_ms_) > stale_threshold_ms_;
}

std::shared_ptr<BBO> OrderBook::on_book_ticker(const std::unordered_map<std::string, std::string>& data) {
    auto it_bid = data.find("b");
    auto it_bid_size = data.find("B");
    auto it_ask = data.find("a");
    auto it_ask_size = data.find("A");
    
    if (it_bid == data.end() || it_ask == data.end()) {
        return nullptr;
    }
    
    auto new_bbo = std::make_shared<BBO>();
    new_bbo->bid_price = Decimal(it_bid->second);
    new_bbo->bid_size = std::stoi(it_bid_size->second);
    new_bbo->ask_price = Decimal(it_ask->second);
    new_bbo->ask_size = std::stoi(it_ask_size->second);
    new_bbo->ts_ms = epoch_ms();
    
    last_update_ms_ = new_bbo->ts_ms;
    
    bool changed = (!bbo_ || bbo_->bid_price != new_bbo->bid_price || bbo_->ask_price != new_bbo->ask_price);
    
    if (changed) {
        bbo_ = new_bbo;
        return bbo_;
    }
    
    return nullptr;
}

void OrderBook::on_order_book_snapshot(const std::unordered_map<std::string, std::string>& data) {
    bids_.clear();
    asks_.clear();
    
    // Parse bids/asks from JSON (placeholder)
    // In production, use nlohmann/json to parse
    
    last_update_ms_ = epoch_ms();
    sync_bbo_from_l2();
}

void OrderBook::on_order_book_update(const std::unordered_map<std::string, std::string>& data) {
    // Parse and apply incremental updates (placeholder)
    
    last_update_ms_ = epoch_ms();
    sync_bbo_from_l2();
}

void OrderBook::sync_bbo_from_l2() {
    if (bids_.empty() || asks_.empty()) return;
    
    // Find best bid and ask
    Decimal best_bid_price = Decimal("0");
    int best_bid_size = 0;
    for (const auto& [price, size] : bids_) {
        if (price > best_bid_price) {
            best_bid_price = price;
            best_bid_size = size;
        }
    }
    
    Decimal best_ask_price = Decimal("999999");  // Initialize with high value
    int best_ask_size = 0;
    for (const auto& [price, size] : asks_) {
        if (price < best_ask_price) {
            best_ask_price = price;
            best_ask_size = size;
        }
    }
    
    if (best_bid_price > Decimal("0") && best_ask_price < Decimal("999999")) {
        auto new_bbo = std::make_shared<BBO>();
        new_bbo->bid_price = best_bid_price;
        new_bbo->bid_size = best_bid_size;
        new_bbo->ask_price = best_ask_price;
        new_bbo->ask_size = best_ask_size;
        new_bbo->ts_ms = epoch_ms();
        
        if (!bbo_ || bbo_->bid_price != new_bbo->bid_price || bbo_->ask_price != new_bbo->ask_price) {
            bbo_ = new_bbo;
        }
    }
}

std::vector<std::pair<Decimal, int>> OrderBook::bid_depth(int n) const {
    std::vector<std::pair<Decimal, int>> result;
    for (const auto& [price, size] : bids_) {
        result.emplace_back(price, size);
    }
    std::sort(result.begin(), result.end(), 
        [](const auto& a, const auto& b) { return a.first > b.first; });
    if (result.size() > static_cast<size_t>(n)) {
        result.resize(n);
    }
    return result;
}

std::vector<std::pair<Decimal, int>> OrderBook::ask_depth(int n) const {
    std::vector<std::pair<Decimal, int>> result;
    for (const auto& [price, size] : asks_) {
        result.emplace_back(price, size);
    }
    std::sort(result.begin(), result.end());
    if (result.size() > static_cast<size_t>(n)) {
        result.resize(n);
    }
    return result;
}

int OrderBook::cumulative_bid_depth(int levels) const {
    int total = 0;
    auto depth = bid_depth(levels);
    for (const auto& [price, size] : depth) {
        total += size;
    }
    return total;
}

int OrderBook::cumulative_ask_depth(int levels) const {
    int total = 0;
    auto depth = ask_depth(levels);
    for (const auto& [price, size] : depth) {
        total += size;
    }
    return total;
}

// OrderBookRegistry implementation
OrderBookRegistry registry;

std::shared_ptr<OrderBook> OrderBookRegistry::get_or_create(const std::string& contract) {
    if (books_.find(contract) == books_.end()) {
        books_[contract] = std::make_shared<OrderBook>(contract);
    }
    return books_[contract];
}

std::shared_ptr<OrderBook> OrderBookRegistry::operator[](const std::string& contract) {
    return books_[contract];
}

std::vector<std::string> OrderBookRegistry::contracts() const {
    std::vector<std::string> result;
    for (const auto& [contract, book] : books_) {
        result.push_back(contract);
    }
    return result;
}

} // namespace depthos
