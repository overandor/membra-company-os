/**
 * Backtest tests for DepthOS C++ implementation.
 */

#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>

#include "../include/backtest_engine.hpp"
#include "../include/metrics.hpp"
#include "../include/config.hpp"

using namespace depthos;

TEST_CASE("BacktestMetrics initialization") {
    BacktestMetrics metrics;
    
    REQUIRE(metrics.total_trades == 0);
    REQUIRE(metrics.total_pnl == Decimal("0"));
    REQUIRE(metrics.max_drawdown == Decimal("0"));
}

TEST_CASE("BacktestMetrics add trade") {
    BacktestMetrics metrics;
    
    Trade trade{
        .timestamp = 1234567890,
        .contract = "SHIB_USDT",
        .side = "buy",
        .price = Decimal("0.00005"),
        .size = 10,
        .fee = Decimal("0.000001"),
        .pnl = Decimal("0.0001")
    };
    
    metrics.add_trade(trade);
    
    REQUIRE(metrics.total_trades == 1);
    REQUIRE(metrics.winning_trades == 1);
    REQUIRE(metrics.total_pnl == Decimal("0.0001"));
}

TEST_CASE("BacktestEngine initialization") {
    BacktestEngine engine;
    
    REQUIRE(engine.risk() != nullptr);
    REQUIRE(engine.snapshots().empty());
}

TEST_CASE("BacktestEngine generate synthetic data") {
    BacktestEngine engine;
    
    engine.generate_synthetic_data("SHIB_USDT", 100);
    
    REQUIRE(engine.snapshots().size() == 100);
    REQUIRE(engine.snapshots()[0].contract == "SHIB_USDT");
}

TEST_CASE("BacktestEngine run backtest") {
    BacktestEngine engine;
    
    engine.generate_synthetic_data("SHIB_USDT", 1000);
    
    ContractSpec spec{
        .name = "SHIB_USDT",
        .tick_size = Decimal("0.000001"),
        .lot_size = 1,
        .quanto_multiplier = Decimal("0.01"),
        .max_price = Decimal("0.10")
    };
    
    std::unordered_map<std::string, ContractSpec> specs;
    specs["SHIB_USDT"] = spec;
    
    auto metrics = engine.run_backtest({"SHIB_USDT"}, specs, 60);
    
    REQUIRE(metrics != nullptr);
    REQUIRE(metrics->total_trades >= 0);
}
