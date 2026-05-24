#ifndef BLOCKCHAIN_H
#define BLOCKCHAIN_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <optional>
#include <mutex>
#include <shared_mutex>

namespace llm_integration {

// Transaction types
enum class TransactionType {
    PAYMENT,
    VERIFICATION,
    REGISTRATION,
    SPONSORSHIP,
    GOVERNANCE,
    REWARD,
    SMART_CONTRACT
};

// Transaction status
enum class TransactionStatus {
    PENDING,
    VALIDATED,
    EXECUTED,
    CONFIRMED,
    FAILED,
    REVERTED
};

// Transaction structure
struct Transaction {
    std::string tx_id;
    std::string from_address;
    std::string to_address;
    double amount;
    TransactionType transaction_type;
    std::chrono::system_clock::time_point timestamp;
    TransactionStatus status;
    uint64_t gas_limit;
    uint64_t gas_used;
    double gas_price;
    std::string data;
    std::string signature;
    uint64_t block_number;
    uint64_t confirmation_count;
    std::map<std::string, std::string> metadata;
    
    Transaction(const std::string& from, const std::string& to, double amount,
                TransactionType type, const std::string& data);
    static std::string generate_tx_id(const std::string& from, const std::string& to, double amount);
};

// Block structure
struct Block {
    uint64_t block_number;
    std::chrono::system_clock::time_point timestamp;
    std::vector<std::string> transactions;
    std::string parent_hash;
    std::string block_hash;
    std::string state_root;
    std::string validator;
    uint64_t gas_used;
    uint64_t gas_limit;
    
    Block(uint64_t block_number, const std::string& parent_hash, const std::string& validator,
          const std::vector<std::string>& transactions);
    static std::string calculate_block_hash(uint64_t block_number, const std::string& parent_hash,
                                            const std::vector<std::string>& transactions, const std::string& validator);
};

// Account structure
struct Account {
    std::string address;
    double balance;
    uint64_t nonce;
    std::map<std::string, std::string> storage;
    std::string code;
    std::chrono::system_clock::time_point created_at;
    
    Account(const std::string& address = "", double balance = 0.0);
    static std::string generate_address();
};

// Validation result
struct ValidationResult {
    bool is_valid;
    double confidence;
    std::map<std::string, bool> validation_checks;
    std::vector<std::string> errors;
    std::vector<std::string> warnings;
    std::string reasoning;
    uint64_t gas_estimate;
};

// Execution result
struct ExecutionResult {
    bool success;
    std::string tx_id;
    std::optional<std::string> error;
    uint64_t gas_used;
    double tx_cost;
};

// Chain statistics
struct ChainStats {
    std::string chain_id;
    uint64_t block_number;
    uint64_t total_transactions;
    uint64_t pending_transactions;
    uint64_t total_accounts;
    double total_supply;
    std::optional<std::string> latest_block_hash;
    uint64_t difficulty;
    uint64_t block_time;
};

// LLM transaction validator
class LlmTransactionValidator {
public:
    LlmTransactionValidator(const std::string& openai_api_key = "");
    
    ValidationResult validate_transaction(const Transaction& transaction, double sender_balance, uint64_t sender_nonce);
    
    void set_openai_api_key(const std::string& api_key) { openai_api_key_ = api_key; }
    
private:
    std::string openai_api_key_;
    
    ValidationResult validate_with_llm(const Transaction& transaction, double sender_balance, uint64_t sender_nonce);
    ValidationResult validate_fallback(const Transaction& transaction, double sender_balance, uint64_t sender_nonce);
    bool validate_address(const std::string& address) const;
    std::string get_system_prompt() const;
};

// Custom blockchain implementation
class CustomBlockchain {
public:
    CustomBlockchain(const std::string& openai_api_key = "", const std::string& chain_id = "overmanifold-1");
    
    void initialize();
    double get_balance(const std::string& address) const;
    Transaction create_transaction(const std::string& from_address, const std::string& to_address,
                                   double amount, TransactionType transaction_type, const std::string& data);
    std::string submit_transaction(const Transaction& transaction);
    ExecutionResult validate_and_execute_transaction(const std::string& tx_id);
    Block produce_block(const std::string& validator_address = "");
    ChainStats get_chain_stats() const;
    
    void set_openai_api_key(const std::string& api_key) { openai_api_key_ = api_key; }
    
private:
    std::string chain_id_;
    std::string openai_api_key_;
    std::unique_ptr<LlmTransactionValidator> validator_;
    
    mutable std::shared_mutex accounts_mutex_;
    std::map<std::string, Account> accounts_;
    
    mutable std::shared_mutex blocks_mutex_;
    std::map<uint64_t, Block> blocks_;
    
    mutable std::shared_mutex transactions_mutex_;
    std::map<std::string, Transaction> transactions_;
    
    mutable std::mutex pending_mutex_;
    std::vector<std::string> pending_transactions_;
    
    mutable std::mutex block_number_mutex_;
    uint64_t block_number_;
    
    std::string miner_address_;
};

} // namespace llm_integration

#endif // BLOCKCHAIN_H