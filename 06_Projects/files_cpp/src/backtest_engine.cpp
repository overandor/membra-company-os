/**
 * Backtest engine implementation.
 */

#include "backtest_engine.hpp"
#include <chrono>
#include <random>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <iomanip>

namespace depthos {

BacktestEngine::BacktestEngine(int slippage_bps, int latency_ms, double fill_probability)
    : risk_(std::make_unique<RiskManager>())
    , oms_(std::make_unique<OMS>())
    , metrics_(std::make_unique<BacktestMetrics>())
    , maker_fee_rate_(Decimal("0.0002"))  // 0.02% maker fee
    , taker_fee_rate_(Decimal("0.0005"))   // 0.05% taker fee
    , slippage_bps_(slippage_bps)
    , latency_ms_(latency_ms)
    , fill_probability_(fill_probability)
    , rng_(std::chrono::steady_clock::now().time_since_epoch().count())
{
}

void BacktestEngine::load_snapshots_from_csv(const std::string& filepath, const std::string& contract) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open CSV file: " + filepath);
    }
    
    std::string line;
    std::getline(file, line);  // Skip header
    
    while (std::getline(file, line)) {
        std::istringstream iss(line);
        std::string token;
        
        MarketSnapshot snapshot;
        
        std::getline(iss, token, ',');
        snapshot.timestamp = std::stoll(token);
        
        std::getline(iss, token, ',');
        snapshot.bid_price = Decimal(token);
        
        std::getline(iss, token, ',');
        snapshot.bid_size = std::stoi(token);
        
        std::getline(iss, token, ',');
        snapshot.ask_price = Decimal(token);
        
        std::getline(iss, token, ',');
        snapshot.ask_size = std::stoi(token);
        
        snapshot.contract = contract;
        
        if (std::getline(iss, token, ',')) {
            snapshot.last_price = Decimal(token);
        }
        
        snapshots_.push_back(snapshot);
    }
    
    file.close();
}

void BacktestEngine::generate_synthetic_data(
    const std::string& contract,
    size_t num_snapshots,
    Decimal start_price,
    Decimal volatility,
    int spread_bps
) {
    auto now = std::chrono::system_clock::now();
    auto timestamp_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()
    ).count();
    
    Decimal current_price = start_price;
    Decimal spread = start_price * Decimal(spread_bps) / Decimal("10000");
    
    std::uniform_real_distribution<double> dist(-1.0, 1.0);
    std::uniform_int_distribution<int> size_dist(100, 10000);
    
    for (size_t i = 0; i < num_snapshots; ++i) {
        // Random walk price
        double change = dist(rng_) * static_cast<double>(volatility);
        current_price = current_price + Decimal(change);
        if (current_price < Decimal("0.000001")) {
            current_price = Decimal("0.000001");
        }
        
        MarketSnapshot snapshot;
        snapshot.timestamp = timestamp_ms + i * 1000;
        snapshot.contract = contract;
        snapshot.bid_price = current_price - spread / 2;
        snapshot.bid_size = size_dist(rng_);
        snapshot.ask_price = current_price + spread / 2;
        snapshot.ask_size = size_dist(rng_);
        snapshot.last_price = current_price;
        
        snapshots_.push_back(snapshot);
    }
}

std::unique_ptr<BacktestMetrics> BacktestEngine::run_backtest(
    const std::vector<std::string>& contracts,
    const std::unordered_map<std::string, ContractSpec>& specs,
    int duration_seconds
) {
    metrics_ = std::make_unique<BacktestMetrics>();
    current_positions_.clear();
    
    for (const auto& contract : contracts) {
        current_positions_[contract] = 0;
        risk_->state(contract);  // Initialize state
    }
    
    if (snapshots_.empty()) {
        generate_synthetic_data(contracts[0]);
    }
    
    // Set start time
    if (!snapshots_.empty()) {
        metrics_->start_time = snapshots_[0].timestamp;
    }
    
    // Simulate
    std::unordered_map<std::string, ContractOrders> open_orders;
    for (const auto& contract : contracts) {
        open_orders[contract] = ContractOrders{contract};
    }
    
    for (size_t i = 0; i < snapshots_.size(); ++i) {
        const auto& snapshot = snapshots_[i];
        
        // Check duration limit
        if (duration_seconds && metrics_->start_time) {
            int64_t elapsed = snapshot.timestamp - *metrics_->start_time;
            if (elapsed > static_cast<int64_t>(duration_seconds) * 1000) {
                break;
            }
        }
        
        // Only process snapshots for our contracts
        if (std::find(contracts.begin(), contracts.end(), snapshot.contract) == contracts.end()) {
            continue;
        }
        
        const std::string& contract = snapshot.contract;
        auto it = specs.find(contract);
        if (it == specs.end()) {
            continue;
        }
        
        const ContractSpec& spec = it->second;
        
        // Check if we can quote
        if (!risk_->can_quote(contract, spec)) {
            continue;
        }
        
        // Get allowed sizes
        int bid_size = risk_->allowed_buy_size(contract, mm_config.order_size);
        int ask_size = risk_->allowed_sell_size(contract, mm_config.order_size);
        
        if (bid_size == 0 && ask_size == 0) {
            continue;
        }
        
        // Simulate order placement
        if (bid_size > 0 && snapshot.bid_price > Decimal("0")) {
            open_orders[contract].bid_price = snapshot.bid_price;
            open_orders[contract].bid_size = bid_size;
            open_orders[contract].bid_placed_ts = static_cast<double>(snapshot.timestamp);
        }
        
        if (ask_size > 0 && snapshot.ask_price > Decimal("0")) {
            open_orders[contract].ask_price = snapshot.ask_price;
            open_orders[contract].ask_size = ask_size;
            open_orders[contract].ask_placed_ts = static_cast<double>(snapshot.timestamp);
        }
        
        // Check for fills
        check_fills(contract, open_orders, snapshot, spec);
        
        // Update equity curve
        metrics_->equity_curve.push_back(metrics_->total_pnl);
    }
    
    // Close all positions at end
    const MarketSnapshot* last_snapshot = snapshots_.empty() ? nullptr : &snapshots_.back();
    close_all_positions(contracts, specs, last_snapshot);
    
    // Set end time
    if (!snapshots_.empty()) {
        metrics_->end_time = snapshots_.back().timestamp;
    }
    
    // Calculate metrics
    metrics_->calculate_metrics();
    
    return std::move(metrics_);
}

