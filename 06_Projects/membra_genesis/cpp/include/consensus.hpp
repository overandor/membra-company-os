#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include <array>
#include <memory>

namespace membra {

constexpr size_t HASH_SIZE = 32;
constexpr size_t MAX_BATCH = 10000;
constexpr double CONSENSUS_THRESHOLD = 0.67;

using Hash = std::array<uint8_t, HASH_SIZE>;

struct Transaction {
    Hash tx_hash;
    Hash from;
    Hash to;
    uint64_t amount;
    uint64_t nonce;
    uint64_t timestamp;
    uint8_t tx_type; // 0=Prompt, 1=Inference, 2=Response, 3=ConsensusVote
    char data[256];
};

struct InferenceProof {
    Hash prompt_hash;
    Hash response_hash;
    Hash proof_hash;  // hash of LLM output = proof
    uint64_t token_count;
    double confidence;
    uint64_t timestamp;
};

struct ConsensusBatch {
    Hash root_hash;
    uint64_t tx_count;
    uint64_t timestamp;
    bool finalized;
    std::vector<InferenceProof> proofs;
};

// C API for FFI
extern "C" {
    // Genesis
    void* membra_genesis_create(const char* node_id);
    void membra_genesis_destroy(void* genesis);
    
    // Transaction processing (hot path)
    bool membra_tx_verify(void* genesis, const Transaction* tx);
    void membra_tx_submit(void* genesis, const Transaction* tx);
    uint64_t membra_tx_pool_size(void* genesis);
    
    // Consensus
    void* membra_batch_form(void* genesis, const Transaction* txs, size_t count);
    void membra_proof_submit(void* genesis, void* batch, const InferenceProof* proof);
    bool membra_consensus_check(void* genesis, void* batch);
    void membra_batch_finalize(void* genesis, void* batch);
    uint64_t membra_finalized_count(void* genesis);
    
    // State
    uint64_t membra_balance_get(void* genesis, const Hash* address);
    void membra_balance_credit(void* genesis, const Hash* address, uint64_t amount);
    bool membra_balance_debit(void* genesis, const Hash* address, uint64_t amount);
    
    // Merkle
    void membra_merkle_root(const Hash* leaves, size_t count, Hash* out);
    
    // Stats
    void membra_stats(void* genesis, uint64_t* total_tx, uint64_t* total_tokens, uint64_t* finalized);
}

} // namespace membra
