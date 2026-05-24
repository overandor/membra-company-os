#include "risk.hpp"
#include "config.hpp"
#include "logger.hpp"
#include <iostream>
#include <sstream>
#include <iomanip>

namespace depthos {

// ContractRiskState implementation
void ContractRiskState::update_fill(const Fill& fill) {
    fills.push_back(fill);
    int prev_pos = net_position;
    net_position += fill.size;
    
    total_fees += fill.fee;
    
    // Realized PnL calculation (simplified)
    if (prev_pos != 0 && ((prev_pos > 0 && fill.size < 0) || (prev_pos < 0 && fill.size > 0))) {
        // Closing trade
        Decimal avg_entry = avg_entry_price();
        if (avg_entry > Decimal("0")) {
            int closing_size = std::min(std::abs(fill.size), std::abs(prev_pos));
            if (prev_pos > 0) {
                // Was long, closing with sell
                Decimal pnl = (fill.price - avg_entry) * Decimal(closing_size);
                realized_pnl += pnl;
            } else {
                // Was short, closing with buy
                Decimal pnl = (avg_entry - fill.price) * Decimal(closing_size);
                realized_pnl += pnl;
            }
        }
    }
}

Decimal ContractRiskState::avg_entry_price() const {
    if (fills.empty()) return Decimal("0");
    
    // Calculate average entry price
    int total_size = 0;
    Decimal total_value = Decimal("0");
    
    for (const auto& fill : fills) {
        if (fill.size != 0) {
            total_size += std::abs(fill.size);
            total_value += Decimal(std::abs(fill.size)) * fill.price;
        }
    }
    
    if (total_size == 0) return Decimal("0");
    
    return total_value / Decimal(total_size);
}

// RiskManager implementation
RiskManager::RiskManager() 
    : day_start_ts_(static_cast<double>(std::chrono::system_clock::to_time_t(std::chrono::system_clock::now()))) {
}

ContractRiskState& RiskManager::state(const std::string& contract) {
    if (states_.find(contract) == states_.end()) {
        states_[contract] = ContractRiskState();
        states_[contract].contract = contract;
    }
    return states_[contract];
}

int RiskManager::net_position(const std::string& contract) {
    return state(contract).net_position;
}

void RiskManager::on_fill(const Fill& fill) {
    ContractRiskState& s = state(fill.contract);
    s.update_fill(fill);
    
    // Subtract fee from daily PnL
    daily_pnl_ -= fill.fee;
    
    check_daily_loss_halt();
    
    LOG_INFO("Fill: {} size={} price={} fee={} net_pos={}", fill.contract, fill.size, fill.price.str(), fill.fee.str(), s.net_position);
}

void RiskManager::on_pnl_delta(const std::string& contract, const Decimal& delta) {
    state(contract).unrealized_pnl += delta;
    daily_pnl_ += delta;
}

bool RiskManager::can_quote(const std::string& contract, const ContractSpec& spec) {
    if (global_halted_) {
        LOG_DEBUG("can_quote {} -> False (global halt: {})", contract, global_reason_);
        return false;
    }
    
    ContractRiskState& s = state(contract);
    if (s.halted) {
        LOG_DEBUG("can_quote {} -> False (contract halt: {})", contract, s.halt_reason);
        return false;
    }
    
    return true;
}

int RiskManager::allowed_buy_size(const std::string& contract, int requested) {
    int pos = net_position(contract);
    int max_inv = mm_config.max_inventory_contracts;
    
    if (pos >= max_inv) {
        return 0;
    }
    
    // Skew reduction
    int skew_thresh = mm_config.skew_threshold_contracts;
    if (pos >= skew_thresh) {
        double fraction = 1.0 - (pos - skew_thresh) / static_cast<double>(max_inv - skew_thresh);
        requested = std::max(1, static_cast<int>(requested * fraction));
    }
    
    return std::min(requested, max_inv - pos);
}

int RiskManager::allowed_sell_size(const std::string& contract, int requested) {
    int pos = net_position(contract);
    int max_inv = mm_config.max_inventory_contracts;
    
    if (pos <= -max_inv) {
        return 0;
    }
    
    int skew_thresh = mm_config.skew_threshold_contracts;
    if (pos <= -skew_thresh) {
        double fraction = 1.0 - (-pos - skew_thresh) / static_cast<double>(max_inv - skew_thresh);
        requested = std::max(1, static_cast<int>(requested * fraction));
    }
    
    return std::min(requested, max_inv + pos);
}

void RiskManager::check_daily_loss_halt() {
    if (daily_pnl_ < -mm_config.daily_loss_limit_usdt) {
        global_halted_ = true;
        std::ostringstream oss;
        oss << "Daily loss limit hit: " << daily_pnl_.str() << " USDT < -" << mm_config.daily_loss_limit_usdt.str();
        global_reason_ = oss.str();
        LOG_CRITICAL("GLOBAL HALT - {}", global_reason_);
    }
}

void RiskManager::reset_daily() {
    LOG_INFO("Daily PnL reset. Previous: {} USDT. Unhalt: {}", daily_pnl_.str(), global_halted_);
    daily_pnl_ = Decimal("0");
    day_start_ts_ = static_cast<double>(std::chrono::system_clock::to_time_t(std::chrono::system_clock::now()));
    global_halted_ = false;
    global_reason_.clear();
}

std::string RiskManager::summary() const {
    std::ostringstream oss;
    oss << std::string(60, '-') << "\n";
    oss << "  RISK SUMMARY  daily_pnl=" << daily_pnl_.str() << " USDT\n";
    
    if (global_halted_) {
        oss << "  ⚠ GLOBAL HALT: " << global_reason_ << "\n";
    }
    
    for (const auto& [contract, state] : states_) {
        oss << "  " << std::left << std::setw(20) << contract 
            << "  pos=" << std::setw(6) << state.net_position
            << "  realized=" << state.realized_pnl.str()
            << "  fees=" << state.total_fees.str() << "\n";
    }
    
    oss << std::string(60, '-');
    return oss.str();
}

// Global risk manager
RiskManager risk;

} // namespace depthos