void BacktestEngine::check_fills(
    const std::string& contract,
    std::unordered_map<std::string, ContractOrders>& orders,
    const MarketSnapshot& snapshot,
    const ContractSpec& spec
) {
    Decimal slippage_factor = Decimal(slippage_bps_) / Decimal("10000");
    std::uniform_real_distribution<double> prob_dist(0.0, 1.0);
    
    // Calculate Order Flow Imbalance (OFI)
    Decimal ofi = Decimal("0");
    if (snapshot.bid_size + snapshot.ask_size > 0) {
        ofi = Decimal(snapshot.bid_size - snapshot.ask_size) / Decimal(snapshot.bid_size + snapshot.ask_size);
    }
    
    // Calculate mid price
    Decimal mid_before = Decimal("0");
    if (snapshot.bid_price > Decimal("0") && snapshot.ask_price > Decimal("0")) {
        mid_before = (snapshot.bid_price + snapshot.ask_price) / Decimal("2");
    }
    
    // Calculate spread at fill
    Decimal spread_at_fill = Decimal("0");
    if (snapshot.ask_price > snapshot.bid_price) {
        spread_at_fill = snapshot.ask_price - snapshot.bid_price;
    }
    
    // Check bid fill
    const ContractOrders& contract_orders = orders.at(contract);
    if (contract_orders.bid_size > 0 && snapshot.last_price && snapshot.last_price >= contract_orders.bid_price) {
        // Apply fill probability
        if (prob_dist(rng_) > fill_probability_) {
            return;  // No fill
        }
        
        // Apply slippage
        Decimal fill_price = contract_orders.bid_price * (Decimal("1") + slippage_factor);
        int fill_size = contract_orders.bid_size;
        Decimal fee = fill_price * Decimal(fill_size) * spec.quanto_multiplier * maker_fee_rate_;
        
        // Calculate quote survival time
        int64_t quote_survival_time_ms = snapshot.timestamp - static_cast<int64_t>(contract_orders.bid_placed_ts * 1000);
        
        // Update position
        current_positions_[contract] += fill_size;
        metrics_->max_position_size = std::max(metrics_->max_position_size, std::abs(current_positions_[contract]));
        
        // Create fill
        Fill fill;
        fill.contract = contract;
        fill.size = fill_size;
        fill.price = fill_price;
        fill.fee = fee;
        fill.ts_ms = snapshot.timestamp + latency_ms_;
        risk_->on_fill(fill);
        
        // Calculate P&L
        Decimal pnl;
        if (snapshot.last_price) {
            Decimal unrealized_pnl = (*snapshot.last_price - fill_price) * Decimal(fill_size) * spec.quanto_multiplier;
            pnl = unrealized_pnl - fee;
        } else {
            pnl = -fee;
        }
        
        // Calculate fill toxicity for longs
        Decimal fill_toxicity = Decimal("0");
        if (mid_before > Decimal("0") && snapshot.last_price) {
            fill_toxicity = ((*snapshot.last_price - mid_before) / mid_before) * Decimal("10000");
        }
        
        // Calculate spread capture
        Decimal spread_capture = Decimal("0");
        if (spread_at_fill > Decimal("0")) {
            spread_capture = pnl / spread_at_fill;
        }
        
        // Record trade with alpha metrics
        Trade trade;
        trade.timestamp = snapshot.timestamp + latency_ms_;
        trade.contract = contract;
        trade.side = "buy";
        trade.price = fill_price;
        trade.size = fill_size;
        trade.fee = fee;
        trade.pnl = pnl;
        trade.ofi = ofi;
        trade.mid_before = mid_before;
        trade.mid_after = snapshot.last_price ? *snapshot.last_price : Decimal("0");
        trade.fill_toxicity = fill_toxicity;
        trade.is_maker = true;
        trade.spread_at_fill = spread_at_fill;
        trade.spread_capture = spread_capture;
        trade.quote_survival_time_ms = quote_survival_time_ms;
        trade.hedge_latency_ms = latency_ms_;
        trade.queue_decay_bid = Decimal("0");
        trade.queue_decay_ask = Decimal("0");
        metrics_->add_trade(trade);
    }
    
    // Check ask fill
    if (contract_orders.ask_size > 0 && snapshot.last_price && snapshot.last_price <= contract_orders.ask_price) {
        // Apply fill probability
        if (prob_dist(rng_) > fill_probability_) {
            return;  // No fill
        }
        
        // Apply slippage (worse price for seller)
        Decimal fill_price = contract_orders.ask_price * (Decimal("1") - slippage_factor);
        int fill_size = contract_orders.ask_size;
        Decimal fee = fill_price * Decimal(fill_size) * spec.quanto_multiplier * maker_fee_rate_;
        
        // Calculate quote survival time
        int64_t quote_survival_time_ms = snapshot.timestamp - static_cast<int64_t>(contract_orders.ask_placed_ts * 1000);
        
        // Update position
        current_positions_[contract] -= fill_size;
        metrics_->max_position_size = std::max(metrics_->max_position_size, std::abs(current_positions_[contract]));
        
        // Create fill
        Fill fill;
        fill.contract = contract;
        fill.size = -fill_size;
        fill.price = fill_price;
        fill.fee = fee;
        fill.ts_ms = snapshot.timestamp + latency_ms_;
        risk_->on_fill(fill);
        
        // Calculate P&L
        Decimal pnl;
        if (snapshot.last_price) {
            Decimal unrealized_pnl = (fill_price - *snapshot.last_price) * Decimal(fill_size) * spec.quanto_multiplier;
            pnl = unrealized_pnl - fee;
        } else {
            pnl = -fee;
        }
        
        // Calculate fill toxicity for shorts
        Decimal fill_toxicity = Decimal("0");
        if (mid_before > Decimal("0") && snapshot.last_price) {
            fill_toxicity = (mid_before - *snapshot.last_price) / mid_before * Decimal("10000");
        }
        
        // Calculate spread capture
        Decimal spread_capture = Decimal("0");
        if (spread_at_fill > Decimal("0")) {
            spread_capture = pnl / spread_at_fill;
        }
        
        // Record trade with alpha metrics
        Trade trade;
        trade.timestamp = snapshot.timestamp + latency_ms_;
        trade.contract = contract;
        trade.side = "sell";
        trade.price = fill_price;
        trade.size = fill_size;
        trade.fee = fee;
        trade.pnl = pnl;
        trade.ofi = ofi;
        trade.mid_before = mid_before;
        trade.mid_after = snapshot.last_price ? *snapshot.last_price : Decimal("0");
        trade.fill_toxicity = fill_toxicity;
        trade.is_maker = true;
        trade.spread_at_fill = spread_at_fill;
        trade.spread_capture = spread_capture;
        trade.quote_survival_time_ms = quote_survival_time_ms;
        trade.hedge_latency_ms = latency_ms_;
        trade.queue_decay_bid = Decimal("0");
        trade.queue_decay_ask = Decimal("0");
        metrics_->add_trade(trade);
    }
}

