/**
 * Simple backtest runner for DepthOS C++ implementation.
 */

#include "backtest_engine.hpp"
#include "metrics.hpp"
#include <iostream>
#include <iomanip>

using namespace depthos;

int main() {
    std::cout << "DepthOS C++ Backtest Runner\n";
    std::cout << "===========================\n\n";
    
    // Create backtest engine with realistic parameters
    BacktestEngine engine(
        5,      // slippage_bps
        50,     // latency_ms
        0.3     // fill_probability
    );
    
    // Generate synthetic data
    std::cout << "Generating synthetic market data...\n";
    engine.generate_synthetic_data("SHIB_USDT", 10000);
    
    // Create contract spec
    ContractSpec spec{
        .name = "SHIB_USDT",
        .tick_size = Decimal("0.000001"),
        .lot_size = 1,
        .quanto_multiplier = Decimal("0.01"),
        .max_price = Decimal("0.10")
    };
    
    std::unordered_map<std::string, ContractSpec> specs;
    specs["SHIB_USDT"] = spec;
    
    // Run backtest
    std::cout << "Running backtest simulation...\n";
    auto metrics = engine.run_backtest({"SHIB_USDT"}, specs, 3600);  // 1 hour
    
    if (metrics) {
        std::cout << "\n";
        std::cout << metrics->summary();
        std::cout << "\n";
        
        // Alpha interpretation
        std::cout << "\nAlpha Dashboard:\n";
        std::cout << "================\n";
        std::cout << "Order Flow Imbalance (OFI): " << std::fixed << std::setprecision(4) 
                  << static_cast<double>(metrics->avg_ofi) << "\n";
        std::cout << "Interpretation: ";
        if (metrics->avg_ofi > Decimal("0.1")) {
            std::cout << "Strong buy pressure\n";
        } else if (metrics->avg_ofi < Decimal("-0.1")) {
            std::cout << "Strong sell pressure\n";
        } else {
            std::cout << "Balanced market\n";
        }
        
        std::cout << "\nFill Toxicity: " << std::fixed << std::setprecision(4) 
                  << static_cast<double>(metrics->avg_fill_toxicity) << "\n";
        std::cout << "Interpretation: ";
        if (metrics->avg_fill_toxicity > Decimal("0")) {
            std::cout << "Positive fills (good)\n";
        } else {
            std::cout << "Negative fills (being picked off)\n";
        }
        
        std::cout << "\nMaker Fill Ratio: " << std::fixed << std::setprecision(2) 
                  << (static_cast<double>(metrics->maker_fill_ratio) * 100.0) << "%\n";
        std::cout << "Target: > 80%\n";
        
        std::cout << "\nRealized Edge: " << std::fixed << std::setprecision(2) 
                  << static_cast<double>(metrics->realized_edge_bps) << " bps\n";
        std::cout << "Interpretation: ";
        if (metrics->realized_edge_bps > Decimal("2")) {
            std::cout << "STRONG alpha\n";
        } else if (metrics->realized_edge_bps > Decimal("1")) {
            std::cout << "SURVIVABLE alpha\n";
        } else if (metrics->realized_edge_bps > Decimal("0")) {
            std::cout << "WEAK alpha\n";
        } else {
            std::cout << "DEAD strategy\n";
        }
        
        std::cout << "\nQuote Survival Time: " << std::fixed << std::setprecision(2) 
                  << static_cast<double>(metrics->avg_quote_survival_time_ms) << " ms\n";
        std::cout << "Hedge Latency: " << std::fixed << std::setprecision(2) 
                  << static_cast<double>(metrics->avg_hedge_latency_ms) << " ms\n";
    }
    
    return 0;
}
