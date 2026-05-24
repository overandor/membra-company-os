/**
 * Backtest metrics implementation.
 */

#include "metrics.hpp"
#include <sstream>
#include <iomanip>
#include <cmath>
#include <numeric>

namespace depthos {

BacktestMetrics::BacktestMetrics() = default;

void BacktestMetrics::add_trade(const Trade& trade) {
    trades.push_back(trade);
    total_trades++;
    
    if (trade.pnl > Decimal("0")) {
        winning_trades++;
    } else if (trade.pnl < Decimal("0")) {
        losing_trades++;
    }
    
    total_pnl += trade.pnl;
    gross_pnl += trade.pnl + trade.fee;
    total_fees += trade.fee;
    
    // Alpha metrics accumulation
    avg_ofi += trade.ofi;
    avg_fill_toxicity += trade.fill_toxicity;
    avg_spread_capture += trade.spread_capture;
    avg_quote_survival_time_ms += Decimal(trade.quote_survival_time_ms);
    avg_hedge_latency_ms += Decimal(trade.hedge_latency_ms);
    avg_queue_decay_bid += trade.queue_decay_bid;
    avg_queue_decay_ask += trade.queue_decay_ask;
    
    if (trade.is_maker) {
        maker_fills++;
    } else {
        taker_fills++;
    }
    
    // Track per-contract metrics
    if (contract_metrics.find(trade.contract) == contract_metrics.end()) {
        contract_metrics[trade.contract] = {
            {"trades", Decimal("0")},
            {"pnl", Decimal("0")},
            {"fees", Decimal("0")},
            {"max_position", Decimal("0")},
            {"ofi", Decimal("0")},
            {"toxicity", Decimal("0")}
        };
    }
    
    contract_metrics[trade.contract]["trades"] += Decimal("1");
    contract_metrics[trade.contract]["pnl"] += trade.pnl;
    contract_metrics[trade.contract]["fees"] += trade.fee;
    contract_metrics[trade.contract]["ofi"] += trade.ofi;
    contract_metrics[trade.contract]["toxicity"] += trade.fill_toxicity;
}

void BacktestMetrics::calculate_metrics() {
    if (trades.empty()) {
        return;
    }
    
    // Win rate
    if (total_trades > 0) {
        win_rate_ = Decimal(winning_trades) / Decimal(total_trades);
    }
    
    // Average trade
    if (total_trades > 0) {
        avg_trade_pnl_ = total_pnl / Decimal(total_trades);
        
        // Alpha metrics averages
        avg_ofi /= Decimal(total_trades);
        avg_fill_toxicity /= Decimal(total_trades);
        avg_spread_capture /= Decimal(total_trades);
        avg_quote_survival_time_ms /= Decimal(total_trades);
        avg_hedge_latency_ms /= Decimal(total_trades);
        avg_queue_decay_bid /= Decimal(total_trades);
        avg_queue_decay_ask /= Decimal(total_trades);
        
        // Maker fill ratio
        maker_fill_ratio = Decimal(maker_fills) / Decimal(total_trades);
        
        // Realized edge in basis points
        Decimal gross_notional = gross_pnl + total_fees;
        if (gross_notional > Decimal("0")) {
            realized_edge_bps = (total_pnl / gross_notional) * Decimal("10000");
        }
        
        // Adverse selection score (simplified: avg post-fill return)
        adverse_selection_score = avg_fill_toxicity;
        
        // Inventory drift (simplified: max position size)
        inventory_drift = Decimal(max_position_size);
    }
    
    // Max drawdown from equity curve
    if (equity_curve.size() > 1) {
        Decimal peak = equity_curve[0];
        for (const auto& equity : equity_curve) {
            if (equity > peak) {
                peak = equity;
            }
            Decimal drawdown = peak - equity;
            if (drawdown > max_drawdown) {
                max_drawdown = drawdown;
            }
        }
        
        if (peak > Decimal("0")) {
            max_drawdown_pct = (max_drawdown / peak) * Decimal("100");
        }
    }
    
    // Duration
    if (start_time && end_time) {
        duration_seconds = *end_time - *start_time;
    }
    
    // Cent per second and cent per hour
    if (duration_seconds && *duration_seconds > 0) {
        Decimal pnl_cents = total_pnl * Decimal("100");
        cent_per_second = pnl_cents / Decimal(*duration_seconds);
        cent_per_hour = cent_per_second * Decimal("3600");
    }
    
    // Sharpe ratio calculation (simplified)
    if (equity_curve.size() > 2 && duration_seconds) {
        std::vector<Decimal> returns;
        for (size_t i = 1; i < equity_curve.size(); ++i) {
            if (equity_curve[i-1] != Decimal("0")) {
                Decimal ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1];
                returns.push_back(ret);
            }
        }
        
        if (!returns.empty()) {
            Decimal avg_return = std::accumulate(returns.begin(), returns.end(), Decimal("0")) / Decimal(returns.size());
            
            Decimal variance = Decimal("0");
            for (const auto& r : returns) {
                Decimal diff = r - avg_return;
                variance += diff * diff;
            }
            variance /= Decimal(returns.size());
            
            double variance_d = static_cast<double>(variance);
            double std_dev_d = std::sqrt(variance_d);
            Decimal std_dev = Decimal(std_dev_d > 0 ? std_dev_d : 0.000001);
            
            // Annualized Sharpe (assuming 252 trading days)
            if (std_dev > Decimal("0")) {
                Decimal periods_per_year = Decimal("252") * Decimal("24") * Decimal("3600") / Decimal(*duration_seconds);
                double periods_per_year_d = static_cast<double>(periods_per_year);
                double avg_return_d = static_cast<double>(avg_return);
                double sharpe_d = (avg_return_d * periods_per_year_d) / (std_dev_d * std::sqrt(periods_per_year_d));
                sharpe_ratio = Decimal(sharpe_d);
            }
        }
    }
}

