#include "blockchain.h"
#include <sstream>
#include <iomanip>
#include <random>
#include <algorithm>
#include <cctype>
#include <openssl/sha.h>
#include <openssl/rand.h>
#include <iostream>

namespace llm_integration {

// Helper function for SHA256
std::string sha256(const std::string& input) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, input.c_str(), input.size());
    SHA256_Final(hash, &sha256);
    
    std::stringstream ss;
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    return ss.str();
}

// Transaction implementation
Transaction::Transaction(const std::string& from, const std::string& to, double amount,
                         TransactionType type, const std::string& data)
    : from_address(from), to_address(to), amount(amount), transaction_type(type), data(data),
      timestamp(std::chrono::system_clock::now()), status(TransactionStatus::PENDING),
      gas_limit(21000), gas_used(0), gas_price(0.00001), block_number(0), confirmation_count(0) {
    tx_id = generate_tx_id(from, to, amount);
}

std::string Transaction::generate_tx_id(const std::string& from, const std::string& to, double amount) {
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    std::string input = from + to + std::to_string(amount) + std::to_string(timestamp);
    return sha256(input);
}

// Block implementation
Block::Block(uint64_t block_number, const std::string& parent_hash, const std::string& validator,
             const std::vector<std::string>& transactions)
    : block_number(block_number), timestamp(std::chrono::system_clock::now()),
      transactions(transactions), parent_hash(parent_hash), validator(validator),
      gas_used(0), gas_limit(1000000) {
    block_hash = calculate_block_hash(block_number, parent_hash, transactions, validator);
}

std::string Block::calculate_block_hash(uint64_t block_number, const std::string& parent_hash,
                                        const std::vector<std::string>& transactions, const std::string& validator) {
    std::string txs_hash;
    for (const auto& tx : transactions) {
        txs_hash += tx;
    }
    std::string input = std::to_string(block_number) + parent_hash + txs_hash + validator;
    return sha256(input);
}

// Account implementation
Account::Account(const std::string& address, double balance)
    : address(address.empty() ? generate_address() : address), balance(balance), nonce(0),
      created_at(std::chrono::system_clock::now()) {
}

std::string Account::generate_address() {
    unsigned char random_bytes[20];
    if (RAND_bytes(random_bytes, sizeof(random_bytes)) != 1) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 255);
        for (int i = 0; i < 20; i++) {
            random_bytes[i] = static_cast<unsigned char>(dis(gen));
        }
    }
    
    std::stringstream hex_stream;
    for (int i = 0; i < 20; i++) {
        hex_stream << std::hex << std::setw(2) << std::setfill('0') << (int)random_bytes[i];
    }
    
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    
    std::string input = "overmanifold" + hex_stream.str() + std::to_string(timestamp);
    std::string hash = sha256(input);
    
    return "0x" + hash.substr(0, 40);
}

// LlmTransactionValidator implementation
LlmTransactionValidator::LlmTransactionValidator(const std::string& openai_api_key)
    : openai_api_key_(openai_api_key) {
}

ValidationResult LlmTransactionValidator::validate_transaction(const Transaction& transaction,
                                                                double sender_balance, uint64_t sender_nonce) {
    if (!openai_api_key_.empty()) {
        return validate_with_llm(transaction, sender_balance, sender_nonce);
    } else {
        return validate_fallback(transaction, sender_balance, sender_nonce);
    }
}

ValidationResult LlmTransactionValidator::validate_with_llm(const Transaction& transaction,
                                                             double sender_balance, uint64_t sender_nonce) {
    std::cout << "[Blockchain Validator] Would validate with LLM" << std::endl;
    return validate_fallback(transaction, sender_balance, sender_nonce);
}

ValidationResult LlmTransactionValidator::validate_fallback(const Transaction& transaction,
                                                             double sender_balance, uint64_t sender_nonce) {
    ValidationResult result;
    result.is_valid = true;
    result.confidence = 0.85;
    result.reasoning = "Rule-based validation";
    result.gas_estimate = 21000;
    
    // Validate amount
    bool amount_valid = transaction.amount > 0.0 && transaction.amount <= 1000000.0;
    result.validation_checks["amount_valid"] = amount_valid;
    if (!amount_valid) {
        result.errors.push_back("Invalid amount");
        result.is_valid = false;
    }
    
    // Validate balance
    bool balance_sufficient = sender_balance >= transaction.amount;
    result.validation_checks["balance_sufficient"] = balance_sufficient;
    if (!balance_sufficient) {
        result.errors.push_back("Insufficient balance");
        result.is_valid = false;
    }
    
    // Validate nonce
    bool nonce_valid = transaction.nonce == sender_nonce;
    result.validation_checks["nonce_valid"] = nonce_valid;
    if (!nonce_valid) {
        result.errors.push_back("Invalid nonce");
        result.is_valid = false;
    }
    
    // Validate addresses
    result.validation_checks["sender_valid"] = validate_address(transaction.from_address);
    result.validation_checks["recipient_valid"] = validate_address(transaction.to_address);
    
    if (!validate_address(transaction.from_address)) {
        result.errors.push_back("Invalid sender address");
        result.is_valid = false;
    }
    if (!validate_address(transaction.to_address)) {
        result.errors.push_back("Invalid recipient address");
        result.is_valid = false;
    }
    
    // Validate gas
    bool gas_sufficient = transaction.gas_limit >= 21000;
    result.validation_checks["gas_sufficient"] = gas_sufficient;
    if (!gas_sufficient) {
        result.warnings.push_back("Low gas limit");
    }
    
    return result;
}

