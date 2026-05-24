#include "config.hpp"
#include "logger.hpp"
#include <cstdlib>
#include <iostream>

namespace depthos {

MMConfig mm_config;
std::string API_KEY;
std::string API_SECRET;

void load_environment() {
    const char* key = std::getenv("GATE_API_KEY");
    const char* secret = std::getenv("GATE_API_SECRET");
    
    if (!key) {
        LOG_CRITICAL("GATE_API_KEY environment variable not set");
        std::exit(1);
    }
    
    if (!secret) {
        LOG_CRITICAL("GATE_API_SECRET environment variable not set");
        std::exit(1);
    }
    
    API_KEY = key;
    API_SECRET = secret;
    
    // Safety: dry_run defaults to true; only disable if LIVE_TRADING_CONFIRM=1 is set
    const char* live_confirm = std::getenv("LIVE_TRADING_CONFIRM");
    const char* dry_run = std::getenv("DRY_RUN");

    if (dry_run && (std::string(dry_run) == "0" || std::string(dry_run) == "false")) {
        if (live_confirm && std::string(live_confirm) == "1") {
            mm_config.dry_run = false;
            LOG_CRITICAL("LIVE TRADING ENABLED — DRY_RUN=0 and LIVE_TRADING_CONFIRM=1");
        } else {
            LOG_WARN("DRY_RUN=0 requested but LIVE_TRADING_CONFIRM not set to 1 — forcing dry_run");
            mm_config.dry_run = true;
        }
    } else {
        mm_config.dry_run = true;
        LOG_INFO("DRY_RUN mode enabled by default — no orders will be sent");
    }
}

} // namespace depthos
