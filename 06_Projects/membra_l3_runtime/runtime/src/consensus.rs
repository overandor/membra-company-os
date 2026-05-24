use serde::{Deserialize, Serialize};
use sha3::{Digest, Keccak256};
use std::collections::HashMap;
use tokio::sync::RwLock;
use std::sync::Arc;
use tracing::{info, debug};

use crate::transaction::{Transaction, TxType};

/// Proof-of-Proof Consensus:
/// Every inference output is hashed → this hash IS proof.
/// Multiple agents compare proof hashes → agreement IS consensus.
/// No separate validator set needed — the LLM itself validates.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsensusBatch {
    pub batch_id: String,
    pub root_hash: String,
    pub tx_count: u64,
    pub proofs: Vec<InferenceProof>,
    pub timestamp: i64,
    pub finalized: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceProof {
    pub agent_id: String,
    pub prompt_hash: String,
    pub response_hash: String,
    pub confidence: f64,
    pub timestamp: i64,
}

pub struct ConsensusEngine {
    batches: Arc<RwLock<Vec<ConsensusBatch>>>,
    current_votes: Arc<RwLock<HashMap<String, Vec<InferenceProof>>>>,
    threshold: f64, // 2/3 = 0.67
}

impl ConsensusEngine {
    pub fn new() -> Self {
        Self {
            batches: Arc::new(RwLock::new(Vec::new())),
            current_votes: Arc::new(RwLock::new(HashMap::new())),
            threshold: 0.67,
        }
    }
    
    /// Form a batch from transactions and compute Merkle root
    pub async fn form_batch(&self, txs: Vec<Transaction>) -> ConsensusBatch {
        let leaves: Vec<String> = txs.iter().map(|tx| tx.tx_hash.clone()).collect();
        let root = Self::merkle_root(&leaves);
        
        ConsensusBatch {
            batch_id: format!("batch-{}", uuid::Uuid::new_v4()),
            root_hash: root,
            tx_count: txs.len() as u64,
            proofs: Vec::new(),
            timestamp: chrono::Utc::now().timestamp_millis(),
            finalized: false,
        }
    }
    
    /// Submit a proof from an agent's LLM inference
    pub async fn submit_proof(&self, batch_id: &str, proof: InferenceProof) {
        let mut votes = self.current_votes.write().await;
        votes.entry(batch_id.to_string())
            .or_insert_with(Vec::new)
            .push(proof);
    }
    
    /// Check if batch has reached 2/3 consensus
    pub async fn check_consensus(&self, batch_id: &str) -> bool {
        let votes = self.current_votes.read().await;
        let proofs = match votes.get(batch_id) {
            Some(p) if p.len() >= 3 => p,
            _ => return false,
        };
        
        // Count agreement on response hashes
        let mut hash_counts: HashMap<String, u32> = HashMap::new();
        for proof in proofs {
            *hash_counts.entry(proof.response_hash.clone()).or_insert(0) += 1;
        }
        
        let total = proofs.len() as f64;
        for (hash, count) in hash_counts {
            let ratio = count as f64 / total;
            if ratio >= self.threshold {
                debug!("Consensus reached on hash {} with {} votes", &hash[..16], count);
                return true;
            }
        }
        
        false
    }
    
    /// Finalize a batch and add to chain
    pub async fn finalize_batch(&self, mut batch: ConsensusBatch) {
        batch.finalized = true;
        let mut batches = self.batches.write().await;
        batches.push(batch);
        info!("Batch finalized. Total finalized: {}", batches.len());
    }
    
    pub async fn finalized_count(&self) -> usize {
        let batches = self.batches.read().await;
        batches.len()
    }
    
    fn merkle_root(leaves: &[String]) -> String {
        if leaves.is_empty() {
            return hex::encode(Keccak256::digest(b"empty"));
        }
        
        let mut hashes: Vec<Vec<u8>> = leaves.iter()
            .map(|s| hex::decode(s).unwrap_or_default())
            .collect();
        
        while hashes.len() > 1 {
            let mut next_level = Vec::new();
            for i in (0..hashes.len()).step_by(2) {
                let left = &hashes[i];
                let right = if i + 1 < hashes.len() { &hashes[i + 1] } else { left };
                let mut hasher = Keccak256::new();
                hasher.update(left);
                hasher.update(right);
                next_level.push(hasher.finalize().to_vec());
            }
            hashes = next_level;
        }
        
        hex::encode(&hashes[0])
    }
}
