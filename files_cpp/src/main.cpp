#include "config.hpp"
#include "auth.hpp"
#include "rest_client.hpp"
#include "ws_manager.hpp"
#include "quoting_engine.hpp"
#include "order_book.hpp"
#include "risk.hpp"
#include "oms.hpp"
#include "logger.hpp"
#include <iostream>
#include <csignal>
#include <thread>
#include <chrono>

namespace depthos {

// Global shutdown flag
std::atomic<bool> shutdown_requested(false);

void signal_handler(int signal) {
    std::cout << "\nShutdown signal received (" << signal << ") - stopping gracefully..." << std::endl;
    shutdown_requested = true;
}

void register_signals() {
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);
}

// Bootstrap phase
bool bootstrap(RestClient& client) {
    LOG_INFO("=== BOOTSTRAP START ===");
    
    // Account mode
    std::string mode = client.fetch_account_mode();
    mm_config.account_mode = mode;
    LOG_INFO("Account mode: {}", mode);
    
    // Balance check
    Decimal balance = client.fetch_balance();
    LOG_INFO("USDT Futures balance: {}", balance.str());
    if (balance < Decimal("1.0")) {
        LOG_WARN("Balance {} is very low - dry_run forced", balance.str());
        mm_config.dry_run = true;
    }
    
    // Contract specs
    auto specs = client.fetch_contract_specs(MICRO_CONTRACTS);
    if (specs.empty()) {
        LOG_ERROR("No valid micro-price contracts found. Check MICRO_CONTRACTS list.");
        return false;
    }
    
    mm_config.contracts = specs;
    LOG_INFO("Loaded {} valid contracts", specs.size());
    
    // Seed risk engine with existing positions (crash recovery)
    for (const auto& [contract, spec] : specs) {
        try {
            int pos = client.fetch_position(contract);
            LOG_WARN("Existing position {}: %+d contracts — seeding risk state", contract, pos);
            risk.state(contract).net_position = pos;
        } catch (const std::exception& exc) {
            LOG_WARN("Could not fetch position for {}: {}", contract, exc.what());
        }
    }
    
    LOG_INFO("=== BOOTSTRAP COMPLETE ===");
    return true;
}

// Heartbeat loop
void heartbeat_loop() {
    int last_reset_day = 0;
    
    while (!shutdown_requested) {
        std::this_thread::sleep_for(std::chrono::seconds(static_cast<int>(mm_config.heartbeat_interval_s)));
        
        if (shutdown_requested) break;
        
        // Daily reset at UTC midnight (simplified)
        auto now = std::chrono::system_clock::now();
        time_t tt = std::chrono::system_clock::to_time_t(now);
        tm* utc_tm = gmtime(&tt);
        int today = utc_tm->tm_yday;
        
        if (last_reset_day == 0) {
            last_reset_day = today;
        } else if (today != last_reset_day) {
            last_reset_day = today;
            risk.reset_daily();
        }
        
        // Status dump
        LOG_INFO("HEARTBEAT  live_orders={}", oms.live_order_count());
        LOG_INFO("{}", risk.summary());
    }
}

} // namespace depthos

int main() {
    using namespace depthos;
    
    // Initialize logging
    const char* log_level = std::getenv("LOG_LEVEL");
    Logger::init(log_level ? log_level : "info");
    
    LOG_INFO("DepthOS - Micro-Price Market Maker for Gate.io Futures");
    LOG_INFO("=======================================================");
    
    // Load environment
    load_environment();
    
    // Register signal handlers
    register_signals();
    
    try {
        // Create REST client
        RestClient client;
        
        // Bootstrap
        if (!bootstrap(client)) {
            LOG_ERROR("Bootstrap failed - aborting");
            return 1;
        }
        
        // Create WebSocket manager
        WSManager ws_mgr;
        
        // Create quoting engine
        QuotingEngine* qe = new QuotingEngine(client);
        
        LOG_INFO("Starting WebSocket connections …");
        ws_mgr.start();
        
        LOG_INFO("Waiting for initial BBO data …");
        std::this_thread::sleep_for(std::chrono::milliseconds(1500));
        
        LOG_INFO("Starting quoting engine …");
        qe->start();
        
        // Start heartbeat thread
        std::thread heartbeat_thread(heartbeat_loop);
        
        LOG_INFO("=== MARKET MAKER RUNNING ===  (CTRL-C to stop)");
        
        // Wait for shutdown signal
        while (!shutdown_requested) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        LOG_INFO("Shutdown signal received — stopping gracefully …");
        
        // Graceful teardown
        shutdown_requested = true;
        
        if (heartbeat_thread.joinable()) {
            heartbeat_thread.join();
        }
        
        qe->stop();
        delete qe;
        qe = nullptr;
        
        ws_mgr.stop();
        
        // Final risk summary
        LOG_INFO("Final risk state:\n{}", risk.summary());
        LOG_INFO("=== SHUTDOWN COMPLETE ===");
        
    } catch (const std::exception& e) {
        LOG_CRITICAL("Fatal error: {}", e.what());
        return 1;
    }
    
    return 0;
}
