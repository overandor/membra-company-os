#pragma once

#include <string>
#include <vector>
#include <memory>
#include <thread>
#include <atomic>
#include <condition_variable>
#include <unordered_map>
#include <mutex>
#include "config.hpp"

namespace depthos {

// Forward declarations
class RestClient;
class OrderBook;
struct ContractSpec;

// Quoting engine - core market-making logic
class QuotingEngine {
public:
    explicit QuotingEngine(RestClient& client);
    ~QuotingEngine();
    
    void start();
    void stop();
    
    // Signal BBO change (called by WS dispatcher)
    static void signal_bbo_change(const std::string& contract);
    
private:
    RestClient& client_;
    std::atomic<bool> running_;
    std::vector<std::thread> threads_;
    
    // Per-contract BBO events
    static std::unordered_map<std::string, std::condition_variable*> bbo_events_;
    static std::unordered_map<std::string, std::mutex> bbo_mutexes_;
    
    void quote_loop(const std::string& contract);
    void evaluate_and_quote(
        const std::string& contract,
        const ContractSpec& spec,
        OrderBook& ob
    );
};

// Global engine instance
extern QuotingEngine* engine;

} // namespace depthos
