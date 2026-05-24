#include "RiskEngine.hpp"
#include <spdlog/spdlog.h>
#include <cmath>

namespace depthos {

RiskEngine::RiskEngine() : kill_switch_enabled_(false) {}

RiskEngine::~RiskEngine() {
    clear_positions();
}

void RiskEngine::set_position_limits(const std::string& contract, const PositionLimits& limits) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    position_limits_[contract] = limits;
    
    spdlog::info("Set position limits for {}: max_position={}, max_order={}, max_exposure={}",
                contract, limits.max_position, limits.max_order_size, limits.max_exposure_usdt);
}

PositionLimits RiskEngine::get_position_limits(const std::string& contract) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = position_limits_.find(contract);
    if (it != position_limits_.end()) {
        return it->second;
    }
    
    // Return default limits if not set
    return PositionLimits();
}

void RiskEngine::update_position(const std::string& contract, int64_t size_change, double price) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    PositionState& state = positions_[contract];
    state.current_position += size_change;
    state.current_exposure_usdt += std::abs(size_change * price);
    
    spdlog::debug("Updated position for {}: position={}, exposure={}",
                 contract, state.current_position, state.current_exposure_usdt);
}

PositionState RiskEngine::get_position_state(const std::string& contract) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = positions_.find(contract);
    if (it != positions_.end()) {
        return it->second;
    }
    
    return PositionState();
}

RiskCheckResult RiskEngine::check_order(
    const std::string& contract,
    int64_t size,
    double price)
{
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check kill switch first
    if (kill_switch_enabled_) {
        spdlog::warn("Kill switch enabled, rejecting order for {}", contract);
        return RiskCheckResult::FailKillSwitch;
    }
    
    // Get position limits
    auto limits_it = position_limits_.find(contract);
    if (limits_it == position_limits_.end()) {
        spdlog::warn("No position limits set for {}, rejecting order", contract);
        return RiskCheckResult::FailUnknown;
    }
    
    const PositionLimits& limits = limits_it->second;
    
    // Check order size
    if (std::abs(size) > limits.max_order_size) {
        spdlog::warn("Order size {} exceeds limit {} for {}", size, limits.max_order_size, contract);
        return RiskCheckResult::FailPositionLimit;
    }
    
    // Check position limit
    PositionState state = positions_[contract];
    int64_t new_position = state.current_position + size;
    
    if (std::abs(new_position) > limits.max_position) {
        spdlog::warn("New position {} exceeds limit {} for {}", new_position, limits.max_position, contract);
        return RiskCheckResult::FailPositionLimit;
    }
    
    // Check exposure limit
    double new_exposure = state.current_exposure_usdt + std::abs(size * price);
    
    if (new_exposure > limits.max_exposure_usdt) {
        spdlog::warn("New exposure {} exceeds limit {} for {}", new_exposure, limits.max_exposure_usdt, contract);
        return RiskCheckResult::FailExposureLimit;
    }
    
    // Check total exposure across all contracts
    double total_exposure = 0.0;
    for (const auto& [_, pos_state] : positions_) {
        total_exposure += pos_state.current_exposure_usdt;
    }
    total_exposure += std::abs(size * price);
    
    // Simple check: total exposure shouldn't exceed 10x single contract limit
    if (total_exposure > limits.max_exposure_usdt * 10) {
        spdlog::warn("Total exposure {} exceeds safe limit for {}", total_exposure, contract);
        return RiskCheckResult::FailExposureLimit;
    }
    
    return RiskCheckResult::Pass;
}

void RiskEngine::set_kill_switch(bool enabled) {
    kill_switch_enabled_ = enabled;
    
    if (enabled) {
        spdlog::warn("KILL SWITCH ENABLED - All trading will be blocked");
    } else {
        spdlog::info("Kill switch disabled");
    }
}

bool RiskEngine::is_kill_switch_enabled() const {
    return kill_switch_enabled_;
}

void RiskEngine::set_risk_violation_callback(RiskViolationCallback callback) {
    risk_violation_callback_ = callback;
}

double RiskEngine::get_total_exposure() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    double total = 0.0;
    for (const auto& [_, state] : positions_) {
        total += state.current_exposure_usdt;
    }
    
    return total;
}

int64_t RiskEngine::get_total_position() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    int64_t total = 0;
    for (const auto& [_, state] : positions_) {
        total += std::abs(state.current_position);
    }
    
    return total;
}

void RiskEngine::clear_positions() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    positions_.clear();
    spdlog::info("Cleared all positions");
}

void RiskEngine::clear_position(const std::string& contract) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    positions_.erase(contract);
    spdlog::info("Cleared position for {}", contract);
}

void RiskEngine::notify_risk_violation(const std::string& contract, RiskCheckResult result) {
    if (risk_violation_callback_) {
        risk_violation_callback_(contract, result);
    }
}

} // namespace depthos
