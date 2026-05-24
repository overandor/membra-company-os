#pragma once

#include <string>
#include <unordered_map>
#include <cstdint>
#include <vector>
#include <functional>
#include <mutex>

#include "OrderBook.hpp"

namespace depthos {

enum class ReconciliationState {
    InSync,
    GapDetected,
    Resyncing,
    Error
};

struct GapInfo {
    uint64_t expected_seq;
    uint64_t actual_seq;
    uint64_t gap_size;
    int64_t timestamp_ms;
    
    GapInfo() : expected_seq(0), actual_seq(0), gap_size(0), timestamp_ms(0) {}
};

using GapCallback = std::function<void(const std::string& contract, const GapInfo& gap)>;
using ResyncCallback = std::function<void(const std::string& contract)>;

class BookReconciliation {
public:
    BookReconciliation();
    ~BookReconciliation();
    
    // Process a delta update with sequence validation
    bool process_delta(
        const std::string& contract,
        uint64_t sequence,
        const std::vector<OrderBookLevel>& bid_changes,
        const std::vector<OrderBookLevel>& ask_changes,
        int64_t timestamp_ms
    );
    
    // Process a snapshot update
    bool process_snapshot(
        const std::string& contract,
        const std::vector<OrderBookLevel>& bids,
        const std::vector<OrderBookLevel>& asks,
        uint64_t sequence,
        int64_t timestamp_ms
    );
    
    // Request a resync for a contract
    void request_resync(const std::string& contract);
    
    // Get reconciliation state for a contract
    ReconciliationState get_state(const std::string& contract) const;
    
    // Get last sequence for a contract
    uint64_t get_last_sequence(const std::string& contract) const;
    
    // Check if there's a gap
    bool has_gap(const std::string& contract) const;
    
    // Set gap callback
    void set_gap_callback(GapCallback callback);
    
    // Set resync callback
    void set_resync_callback(ResyncCallback callback);
    
    // Clear all reconciliation state
    void clear();
    
    // Clear reconciliation state for a specific contract
    void clear_contract(const std::string& contract);
    
private:
    std::unordered_map<std::string, uint64_t> last_sequences_;
    std::unordered_map<std::string, ReconciliationState> states_;
    std::unordered_map<std::string, GapInfo> gaps_;
    
    GapCallback gap_callback_;
    ResyncCallback resync_callback_;
    
    mutable std::mutex mutex_;
    
    void set_state(const std::string& contract, ReconciliationState state);
    void notify_gap(const std::string& contract, const GapInfo& gap);
    void notify_resync(const std::string& contract);
};

} // namespace depthos
