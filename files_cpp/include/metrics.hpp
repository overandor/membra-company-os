/**
 * Backtest metrics for DepthOS C++ implementation.
 */

#ifndef DEPTHOS_METRICS_HPP
#define DEPTHOS_METRICS_HPP

#include <vector>
#include <unordered_map>
#include <string>
#include <optional>
#include "config.hpp"

namespace depthos {

/**
 * Individual trade record with alpha measurements.
 */
struct Trade {
    int64_t timestamp;
    std::string contract;
    std::string side;  // "buy" or "sell"
    Decimal price;
    int size;
    Decimal fee;
    Decimal pnl;
    
    // Alpha measurement fields
    Decimal ofi = Decimal("0");                    // Order Flow Imbalance at fill time
    Decimal mid_before = Decimal("0");              // Mid price before fill
    Decimal mid_after = Decimal("0");               // Mid price after fill (1s later)
    Decimal fill_toxicity = Decimal("0");           // Fill toxicity
    bool is_maker = true;                           // Whether fill was maker
    Decimal spread_at_fill = Decimal("0");          // Spread at fill time
    Decimal spread_capture = Decimal("0");          // Spread capture efficiency
    int64_t quote_survival_time_ms = 0;             // Time quote was alive
    int64_t hedge_latency_ms = 0;                   // Time to hedge
    Decimal queue_decay_bid = Decimal("0");         // Queue decay bid
    Decimal queue_decay_ask = Decimal("0");         // Queue decay ask
};

/**
 * Backtest performance metrics.
 */
class BacktestMetrics {
public:
    BacktestMetrics();
    
    // Basic stats
    int total_trades = 0;
    int winning_trades = 0;
    int losing_trades = 0;
    
    // P&L
    Decimal total_pnl = Decimal("0");
    Decimal gross_pnl = Decimal("0");
    Decimal total_fees = Decimal("0");
    Decimal max_drawdown = Decimal("0");
    Decimal max_drawdown_pct = Decimal("0");
    
    // Risk metrics
    std::optional<Decimal> sharpe_ratio;
    std::optional<Decimal> sortino_ratio;
    int max_position_size = 0;
    Decimal avg_position_size = Decimal("0");
    
    // Time-based metrics
    Decimal cent_per_second = Decimal("0");
    Decimal cent_per_hour = Decimal("0");
    
    // Alpha metrics
    Decimal avg_ofi = Decimal("0");              // Order Flow Imbalance
    Decimal avg_queue_decay_bid = Decimal("0");    // Queue depletion velocity bid
    Decimal avg_queue_decay_ask = Decimal("0");    // Queue depletion velocity ask
    Decimal avg_fill_toxicity = Decimal("0");      // Fill toxicity
    Decimal maker_fill_ratio = Decimal("0");       // Maker fill ratio
    Decimal avg_spread_capture = Decimal("0");     // Spread capture efficiency
    Decimal avg_hedge_latency_ms = Decimal("0");   // Hedge latency
    Decimal avg_quote_survival_time_ms = Decimal("0"); // Quote survival time
    Decimal adverse_selection_score = Decimal("0"); // Adverse selection score
    Decimal inventory_drift = Decimal("0");        // Inventory drift
    Decimal realized_edge_bps = Decimal("0");       // Realized edge in basis points
    int maker_fills = 0;
    int taker_fills = 0;
    
    // Time tracking
    std::optional<int64_t> start_time;
    std::optional<int64_t> end_time;
    std::optional<int64_t> duration_seconds;
    
    // Per-contract breakdown
    std::unordered_map<std::string, std::unordered_map<std::string, Decimal>> contract_metrics;
    
    // Trade history
    std::vector<Trade> trades;
    
    // Equity curve
    std::vector<Decimal> equity_curve;
    
    // Methods
    void add_trade(const Trade& trade);
    void calculate_metrics();
    std::string summary() const;
    
private:
    Decimal win_rate_ = Decimal("0");
    Decimal avg_trade_pnl_ = Decimal("0");
};

} // namespace depthos

#endif // DEPTHOS_METRICS_HPP
