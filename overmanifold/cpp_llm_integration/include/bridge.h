#ifndef BRIDGE_H
#define BRIDGE_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <optional>
#include <shared_mutex>

namespace llm_integration {

// Bridge operation types
enum class BridgeOperationType {
    DEPOSIT,
    WITHDRAW,
    TRANSFER,
    SWAP,
    LOCK,
    UNLOCK,
    CLAIM,
    APPROVE
};

// Bridge status
enum class BridgeStatus {
    PENDING,
    PROCESSING,
    COMPLETED,
    FAILED,
    REVERSED,
    TIMEOUT
};

// Bridge operation
struct BridgeOperation {
    std::string operation_id;
    BridgeOperationType operation_type;
    std::string from_chain;
    std::string to_chain;
    std::string from_address;
    std::string to_address;
    double amount;
    std::string token;
    std::chrono::system_clock::time_point timestamp;
    BridgeStatus status;
    uint64_t confirmations;
    uint64_t required_confirmations;
    double gas_used;
    double bridge_fee;
    std::map<std::string, std::string> metadata;
    
    BridgeOperation(BridgeOperationType type, const std::string& from_chain, const std::string& to_chain,
                    const std::string& from_address, const std::string& to_address,
                    double amount, const std::string& token);
    static std::string generate_operation_id(const std::string& from_chain, const std::string& to_chain,
                                             const std::string& from_address, double amount);
};

// Bridge pool
struct BridgePool {
    std::string pool_id;
    std::string token;
    std::string chain;
    double balance;
    double min_balance;
    double max_balance;
    double fee_rate;
    std::chrono::system_clock::time_point last_updated;
    
    BridgePool(const std::string& token, const std::string& chain, double balance, double fee_rate);
    static std::string generate_pool_id(const std::string& token, const std::string& chain);
};

// Bridge analysis result
struct BridgeAnalysis {
    std::string operation_type;
    double confidence;
    std::vector<std::string> recommended_route;
    uint64_t estimated_time_seconds;
    double estimated_cost;
    double estimated_fee;
    std::string slippage_risk;
    std::string security_risk;
    bool liquidity_available;
    uint64_t required_confirmations;
    std::string reasoning;
    std::vector<std::string> warnings;
    std::vector<std::string> optimization_suggestions;
};

// Bridge execution result
struct BridgeExecutionResult {
    bool success;
    std::string operation_id;
    double amount;
    double bridge_fee;
    double gas_used;
    double pool_balance;
};

// Bridge statistics
struct BridgeStatistics {
    uint64_t total_operations;
    uint64_t completed;
    uint64_t failed;
    uint64_t pending;
    double success_rate;
    double total_volume;
    double total_fees;
    std::map<std::string, uint64_t> operation_types;
    uint64_t total_pools;
    std::vector<std::string> supported_chains;
};

// LLM bridge analyzer
class LlmBridgeAnalyzer {
public:
    LlmBridgeAnalyzer(const std::string& openai_api_key = "");
    
    BridgeAnalysis analyze_bridge_operation(BridgeOperationType operation_type, const std::string& from_chain,
                                            const std::string& to_chain, double amount, const std::string& token,
                                            bool urgent);
    
    void set_openai_api_key(const std::string& api_key) { openai_api_key_ = api_key; }
    
private:
    std::string openai_api_key_;
    
    BridgeAnalysis analyze_with_llm(BridgeOperationType operation_type, const std::string& from_chain,
                                    const std::string& to_chain, double amount, const std::string& token, bool urgent);
    BridgeAnalysis analyze_fallback(BridgeOperationType operation_type, const std::string& from_chain,
                                    const std::string& to_chain, double amount, const std::string& token, bool urgent);
    std::string get_system_prompt() const;
};

// Custom Membra bridge
class CustomMembraBridge {
public:
    CustomMembraBridge(const std::string& openai_api_key = "");
    
    void initialize();
    BridgeOperation create_bridge_operation(BridgeOperationType operation_type, const std::string& from_chain,
                                           const std::string& to_chain, const std::string& from_address,
                                           const std::string& to_address, double amount, const std::string& token);
    BridgeExecutionResult execute_bridge_operation(const std::string& operation_id);
    BridgeExecutionResult deposit_to_overmanifold(const std::string& from_chain, const std::string& from_address,
                                                  const std::string& to_address, double amount, const std::string& token);
    BridgeExecutionResult withdraw_from_overmanifold(const std::string& to_chain, const std::string& from_address,
                                                     const std::string& to_address, double amount, const std::string& token);
    BridgeStatistics get_bridge_statistics() const;
    
    void set_openai_api_key(const std::string& api_key) { openai_api_key_ = api_key; }
    
private:
    std::string openai_api_key_;
    std::unique_ptr<LlmBridgeAnalyzer> bridge_analyzer_;
    
    mutable std::shared_mutex operations_mutex_;
    std::map<std::string, BridgeOperation> operations_;
    
    mutable std::shared_mutex pools_mutex_;
    std::map<std::string, BridgePool> pools_;
    
    mutable std::shared_mutex chain_configs_mutex_;
    std::map<std::string, std::map<std::string, std::string>> chain_configs_;
    
    std::string bridge_address_;
    double min_bridge_amount_;
    double max_bridge_amount_;
    double default_fee_rate_;
};

} // namespace llm_integration

#endif // BRIDGE_H