bool LlmTransactionValidator::validate_address(const std::string& address) const {
    return address.size() == 42 && address.substr(0, 2) == "0x";
}

std::string LlmTransactionValidator::get_system_prompt() const {
    return R"(You are an intelligent transaction validator for Overmanifold Protocol.)";
}

// CustomBlockchain implementation
CustomBlockchain::CustomBlockchain(const std::string& openai_api_key, const std::string& chain_id)
    : chain_id_(chain_id), openai_api_key_(openai_api_key),
      validator_(std::make_unique<LlmTransactionValidator>(openai_api_key)),
      block_number_(0), miner_address_("0x0000000000000000000000000000000000000001") {
}

void CustomBlockchain::initialize() {
    // Create genesis block
    Block genesis_block(0, std::string(64, '0'), "genesis", {});
    
    {
        std::unique_lock<std::shared_mutex> lock(blocks_mutex_);
        blocks_[0] = genesis_block;
    }
    
    // Create genesis accounts
    {
        std::unique_lock<std::shared_mutex> lock(accounts_mutex_);
        accounts_["0x0000000000000000000000000000000000000001"] = Account("", 1000000.0);
        accounts_["0x0000000000000000000000000000000000000002"] = Account("", 1000000.0);
        accounts_["0x0000000000000000000000000000000000000003"] = Account("", 1000000.0);
    }
    
    {
        std::unique_lock<std::mutex> lock(block_number_mutex_);
        block_number_ = 1;
    }
    
    std::cout << "[Blockchain] Genesis block and accounts initialized" << std::endl;
}

double CustomBlockchain::get_balance(const std::string& address) const {
    std::shared_lock<std::shared_mutex> lock(accounts_mutex_);
    auto it = accounts_.find(address);
    return it != accounts_.end() ? it->second.balance : 0.0;
}

Transaction CustomBlockchain::create_transaction(const std::string& from_address, const std::string& to_address,
                                                  double amount, TransactionType transaction_type, const std::string& data) {
    return Transaction(from_address, to_address, amount, transaction_type, data);
}

std::string CustomBlockchain::submit_transaction(const Transaction& transaction) {
    std::string tx_id = transaction.tx_id;
    
    {
        std::unique_lock<std::shared_mutex> lock(transactions_mutex_);
        transactions_[tx_id] = transaction;
    }
    
    {
        std::unique_lock<std::mutex> lock(pending_mutex_);
        pending_transactions_.push_back(tx_id);
    }
    
    std::cout << "[Blockchain] Transaction submitted: " << tx_id << std::endl;
    return tx_id;
}

