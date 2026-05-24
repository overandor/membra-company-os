#include <iostream>
#include <cstring>
#include "consensus.hpp"

int main(int argc, char** argv) {
    std::cout << "╔══════════════════════════════════════════════════════════════╗" << std::endl;
    std::cout << "║  MEMBRA GENESIS NODE — C++ Core                             ║" << std::endl;
    std::cout << "║  Proof-of-Proof Consensus Engine                            ║" << std::endl;
    std::cout << "╚══════════════════════════════════════════════════════════════╝" << std::endl;
    
    const char* node_id = argc > 1 ? argv[1] : "genesis-001";
    
    void* genesis = membra::membra_genesis_create(node_id);
    if (!genesis) {
        std::cerr << "Failed to create genesis node" << std::endl;
        return 1;
    }
    
    std::cout << "Genesis node " << node_id << " created" << std::endl;
    std::cout << "Press Enter to run test, Ctrl+C to exit..." << std::endl;
    std::cin.get();
    
    // Test: Submit 100 transactions
    std::cout << "Submitting 100 test transactions..." << std::endl;
    
    for (int i = 0; i < 100; i++) {
        membra::Transaction tx{};
        tx.amount = 100;
        tx.nonce = static_cast<uint64_t>(i);
        tx.timestamp = static_cast<uint64_t>(time(nullptr));
        tx.tx_type = (i % 3 == 0) ? 0 : 1; // mix of prompts and inferences
        
        // Generate pseudo-hash
        for (int j = 0; j < 32; j++) {
            tx.tx_hash[j] = static_cast<uint8_t>((i * 7 + j * 13) % 256);
        }
        
        membra::membra_tx_submit(genesis, &tx);
    }
    
    uint64_t pool_size = membra::membra_tx_pool_size(genesis);
    std::cout << "Pool size: " << pool_size << std::endl;
    
    // Form batch and finalize
    if (pool_size > 0) {
        std::vector<membra::Transaction> txs;
        // In real impl, we'd drain from pool; for test, create inline
        for (int i = 0; i < 10; i++) {
            membra::Transaction tx{};
            tx.amount = 100;
            for (int j = 0; j < 32; j++) tx.tx_hash[j] = static_cast<uint8_t>(i + j);
            txs.push_back(tx);
        }
        
        void* batch = membra::membra_batch_form(genesis, txs.data(), txs.size());
        
        // Submit proofs from 3 agents
        for (int agent = 0; agent < 3; agent++) {
            membra::InferenceProof proof{};
            for (int j = 0; j < 32; j++) {
                proof.response_hash[j] = static_cast<uint8_t>(42); // All agree = consensus
                proof.prompt_hash[j] = static_cast<uint8_t>(j);
                proof.proof_hash[j] = static_cast<uint8_t>(agent + j);
            }
            proof.confidence = 0.95;
            proof.token_count = 10;
            membra::membra_proof_submit(genesis, batch, &proof);
        }
        
        bool consensus = membra::membra_consensus_check(genesis, batch);
        std::cout << "Consensus reached: " << (consensus ? "YES" : "NO") << std::endl;
        
        if (consensus) {
            membra::membra_batch_finalize(genesis, batch);
        }
    }
    
    uint64_t finalized = membra::membra_finalized_count(genesis);
    std::cout << "Finalized batches: " << finalized << std::endl;
    
    uint64_t total_tx = 0, total_tokens = 0;
    membra::membra_stats(genesis, &total_tx, &total_tokens, &finalized);
    std::cout << "Stats: tx=" << total_tx << " tokens=" << total_tokens << " finalized=" << finalized << std::endl;
    
    membra::membra_genesis_destroy(genesis);
    std::cout << "Genesis node shut down." << std::endl;
    
    return 0;
}
