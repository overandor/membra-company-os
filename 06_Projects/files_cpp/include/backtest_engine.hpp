/**
 * Backtest engine for DepthOS C++ implementation.
 */

#ifndef DEPTHOS_BACKTEST_ENGINE_HPP
#define DEPTHOS_BACKTEST_ENGINE_HPP

#include <vector>
#include <unordered_map>
#include <memory>
#include <random>
#include <string>

#include "config.hpp"
#include "risk.hpp"
#include "oms.hpp"
#include "order_book.hpp"
#include "metrics.hpp"

namespace depthos {

/**
 * Market snapshot data structure.
 */
struct MarketSnapshot {
    int64_t timestamp;
    std::string contract;
    Decimal bid_price;
    int bid_size;
    Decimal ask_price;
    int ask_size;
    std::optional<Decimal> last_price;
};

/**
 * Backtest engine for simulating trading strategies on historical data.
 */
class BacktestEngine {
public:
    BacktestEngine(
        int slippage_bps = 5,
        int latency_ms = 50,
        double fill_probability = 0.3
    );
    
    // Data loading
    void load_snapshots_from_csv(const std::string& filepath, const std::string& contract);
    void generate_synthetic_data(
        const std::string& contract,
        size_t num_snapshots = 10000,
        Decimal start_price = Decimal("0.00005"),
        Decimal volatility = Decimal("0.00001"),
        int spread_bps = 20
    );
    
    // Backtest execution
    std::unique_ptr<BacktestMetrics> run_backtest(
        const std::vector<std::string>& contracts,
        const std::unordered_map<std::string, ContractSpec>& specs,
        int duration_seconds = 0
    );
    
    // Accessors
    const std::vector<MarketSnapshot>& snapshots() const { return snapshots_; }
    RiskManager* risk() { return risk_.get(); }
    
private:
    void check_fills(
        const std::string& contract,
        std::unordered_map<std::string, ContractOrders>& orders,
        const MarketSnapshot& snapshot,
        const ContractSpec& spec
    );
    
    void close_all_positions(
        const std::vector<std::string>& contracts,
        const std::unordered_map<std::string, ContractSpec>& specs,
        const MarketSnapshot* last_snapshot
    );
    
    std::unique_ptr<RiskManager> risk_;
    std::unique_ptr<OMS> oms_;
    std::unique_ptr<BacktestMetrics> metrics_;
    std::vector<MarketSnapshot> snapshots_;
    std::unordered_map<std::string, int> current_positions_;
    
    // Simulation parameters
    Decimal maker_fee_rate_;
    Decimal taker_fee_rate_;
    int slippage_bps_;
    int latency_ms_;
    double fill_probability_;
    std::mt19937 rng_;
};

} // namespace depthos

#endif // DEPTHOS_BACKTEST_ENGINE_HPP
