#include "BookReconciliation.hpp"
#include <spdlog/spdlog.h>

namespace depthos {

BookReconciliation::BookReconciliation() {}

BookReconciliation::~BookReconciliation() {
    clear();
}

bool BookReconciliation::process_delta(
    const std::string& contract,
    uint64_t sequence,
    const std::vector<OrderBookLevel>& bid_changes,
    const std::vector<OrderBookLevel>& ask_changes,
    int64_t timestamp_ms)
{
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Check if we have a previous sequence for this contract
    auto it = last_sequences_.find(contract);
    
    if (it == last_sequences_.end()) {
        // First sequence for this contract
        last_sequences_[contract] = sequence;
        set_state(contract, ReconciliationState::InSync);
        return true;
    }
    
    uint64_t last_seq = it->second;
    
    // Check for gap
    if (sequence > last_seq + 1) {
        // Gap detected
        GapInfo gap;
        gap.expected_seq = last_seq + 1;
        gap.actual_seq = sequence;
        gap.gap_size = sequence - last_seq - 1;
        gap.timestamp_ms = timestamp_ms;
        
        gaps_[contract] = gap;
        set_state(contract, ReconciliationState::GapDetected);
        
        spdlog::warn("Gap detected for {}: expected={}, actual={}, gap_size={}",
                    contract, gap.expected_seq, gap.actual_seq, gap.gap_size);
        
        notify_gap(contract, gap);
        
        return false;
    }
    
    // No gap, update last sequence
    last_sequences_[contract] = sequence;
    set_state(contract, ReconciliationState::InSync);
    
    return true;
}

bool BookReconciliation::process_snapshot(
    const std::string& contract,
    const std::vector<OrderBookLevel>& bids,
    const std::vector<OrderBookLevel>& asks,
    uint64_t sequence,
    int64_t timestamp_ms)
{
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Snapshot resets the sequence
    last_sequences_[contract] = sequence;
    
    // Clear any gap
    auto gap_it = gaps_.find(contract);
    if (gap_it != gaps_.end()) {
        gaps_.erase(gap_it);
    }
    
    set_state(contract, ReconciliationState::InSync);
    
    spdlog::info("Snapshot processed for {}: sequence={}", contract, sequence);
    
    return true;
}

void BookReconciliation::request_resync(const std::string& contract) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    set_state(contract, ReconciliationState::Resyncing);
    
    spdlog::info("Resync requested for {}", contract);
    
    notify_resync(contract);
}

ReconciliationState BookReconciliation::get_state(const std::string& contract) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = states_.find(contract);
    if (it != states_.end()) {
        return it->second;
    }
    
    return ReconciliationState::InSync;
}

uint64_t BookReconciliation::get_last_sequence(const std::string& contract) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = last_sequences_.find(contract);
    if (it != last_sequences_.end()) {
        return it->second;
    }
    
    return 0;
}

bool BookReconciliation::has_gap(const std::string& contract) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    return gaps_.find(contract) != gaps_.end();
}

void BookReconciliation::set_gap_callback(GapCallback callback) {
    gap_callback_ = callback;
}

void BookReconciliation::set_resync_callback(ResyncCallback callback) {
    resync_callback_ = callback;
}

void BookReconciliation::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    last_sequences_.clear();
    states_.clear();
    gaps_.clear();
}

void BookReconciliation::clear_contract(const std::string& contract) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    last_sequences_.erase(contract);
    states_.erase(contract);
    gaps_.erase(contract);
}

void BookReconciliation::set_state(const std::string& contract, ReconciliationState state) {
    states_[contract] = state;
}

void BookReconciliation::notify_gap(const std::string& contract, const GapInfo& gap) {
    if (gap_callback_) {
        gap_callback_(contract, gap);
    }
}

void BookReconciliation::notify_resync(const std::string& contract) {
    if (resync_callback_) {
        resync_callback_(contract);
    }
}

} // namespace depthos
