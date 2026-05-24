#include "quoting_engine.hpp"
#include "config.hpp"
#include "rest_client.hpp"
#include "order_book.hpp"
#include "oms.hpp"
#include "risk.hpp"
#include "auth.hpp"
#include "logger.hpp"
#include <iostream>
#include <thread>
#include <chrono>

namespace depthos {

// Static members
std::unordered_map<std::string, std::condition_variable*> QuotingEngine::bbo_events_;
std::unordered_map<std::string, std::mutex> QuotingEngine::bbo_mutexes_;
QuotingEngine* engine = nullptr;

QuotingEngine::QuotingEngine(RestClient& client) 
    : client_(client), running_(false) {
}

QuotingEngine::~QuotingEngine() {
    stop();
}

void QuotingEngine::start() {
    running_ = true;
    
    for (const auto& contract : MICRO_CONTRACTS) {
        if (mm_config.contracts.find(contract) == mm_config.contracts.end()) {
            LOG_WARN("No spec for {} - skipping quoting", contract);
            continue;
        }
        
        // Create event and mutex for this contract
        bbo_events_[contract] = new std::condition_variable();
        bbo_mutexes_[contract];
        
        // Start quote loop thread
        threads_.emplace_back([this, contract]() {
            quote_loop(contract);
        });
    }
    
    LOG_INFO("QuotingEngine started for {} contracts", threads_.size());
}

void QuotingEngine::stop() {
    running_ = false;
    
    // Signal all events to wake up threads
    for (auto& [contract, cv] : bbo_events_) {
        if (cv) {
            cv->notify_all();
        }
    }
    
    // Join all threads
    for (auto& thread : threads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    
    // Cancel all orders
    oms.cancel_all(client_);
    
    LOG_INFO("QuotingEngine stopped - all orders cancelled");
    
    // Clean up events
    for (auto& [contract, cv] : bbo_events_) {
        delete cv;
    }
    bbo_events_.clear();
}

void QuotingEngine::signal_bbo_change(const std::string& contract) {
    auto it = bbo_events_.find(contract);
    if (it != bbo_events_.end() && it->second) {
        it->second->notify_one();
    }
}

void QuotingEngine::quote_loop(const std::string& contract) {
    std::shared_ptr<OrderBook> ob = registry.get_or_create(contract);
    const ContractSpec& spec = mm_config.contracts[contract];
    
    LOG_DEBUG("Quote loop active: {}", contract);
    
    while (running_) {
        // Wait for BBO update or timeout (TTL enforcement)
        std::unique_lock<std::mutex> lock(bbo_mutexes_[contract]);
        
        bool timed_out = !bbo_events_[contract]->wait_for(
            lock,
            std::chrono::duration<double>(mm_config.order_ttl_s),
            [this]() { return !running_; }
        );
        
        lock.unlock();
        
        if (!running_) break;
        
        evaluate_and_quote(contract, spec, *ob);
    }
}

void QuotingEngine::evaluate_and_quote(
    const std::string& contract,
    const ContractSpec& spec,
    OrderBook& ob
) {
    // Guard: global / contract halt
    if (!risk.can_quote(contract, spec)) {
        // Cancel any open orders when halted
        oms.quote(client_, contract, Decimal("0"), Decimal("0"), 0, 0);
        return;
    }
    
    // Guard: stale BBO
    std::shared_ptr<BBO> bbo = ob.bbo();
    if (!bbo || !bbo->valid()) {
        LOG_DEBUG("{}: no valid BBO yet, skipping quote", contract);
        return;
    }
    
    constexpr int64_t BBO_MAX_AGE_MS = 2000;
    if (bbo->age_ms() > BBO_MAX_AGE_MS) {
        LOG_DEBUG("{}: BBO stale ({} ms), suppressing quote", contract, bbo->age_ms());
        oms.quote(client_, contract, Decimal("0"), Decimal("0"), 0, 0);
        return;
    }
    
    // Guard: price ceiling (micro-price only)
    if (bbo->ask_price > spec.max_price) {
        LOG_WARN("{}: ask_price={} exceeds micro ceiling {}, skipping", contract, bbo->ask_price.str(), spec.max_price.str());
        return;
    }
    
    // Guard: minimum spread (>= 1 tick)
    Decimal spread = bbo->spread();
    if (spread < spec.tick_size) {
        LOG_DEBUG("{}: spread={} < tick={} - crossed book, skipping", contract, spread.str(), spec.tick_size.str());
        return;
    }
    
    // Compute sizes with inventory skew
    int base_size = mm_config.order_size;
    int bid_size = risk.allowed_buy_size(contract, base_size);
    int ask_size = risk.allowed_sell_size(contract, base_size);
    
    // Quote prices: join top of book
    Decimal bid_price = (bid_size > 0) ? bbo->bid_price : Decimal("0");
    Decimal ask_price = (ask_size > 0) ? bbo->ask_price : Decimal("0");
    
    LOG_DEBUG("Quote decision {}: BID {}x{} ASK {}x{} spread={} pos={}", contract, bid_size, bid_price.str(), ask_size, ask_price.str(), spread.str(), risk.net_position(contract));
    
    // Submit to OMS
    oms.quote(client_, contract, bid_price, ask_price, bid_size, ask_size);
}

} // namespace depthos