std::string BacktestMetrics::summary() const {
    std::ostringstream oss;
    
    oss << "============================================================\n";
    oss << "BACKTEST METRICS SUMMARY\n";
    oss << "============================================================\n";
    oss << "Total Trades: " << total_trades << "\n";
    oss << "Winning Trades: " << winning_trades << "\n";
    oss << "Losing Trades: " << losing_trades << "\n";
    oss << "Win Rate: " << std::fixed << std::setprecision(2) << (static_cast<double>(win_rate_) * 100.0) << "%\n";
    oss << "\n";
    oss << "Total P&L: " << std::fixed << std::setprecision(4) << static_cast<double>(total_pnl) << " USDT\n";
    oss << "Gross P&L: " << std::fixed << std::setprecision(4) << static_cast<double>(gross_pnl) << " USDT\n";
    oss << "Total Fees: " << std::fixed << std::setprecision(4) << static_cast<double>(total_fees) << " USDT\n";
    oss << "Average Trade: " << std::fixed << std::setprecision(4) << static_cast<double>(avg_trade_pnl_) << " USDT\n";
    oss << "\n";
    oss << "Max Drawdown: " << std::fixed << std::setprecision(4) << static_cast<double>(max_drawdown) << " USDT (" 
        << std::fixed << std::setprecision(2) << static_cast<double>(max_drawdown_pct) << "%)\n";
    oss << "Max Position: " << max_position_size << " contracts\n";
    oss << "\n";
    
    if (sharpe_ratio) {
        oss << "Sharpe Ratio: " << std::fixed << std::setprecision(2) << static_cast<double>(*sharpe_ratio) << "\n";
    }
    
    oss << "\n";
    oss << "Cent per Second: " << std::fixed << std::setprecision(4) << static_cast<double>(cent_per_second) << "\n";
    oss << "Cent per Hour: " << std::fixed << std::setprecision(4) << static_cast<double>(cent_per_hour) << "\n";
    
    if (duration_seconds) {
        double hours = static_cast<double>(*duration_seconds) / 3600.0;
        oss << "Duration: " << std::fixed << std::setprecision(2) << hours << " hours\n";
        oss << "\n";
    }
    
    // Alpha metrics section
    oss << "============================================================\n";
    oss << "ALPHA METRICS\n";
    oss << "============================================================\n";
    oss << "Order Flow Imbalance (OFI): " << std::fixed << std::setprecision(4) << static_cast<double>(avg_ofi) << "\n";
    oss << "Fill Toxicity: " << std::fixed << std::setprecision(4) << static_cast<double>(avg_fill_toxicity) << "\n";
    oss << "Maker Fill Ratio: " << std::fixed << std::setprecision(2) << (static_cast<double>(maker_fill_ratio) * 100.0) << "%\n";
    oss << "Spread Capture Efficiency: " << std::fixed << std::setprecision(4) << static_cast<double>(avg_spread_capture) << "\n";
    oss << "Quote Survival Time: " << std::fixed << std::setprecision(2) << static_cast<double>(avg_quote_survival_time_ms) << " ms\n";
    oss << "Hedge Latency: " << std::fixed << std::setprecision(2) << static_cast<double>(avg_hedge_latency_ms) << " ms\n";
    oss << "Queue Decay Bid: " << std::fixed << std::setprecision(4) << static_cast<double>(avg_queue_decay_bid) << "\n";
    oss << "Queue Decay Ask: " << std::fixed << std::setprecision(4) << static_cast<double>(avg_queue_decay_ask) << "\n";
    oss << "Adverse Selection Score: " << std::fixed << std::setprecision(4) << static_cast<double>(adverse_selection_score) << "\n";
    oss << "Inventory Drift: " << std::fixed << std::setprecision(2) << static_cast<double>(inventory_drift) << "\n";
    oss << "Realized Edge: " << std::fixed << std::setprecision(2) << static_cast<double>(realized_edge_bps) << " bps\n";
    oss << "\n";
    
    // Alpha interpretation
    oss << "Alpha Interpretation:\n";
    if (realized_edge_bps > Decimal("2")) {
        oss << "  Realized Edge: STRONG (> 2 bps)\n";
    } else if (realized_edge_bps > Decimal("1")) {
        oss << "  Realized Edge: SURVIVABLE (1-2 bps)\n";
    } else if (realized_edge_bps > Decimal("0")) {
        oss << "  Realized Edge: WEAK (0-1 bps)\n";
    } else {
        oss << "  Realized Edge: DEAD STRATEGY (< 0 bps)\n";
    }
    
    if (maker_fill_ratio < Decimal("0.8")) {
        oss << "  WARNING: Maker ratio < 80%, fees destroying edge\n";
    }
    
    if (avg_fill_toxicity < Decimal("0")) {
        oss << "  WARNING: Negative toxicity, being picked off by informed traders\n";
    }
    
    oss << "\n";
    
    if (!contract_metrics.empty()) {
        oss << "Per-Contract Breakdown:\n";
        oss << "------------------------------------------------------------\n";
        for (const auto& [contract, metrics] : contract_metrics) {
            auto it_trades = metrics.find("trades");
            auto it_pnl = metrics.find("pnl");
            auto it_fees = metrics.find("fees");
            
            int trades = it_trades != metrics.end() ? static_cast<int>(it_trades->second) : 0;
            Decimal pnl = it_pnl != metrics.end() ? it_pnl->second : Decimal("0");
            Decimal fees = it_fees != metrics.end() ? it_fees->second : Decimal("0");
            
            oss << "  " << contract << ": " << trades << " trades, "
                << "P&L: " << std::fixed << std::setprecision(4) << static_cast<double>(pnl) << ", "
                << "Fees: " << std::fixed << std::setprecision(4) << static_cast<double>(fees) << "\n";
        }
    }
    
    oss << "============================================================\n";
    
    return oss.str();
}

} // namespace depthos
