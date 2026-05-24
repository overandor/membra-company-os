#include "consensus.hpp"
#include <cstring>
#include <unordered_map>
#include <vector>
#include <mutex>
#include <shared_mutex>

// Simple SHA3-256 (keccak) - production would use OpenSSL or libsodium
extern "C" {
    void sha3_256(const uint8_t* data, size_t len, uint8_t out[32]);
}

namespace membra {

class GenesisNode {
public:
    std::string node_id;
    std::vector<Transaction> pending;
    std::vector<ConsensusBatch> finalized;
    std::unordered_map<std::string, uint64_t> balances;
    std::shared_mutex balance_mutex;
    std::mutex pending_mutex;
    uint64_t total_tx = 0;
    uint64_t total_tokens = 0;
    
    GenesisNode(const std::string& id) : node_id(id) {}
};

// FFI Implementation
extern "C" {

void* membra_genesis_create(const char* node_id) {
    return new GenesisNode(node_id ? node_id : "genesis");
}

void membra_genesis_destroy(void* genesis) {
    delete static_cast<GenesisNode*>(genesis);
}

bool membra_tx_verify(void* genesis, const Transaction* tx) {
    if (!genesis || !tx) return false;
    // Verify tx hash is valid keccak
    uint8_t computed[32];
    sha3_256(reinterpret_cast<const uint8_t*>(tx), sizeof(Transaction) - 32, computed);
    return std::memcmp(computed, tx->tx_hash.data(), 32) == 0;
}

void membra_tx_submit(void* genesis, const Transaction* tx) {
    auto* node = static_cast<GenesisNode*>(genesis);
    std::lock_guard<std::mutex> lock(node->pending_mutex);
    node->pending.push_back(*tx);
    node->total_tx++;
    if (tx->tx_type == 1) { // Inference
        node->total_tokens++;
    }
}

uint64_t membra_tx_pool_size(void* genesis) {
    auto* node = static_cast<GenesisNode*>(genesis);
    std::lock_guard<std::mutex> lock(node->pending_mutex);
    return node->pending.size();
}

void* membra_batch_form(void* genesis, const Transaction* txs, size_t count) {
    auto* node = static_cast<GenesisNode*>(genesis);
    auto* batch = new ConsensusBatch();
    
    std::vector<Hash> leaves;
    for (size_t i = 0; i < count && i < MAX_BATCH; i++) {
        leaves.push_back(txs[i].tx_hash);
    }
    
    membra_merkle_root(leaves.data(), leaves.size(), &batch->root_hash);
    batch->tx_count = count;
    batch->timestamp = static_cast<uint64_t>(time(nullptr));
    batch->finalized = false;
    
    return batch;
}

void membra_proof_submit(void* genesis, void* batch, const InferenceProof* proof) {
    auto* b = static_cast<ConsensusBatch*>(batch);
    if (b && proof) {
        b->proofs.push_back(*proof);
    }
}

bool membra_consensus_check(void* genesis, void* batch) {
    auto* b = static_cast<ConsensusBatch*>(batch);
    if (!b || b->proofs.size() < 3) return false;
    
    // Count agreement on response_hash
    std::unordered_map<std::string, uint32_t> hash_counts;
    for (const auto& proof : b->proofs) {
        std::string key(reinterpret_cast<const char*>(proof.response_hash.data()), 32);
        hash_counts[key]++;
    }
    
    uint32_t max_count = 0;
    for (const auto& [hash, count] : hash_counts) {
        if (count > max_count) max_count = count;
    }
    
    double ratio = static_cast<double>(max_count) / b->proofs.size();
    return ratio >= CONSENSUS_THRESHOLD;
}

void membra_batch_finalize(void* genesis, void* batch) {
    auto* node = static_cast<GenesisNode*>(genesis);
    auto* b = static_cast<ConsensusBatch*>(batch);
    if (b) {
        b->finalized = true;
        {
            std::lock_guard<std::mutex> lock(node->pending_mutex);
            node->finalized.push_back(*b);
        }
        delete b;
    }
}

uint64_t membra_finalized_count(void* genesis) {
    auto* node = static_cast<GenesisNode*>(genesis);
    std::lock_guard<std::mutex> lock(node->pending_mutex);
    return node->finalized.size();
}

uint64_t membra_balance_get(void* genesis, const Hash* address) {
    auto* node = static_cast<GenesisNode*>(genesis);
    std::shared_lock<std::shared_mutex> lock(node->balance_mutex);
    std::string key(reinterpret_cast<const char*>(address->data()), 32);
    auto it = node->balances.find(key);
    return it != node->balances.end() ? it->second : 0;
}

void membra_balance_credit(void* genesis, const Hash* address, uint64_t amount) {
    auto* node = static_cast<GenesisNode*>(genesis);
    std::unique_lock<std::shared_mutex> lock(node->balance_mutex);
    std::string key(reinterpret_cast<const char*>(address->data()), 32);
    node->balances[key] += amount;
}

bool membra_balance_debit(void* genesis, const Hash* address, uint64_t amount) {
    auto* node = static_cast<GenesisNode*>(genesis);
    std::unique_lock<std::shared_mutex> lock(node->balance_mutex);
    std::string key(reinterpret_cast<const char*>(address->data()), 32);
    auto it = node->balances.find(key);
    if (it != node->balances.end() && it->second >= amount) {
        it->second -= amount;
        return true;
    }
    return false;
}

void membra_merkle_root(const Hash* leaves, size_t count, Hash* out) {
    if (count == 0) {
        std::memset(out->data(), 0, 32);
        return;
    }
    
    std::vector<Hash> current;
    for (size_t i = 0; i < count; i++) {
        current.push_back(leaves[i]);
    }
    
    while (current.size() > 1) {
        std::vector<Hash> next;
        for (size_t i = 0; i < current.size(); i += 2) {
            uint8_t combined[64];
            std::memcpy(combined, current[i].data(), 32);
            if (i + 1 < current.size()) {
                std::memcpy(combined + 32, current[i + 1].data(), 32);
            } else {
                std::memcpy(combined + 32, current[i].data(), 32);
            }
            Hash h;
            sha3_256(combined, 64, h.data());
            next.push_back(h);
        }
        current = std::move(next);
    }
    
    *out = current[0];
}

void membra_stats(void* genesis, uint64_t* total_tx, uint64_t* total_tokens, uint64_t* finalized) {
    auto* node = static_cast<GenesisNode*>(genesis);
    if (total_tx) *total_tx = node->total_tx;
    if (total_tokens) *total_tokens = node->total_tokens;
    if (finalized) *finalized = node->finalized.size();
}

} // extern "C"

} // namespace membra

// Minimal SHA3-256 implementation for standalone compilation
// Production: replace with OpenSSL EVP_sha3_256()
extern "C" void sha3_256(const uint8_t* data, size_t len, uint8_t out[32]) {
    // Stub: zero-fill for compilation
    // Real implementation would use keccak/SHA3 library
    for (size_t i = 0; i < len && i < 32; i++) {
        out[i] = data[i] ^ static_cast<uint8_t>(i);
    }
    for (size_t i = len; i < 32; i++) {
        out[i] = static_cast<uint8_t>(i);
    }
}
