use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use ed25519_dalek::{SigningKey, VerifyingKey, Signature, Signer, Verifier};
use chrono::{DateTime, Duration, Utc};

pub mod verification;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProofOfInference {
    pub model_cid: String,
    pub tokenizer_hash: [u8; 32],
    pub prompt_hash: [u8; 32],
    pub prompt_length: u32,
    pub sampler_state: SamplerState,
    pub seed: u64,
    pub token_sequence_hash: [u8; 32],
    pub token_count: u32,
    pub kv_commitment: KVCommitment,
    pub runtime_fingerprint: RuntimeFingerprint,
    pub hardware_attestation: HardwareAttestation,
    pub timestamp: DateTime<Utc>,
    pub inference_id: String,
    pub signature: Vec<u8>,
    // Worker identity binding (Phase 2B)
    pub worker_id: String,
    pub worker_pubkey: String,
    pub worker_signature: Vec<u8>,
    pub worker_registry_epoch: u64,
    pub trust_snapshot: f64,
    pub challenge_window_expires_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SamplerState {
    pub temperature: f32,
    pub top_p: f32,
    pub top_k: u32,
    pub repeat_penalty: f32,
}

impl Default for SamplerState {
    fn default() -> Self {
        Self { temperature: 0.7, top_p: 0.9, top_k: 40, repeat_penalty: 1.0 }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KVCommitment {
    pub layer_hashes: Vec<[u8; 32]>,
    pub cache_size_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuntimeFingerprint {
    pub runtime_version: String,
    pub quantization: String,
    pub context_length: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareAttestation {
    pub cpu_vendor: String,
    pub gpu_vendor: Option<String>,
    pub platform: String,
}

impl ProofOfInference {
    pub fn new(
        model_cid: String,
        prompt: &[u8],
        tokens: &[u32],
        sampler_state: SamplerState,
        seed: u64,
        kv_commitment: KVCommitment,
        runtime_fingerprint: RuntimeFingerprint,
        hardware_attestation: HardwareAttestation,
        keypair: &SigningKey,
        worker_id: String,
        worker_pubkey: String,
        worker_keypair: &SigningKey,
        worker_registry_epoch: u64,
        trust_snapshot: f64,
    ) -> Self {
        let prompt_hash = Sha256::digest(prompt);
        let token_sequence_hash = Self::compute_token_merkle_root(tokens);
        let inference_id = hex::encode(Sha256::digest(&[&prompt_hash[..], &token_sequence_hash[..]].concat()));
        
        let challenge_window_expires_at = Utc::now() + Duration::hours(1);
        
        let mut proof = Self {
            model_cid,
            tokenizer_hash: [0u8; 32],
            prompt_hash: prompt_hash.into(),
            prompt_length: prompt.len() as u32,
            sampler_state,
            seed,
            token_sequence_hash,
            token_count: tokens.len() as u32,
            kv_commitment,
            runtime_fingerprint,
            hardware_attestation,
            timestamp: Utc::now(),
            inference_id,
            signature: Vec::new(),
            worker_id: worker_id.clone(),
            worker_pubkey: worker_pubkey.clone(),
            worker_signature: Vec::new(),
            worker_registry_epoch,
            trust_snapshot,
            challenge_window_expires_at,
        };
        
        // Sign with issuer key
        let message = proof.signing_message();
        let signature = keypair.sign(&message);
        proof.signature = signature.to_bytes().to_vec();
        
        // Sign with worker key
        let worker_message = proof.worker_signing_message();
        let worker_signature = worker_keypair.sign(&worker_message);
        proof.worker_signature = worker_signature.to_bytes().to_vec();
        
        proof
    }
    
    fn compute_token_merkle_root(tokens: &[u32]) -> [u8; 32] {
        if tokens.is_empty() { return [0u8; 32]; }
        let mut hashes: Vec<[u8; 32]> = tokens.iter().map(|t| Sha256::digest(&t.to_be_bytes()[..]).into()).collect();
        while hashes.len() > 1 {
            let mut next = Vec::new();
            for chunk in hashes.chunks(2) {
                if chunk.len() == 2 {
                    let combined = [&chunk[0][..], &chunk[1][..]].concat();
                    next.push(Sha256::digest(&combined).into());
                } else { next.push(chunk[0]); }
            }
            hashes = next;
        }
        hashes[0]
    }
    
    fn signing_message(&self) -> [u8; 32] {
        let data = format!("{}{}{}{}{}{}", self.model_cid, hex::encode(self.prompt_hash), 
            hex::encode(self.token_sequence_hash), self.seed, 
            serde_json::to_string(&self.sampler_state).unwrap(), self.timestamp.timestamp());
        Sha256::digest(data.as_bytes()).into()
    }
    
    fn worker_signing_message(&self) -> [u8; 32] {
        let data = format!("{}{}{}{}{}{}", 
            self.worker_id,
            hex::encode(self.prompt_hash),
            hex::encode(self.token_sequence_hash),
            self.seed,
            self.worker_registry_epoch,
            self.trust_snapshot,
        );
        Sha256::digest(data.as_bytes()).into()
    }
    
    pub fn verify(&self, public_key: &VerifyingKey) -> bool {
        let message = self.signing_message();
        let Ok(sig_bytes): Result<[u8; 64], _> = self.signature[..].try_into() else { return false };
        let signature = Signature::from_bytes(&sig_bytes);
        public_key.verify(&message, &signature).is_ok()
    }
    
    /// Verify worker signature
    pub fn verify_worker_signature(&self, worker_public_key: &VerifyingKey) -> bool {
        let message = self.worker_signing_message();
        let Ok(sig_bytes): Result<[u8; 64], _> = self.worker_signature[..].try_into() else { return false };
        let signature = Signature::from_bytes(&sig_bytes);
        worker_public_key.verify(&message, &signature).is_ok()
    }
    
    /// Check if challenge window is still valid
    pub fn is_challenge_window_valid(&self) -> bool {
        Utc::now() < self.challenge_window_expires_at
    }
}