void BacktestEngine::close_all_positions(
    const std::vector<std::string>& contracts,
    const std::unordered_map<std::string, ContractSpec>& specs,
    const MarketSnapshot* last_snapshot
) {
    for (const auto& contract : contracts) {
        int position = current_positions_[contract];
        if (position == 0) {
            continue;
        }
        
        auto it = specs.find(contract);
        if (it == specs.end()) {
            continue;
        }
        
        const ContractSpec& spec = it->second;
        
        if (!last_snapshot || !last_snapshot->last_price) {
            continue;
        }
        
        Decimal close_price = *last_snapshot->last_price;
        int size = std::abs(position);
        std::string side = position > 0 ? "sell" : "buy";
        Decimal fee = close_price * Decimal(size) * spec.quanto_multiplier * taker_fee_rate_;
        
        // Calculate closing P&L
        Decimal pnl;
        if (position > 0) {
            // Closing long
            pnl = (close_price * Decimal(size) * spec.quanto_multiplier) - fee;
        } else {
            // Closing short
            pnl = (-close_price * Decimal(size) * spec.quanto_multiplier) - fee;
        }
        
        // Record trade
        Trade trade;
        trade.timestamp = last_snapshot->timestamp;
        trade.contract = contract;
        trade.side = side;
        trade.price = close_price;
        trade.size = size;
        trade.fee = fee;
        trade.pnl = pnl;
        metrics_->add_trade(trade);
        
        // Reset position
        current_positions_[contract] = 0;
    }
}

} // namespace depthos
