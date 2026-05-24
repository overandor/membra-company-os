#pragma once

#include <string>
#include <unordered_map>
#include <cstdint>
#include <functional>
#include <mutex>
#include <atomic>

namespace depthos {

enum class RiskCheckResult {
    Pass,
    FailPositionLimit,
    FailExposureLimit,
    FailMarginRequirement,
    FailKillSwitch,
    FailUnknown
};

struct PositionLimits {
    int64_t max_position;  // Maximum position size
    int64_t max_order_size; // Maximum single order size
    double max_exposure_usdt; // Maximum exposure in USDT
    
    PositionLimits() : max_position(0), max_order_size(0), max_exposure_usdt(0.0) {}
};

struct PositionState {
    int64_t current_position;
    double current_exposure_usdt;
    double unrealized_pnl_usdt;
    
    PositionState() : current_position(0), current_exposure_usdt(0.0), unrealized_pnl_usdt(0.0) {}
};

using RiskViolationCallback = std::function<void(const std::string& contract, RiskCheckResult result)>;

class RiskEngine {
public:
    RiskEngine();
    ~RiskEngine();
    
    // Set position limits for a contract
    void set_position_limits(const std::string& contract, const PositionLimits& limits);
    
    // Get position limits for a contract
    PositionLimits get_position_limits(const std::string& contract) const;
    
    // Update position state
    void update_position(const std::string& contract, int64_t size_change, double price);
    
    // Get position state for a contract
    PositionState get_position_state(const std::string& contract) const;
    
    // Check if an order is allowed
    RiskCheckResult check_order(
        const std::string& contract,
        int64_t size,
        double price
    );
    
    // Enable/disable kill switch
    void set_kill_switch(bool enabled);
    
    // Check if kill switch is enabled
    bool is_kill_switch_enabled() const;
    
    // Set risk violation callback
    void set_risk_violation_callback(RiskViolationCallback callback);
    
    // Get total exposure across all contracts
    double get_total_exposure() const;
    
    // Get total position across all contracts
    int64_t get_total_position() const;
    
    // Clear all position state
    void clear_positions();
    
    // Clear position state for a specific contract
    void clear_position(const std::string& contract);
    
private:
    std::unordered_map<std::string, PositionLimits> position_limits_;
    std::unordered_map<std::string, PositionState> positions_;
    
    std::atomic<bool> kill_switch_enabled_;
    
    RiskViolationCallback risk_violation_callback_;
    
    mutable std::mutex mutex_;
    
    void notify_risk_violation(const std::string& contract, RiskCheckResult result);
};

} // namespace depthos
