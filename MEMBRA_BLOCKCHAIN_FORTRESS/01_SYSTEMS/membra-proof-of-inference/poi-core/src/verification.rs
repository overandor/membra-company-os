use crate::ProofOfInference;
use ed25519_dalek::VerifyingKey;
use sha2::{Digest, Sha256};

/// Verification utilities for PoI proofs
impl ProofOfInference {
    /// Verify the complete proof: signature + prompt hash + token merkle root
    pub fn verify_complete(&self, public_key: &VerifyingKey, prompt: &[u8], tokens: &[u32]) -> bool {
        if !self.verify(public_key) {
            return false;
        }
        if !self.verify_prompt(prompt) {
            return false;
        }
        if !self.verify_tokens(tokens) {
            return false;
        }
        true
    }

    /// Verify that the stored prompt_hash matches a given prompt
    pub fn verify_prompt(&self, prompt: &[u8]) -> bool {
        let expected: [u8; 32] = Sha256::digest(prompt).into();
        self.prompt_hash == expected
    }

    /// Verify that the stored token_sequence_hash matches given tokens
    pub fn verify_tokens(&self, tokens: &[u32]) -> bool {
        let expected = Self::compute_token_merkle_root(tokens);
        self.token_sequence_hash == expected
    }

    /// Verify timestamp is recent (within max_age_seconds)
    pub fn verify_timestamp(&self, max_age_seconds: i64) -> bool {
        let now = chrono::Utc::now().timestamp();
        let proof_time = self.timestamp.timestamp();
        (now - proof_time).abs() <= max_age_seconds
    }

    /// Verify model CID format (basic IPFS CID check)
    pub fn verify_model_cid(&self) -> bool {
        self.model_cid.starts_with("bafy") || self.model_cid.starts_with("Qm")
    }

    /// Verify sampler state is within valid bounds
    pub fn verify_sampler_state(&self) -> bool {
        let s = &self.sampler_state;
        s.temperature > 0.0 && s.temperature <= 2.0
            && s.top_p > 0.0 && s.top_p <= 1.0
            && s.top_k > 0
            && s.repeat_penalty >= 1.0
    }
}
