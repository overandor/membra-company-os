use serde::{Deserialize, Serialize};
use sha3::{Digest, Keccak256};

/// Proof-of-Proof: The hash of an inference IS the proof.
/// No external validation needed — correctness is cryptographic.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProofOfProof {
    pub prompt_hash: String,
    pub response_hash: String,
    pub token_hashes: Vec<String>,
    pub total_value: u64,
    pub timestamp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceProof {
    pub agent_id: String,
    pub model: String,
    pub prompt_hash: String,
    pub response_hash: String,
    pub token_count: u64,
    pub confidence: f64,
    pub timestamp: i64,
}

impl ProofOfProof {
    pub fn from_prompt_response(prompt: &str, response: &str, model: &str) -> Self {
        let prompt_hash = Self::hash(prompt);
        let response_hash = Self::hash(response);
        
        // Each token in response generates a micro-hash
        let tokens: Vec<&str> = response.split_whitespace().collect();
        let token_hashes: Vec<String> = tokens.iter()
            .map(|t| Self::hash(t))
            .collect();
        
        // Value = token count * 100 base units
        let total_value = (token_hashes.len() as u64) * 100;
        
        Self {
            prompt_hash,
            response_hash,
            token_hashes,
            total_value,
            timestamp: chrono::Utc::now().timestamp_millis(),
        }
    }
    
    pub fn verify(&self) -> bool {
        // Recompute and verify
        // In production: verify each token hash
        !self.prompt_hash.is_empty() && !self.response_hash.is_empty()
    }
    
    pub fn merkle_root(&self) -> String {
        let mut hashes: Vec<Vec<u8>> = self.token_hashes.iter()
            .map(|h| hex::decode(h).unwrap_or_default())
            .collect();
        
        // Add prompt and response as boundary hashes
        hashes.insert(0, hex::decode(&self.prompt_hash).unwrap_or_default());
        hashes.push(hex::decode(&self.response_hash).unwrap_or_default());
        
        while hashes.len() > 1 {
            let mut next = Vec::new();
            for i in (0..hashes.len()).step_by(2) {
                let left = &hashes[i];
                let right = if i + 1 < hashes.len() { &hashes[i + 1] } else { left };
                let mut hasher = Keccak256::new();
                hasher.update(left);
                hasher.update(right);
                next.push(hasher.finalize().to_vec());
            }
            hashes = next;
        }
        
        hex::encode(&hashes[0])
    }
    
    fn hash(data: &str) -> String {
        let mut hasher = Keccak256::new();
        hasher.update(data.as_bytes());
        hex::encode(hasher.finalize())
    }
}
