#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <cstdint>
#include <memory>
#include "config.hpp"

namespace depthos {

// Forward declarations
struct ContractSpec;

// Record of a confirmed trade
struct Fill {
    std::string contract;
    int size;              // positive=long, negative=short
    Decimal price;
    Decimal fee;
    int64_t ts_ms;
    
    Fill() : size(0), ts_ms(0) {}
};

// Per-contract risk state
struct ContractRiskState {
    std::string contract;
    int net_position = 0;           // signed, contracts
    Decimal realized_pnl = Decimal("0");
    Decimal unrealized_pnl = Decimal("0");
    Decimal total_fees = Decimal("0");
    std::vector<Fill> fills;
    
    bool halted = false;
    std::string halt_reason;
    
    void update_fill(const Fill& fill);
    Decimal avg_entry_price() const;
};

// Portfolio-wide risk manager
class RiskManager {
public:
    RiskManager();
    
    // State accessors
    ContractRiskState& state(const std::string& contract);
    int net_position(const std::string& contract);
    
    // Fill ingestion
    void on_fill(const Fill& fill);
    void on_pnl_delta(const std::string& contract, const Decimal& delta);
    
    // Quote eligibility
    bool can_quote(const std::string& contract, const ContractSpec& spec);
    int allowed_buy_size(const std::string& contract, int requested);
    int allowed_sell_size(const std::string& contract, int requested);
    
    // Daily reset
    void reset_daily();
    
    // Status dump
    std::string summary() const;
    
private:
    std::unordered_map<std::string, ContractRiskState> states_;
    Decimal daily_pnl_ = Decimal("0");
    double day_start_ts_ = 0.0;
    bool global_halted_ = false;
    std::string global_reason_;
    
    void check_daily_loss_halt();
};

// Global risk manager
extern RiskManager risk;

} // namespace depthos