ExecutionResult CustomBlockchain::validate_and_execute_transaction(const std::string& tx_id) {
    std::shared_lock<std::shared_mutex> tlock(transactions_mutex_);
    auto it = transactions_.find(tx_id);
    if (it == transactions_.end()) {
        return ExecutionResult{false, tx_id, "Transaction not found", 0, 0.0};
    }
    
    Transaction transaction = it->second;
    tlock.unlock();
    
    std::shared_lock<std::shared_mutex> alock(accounts_mutex_);
    auto sender_it = accounts_.find(transaction.from_address);
    if (sender_it == accounts_.end()) {
        return ExecutionResult{false, tx_id, "Sender account not found", 0, 0.0};
    }
    
    double sender_balance = sender_it->second.balance;
    uint64_t sender_nonce = sender_it->second.nonce;
    alock.unlock();
    
    auto validation = validator_->validate_transaction(transaction, sender_balance, sender_nonce);
    
    if (!validation.is_valid) {
        std::unique_lock<std::shared_mutex> lock(transactions_mutex_);
        transactions_[tx_id].status = TransactionStatus::FAILED;
        return ExecutionResult{false, tx_id, "Transaction validation failed", 0, 0.0};
    }
    
    // Execute transaction
    std::unique_lock<std::shared_mutex> lock(accounts_mutex_);
    accounts_[transaction.from_address].balance -= transaction.amount;
    accounts_[transaction.from_address].nonce += 1;
    accounts_[transaction.to_address].balance += transaction.amount;
    
    transaction.status = TransactionStatus::EXECUTED;
    transaction.gas_used = validation.gas_estimate;
    
    double tx_cost = transaction.gas_used * transaction.gas_price;
    accounts_[transaction.from_address].balance -= tx_cost;
    
    // Remove from pending
    {
        std::unique_lock<std::mutex> plock(pending_mutex_);
        auto it = std::find(pending_transactions_.begin(), pending_transactions_.end(), tx_id);
        if (it != pending_transactions_.end()) {
            pending_transactions_.erase(it);
        }
    }
    
    {
        std::unique_lock<std::shared_mutex> tlock(transactions_mutex_);
        transactions_[tx_id] = transaction;
    }
    
    std::cout << "[Blockchain] Transaction executed: " << tx_id << std::endl;
    
    return ExecutionResult{true, tx_id, std::nullopt, transaction.gas_used, tx_cost};
}

Block CustomBlockchain::produce_block(const std::string& validator_address) {
    std::string validator = validator_address.empty() ? miner_address_ : validator_address;
    
    std::vector<std::string> pending;
    {
        std::unique_lock<std::mutex> lock(pending_mutex_);
        pending = pending_transactions_;
    }
    
    std::vector<std::string> selected_txs;
    if (!pending.empty()) {
        // Simple selection - take first 10
        selected_txs.assign(pending.begin(), pending.begin() + std::min(size_t(10), pending.size()));
    }
    
    uint64_t last_block_number;
    std::string parent_hash;
    {
        std::unique_lock<std::mutex> lock(block_number_mutex_);
        last_block_number = block_number_ - 1;
    }
    
    {
        std::shared_lock<std::shared_mutex> lock(blocks_mutex_);
        auto it = blocks_.find(last_block_number);
        if (it != blocks_.end()) {
            parent_hash = it->second.block_hash;
        } else {
            parent_hash = std::string(64, '0');
        }
    }
    
    uint64_t current_block_number;
    {
        std::unique_lock<std::mutex> lock(block_number_mutex_);
        current_block_number = block_number_;
        block_number_++;
    }
    
    Block new_block(current_block_number, parent_hash, validator, selected_txs);
    
    // Execute transactions
    for (const auto& tx_id : selected_txs) {
        try {
            validate_and_execute_transaction(tx_id);
        } catch (const std::exception& e) {
            std::cerr << "[Blockchain] Failed to execute transaction " << tx_id << ": " << e.what() << std::endl;
        }
    }
    
    {
        std::unique_lock<std::shared_mutex> lock(blocks_mutex_);
        blocks_[current_block_number] = new_block;
    }
    
    // Reward validator
    double block_reward = 2.0;
    std::unique_lock<std::shared_mutex> lock(accounts_mutex_);
    accounts_[validator].balance += block_reward;
    
    std::cout << "[Blockchain] Block " << new_block.block_number << " produced with " 
              << selected_txs.size() << " transactions" << std::endl;
    
    return new_block;
}

ChainStats CustomBlockchain::get_chain_stats() const {
    std::shared_lock<std::shared_mutex> tlock(transactions_mutex_);
    uint64_t total_transactions = transactions_.size();
    tlock.unlock();
    
    std::shared_lock<std::shared_mutex> alock(accounts_mutex_);
    uint64_t total_accounts = accounts_.size();
    double total_supply = 0.0;
    for (const auto& [addr, acc] : accounts_) {
        total_supply += acc.balance;
    }
    alock.unlock();
    
    std::unique_lock<std::mutex> plock(pending_mutex_);
    uint64_t pending_transactions = pending_transactions_.size();
    plock.unlock();
    
    std::unique_lock<std::mutex> block_lock(block_number_mutex_);
    uint64_t block_number = block_number_;
    block_lock.unlock();
    
    std::shared_lock<std::shared_mutex> blocks_lock(blocks_mutex_);
    std::optional<std::string> latest_block_hash;
    auto it = blocks_.find(block_number - 1);
    if (it != blocks_.end()) {
        latest_block_hash = it->second.block_hash;
    }
    
    return ChainStats{
        chain_id_,
        block_number,
        total_transactions,
        pending_transactions,
        total_accounts,
        total_supply,
        latest_block_hash,
        1,
        15
    };
}

} // namespace llm_integration