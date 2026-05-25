use poi_core::{ProofOfInference, SamplerState, KVCommitment, RuntimeFingerprint, HardwareAttestation};
use dashmap::DashMap;
use parking_lot::RwLock;
use ed25519_dalek::{SigningKey, Signer};
use std::sync::Arc;
use std::collections::HashMap;
use chrono::{DateTime, Utc};

/// PoI Network: custom blockchain for inference proofs
pub struct PoiNetwork {
    /// Chain state
    state: Arc<RwLock<ChainState>>,
    /// Mempool for pending proofs
    mempool: Arc<DashMap<String, ProofOfInference>>,
    /// Validator keypair
    validator_keypair: SigningKey,
    /// Block time in seconds
    block_time: u64,
}

#[derive(Debug, Clone)]
pub struct ChainState {
    pub height: u64,
    pub blocks: HashMap<u64, Block>,
    pub proof_index: HashMap<String, u64>,  // inference_id -> block height
    pub model_registry: HashMap<String, ModelInfo>,
}

#[derive(Debug, Clone)]
pub struct Block {
    pub height: u64,
    pub timestamp: DateTime<Utc>,
    pub previous_hash: [u8; 32],
    pub proofs: Vec<ProofOfInference>,
    pub validator: String,
    pub signature: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct ModelInfo {
    pub cid: String,
    pub name: String,
    pub context_length: u32,
    pub quantization: String,
    pub registered_at: DateTime<Utc>,
}

impl PoiNetwork {
    pub fn new(validator_keypair: SigningKey, block_time: u64) -> Self {
        let genesis = Self::create_genesis();
        let mut blocks = HashMap::new();
        blocks.insert(0, genesis);
        
        let state = ChainState {
            height: 0,
            blocks,
            proof_index: HashMap::new(),
            model_registry: HashMap::new(),
        };
        
        Self {
            state: Arc::new(RwLock::new(state)),
            mempool: Arc::new(DashMap::new()),
            validator_keypair,
            block_time,
        }
    }
    
    fn create_genesis() -> Block {
        Block {
            height: 0,
            timestamp: Utc::now(),
            previous_hash: [0u8; 32],
            proofs: Vec::new(),
            validator: "genesis".to_string(),
            signature: Vec::new(),
        }
    }
    
    /// Submit a proof to the mempool
    pub fn submit_proof(&self, proof: ProofOfInference) -> Result<(), String> {
        // Validate proof structure
        if proof.token_count == 0 {
            return Err("Empty token sequence".to_string());
        }
        
        // Check for duplicates
        if self.mempool.contains_key(&proof.inference_id) {
            return Err("Proof already in mempool".to_string());
        }
        
        self.mempool.insert(proof.inference_id.clone(), proof);
        Ok(())
    }
    
    /// Create a new block from mempool
    pub fn create_block(&self) -> Result<Block, String> {
        let state = self.state.read();
        let height = state.height + 1;
        let previous_block = state.blocks.get(&(height - 1)).ok_or("No previous block")?;
        let previous_hash = Self::compute_block_hash(previous_block);
        drop(state);
        
        // Collect proofs from mempool
        let proofs: Vec<ProofOfInference> = self.mempool
            .iter()
            .map(|entry| entry.value().clone())
            .take(100)  // Max 100 proofs per block
            .collect();
        
        let mut block = Block {
            height,
            timestamp: Utc::now(),
            previous_hash,
            proofs,
            validator: hex::encode(self.validator_keypair.verifying_key().to_bytes()),
            signature: Vec::new(),
        };
        
        // Sign block
        let block_hash = Self::compute_block_hash(&block);
        let signature = self.validator_keypair.sign(&block_hash);
        block.signature = signature.to_bytes().to_vec();
        
        Ok(block)
    }
    
    /// Add a block to the chain
    pub fn add_block(&self, block: Block) -> Result<(), String> {
        let mut state = self.state.write();
        
        // Verify block height
        if block.height != state.height + 1 {
            return Err("Invalid block height".to_string());
        }
        
        // Verify previous hash
        let previous_block = state.blocks.get(&(block.height - 1)).ok_or("No previous block")?;
        let expected_hash = Self::compute_block_hash(previous_block);
        if block.previous_hash != expected_hash {
            return Err("Invalid previous hash".to_string());
        }
        
        // Verify block signature
        let block_hash = Self::compute_block_hash(&block);
        // TODO: verify signature with validator public key
        
        // Add block
        state.blocks.insert(block.height, block.clone());
        state.height = block.height;
        
        // Index proofs
        for proof in &block.proofs {
            state.proof_index.insert(proof.inference_id.clone(), block.height);
            self.mempool.remove(&proof.inference_id);
        }
        
        Ok(())
    }
    
    /// Register a model
    pub fn register_model(&self, cid: String, name: String, context_length: u32, quantization: String) {
        let mut state = self.state.write();
        state.model_registry.insert(cid.clone(), ModelInfo {
            cid,
            name,
            context_length,
            quantization,
            registered_at: Utc::now(),
        });
    }
    
    /// Get a proof by inference ID
    pub fn get_proof(&self, inference_id: &str) -> Option<ProofOfInference> {
        let state = self.state.read();
        let height = state.proof_index.get(inference_id)?;
        let block = state.blocks.get(height)?;
        block.proofs.iter().find(|p| p.inference_id == inference_id).cloned()
    }
    
    /// Get current chain height
    pub fn height(&self) -> u64 {
        self.state.read().height
    }
    
    fn compute_block_hash(block: &Block) -> [u8; 32] {
        use sha2::{Digest, Sha256};
        let data = format!("{}{}{}{}{}", 
            block.height,
            block.timestamp.timestamp(),
            hex::encode(block.previous_hash),
            block.proofs.len(),
            block.validator,
        );
        Sha256::digest(data.as_bytes()).into()
    }
}
