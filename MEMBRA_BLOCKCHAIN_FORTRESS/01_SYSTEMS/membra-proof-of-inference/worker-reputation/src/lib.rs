use dashmap::DashMap;
use ed25519_dalek::{VerifyingKey, Signature, Verifier};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use chrono::{DateTime, Utc, Duration};
use sha2::{Digest, Sha256};
use rand::Rng;

/// Worker Identity Registry
pub struct WorkerRegistry {
    /// Worker identity records
    workers: Arc<DashMap<String, WorkerIdentity>>,
    /// Public key to worker ID mapping
    pubkey_to_worker: Arc<DashMap<String, String>>,
    /// Owner wallet to workers mapping
    owner_to_workers: Arc<DashMap<String, Vec<String>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkerIdentity {
    pub worker_id: String,
    pub public_key: String,
    pub owner_wallet: String,
    pub model_capabilities: Vec<String>,
    pub supported_model_cids: Vec<String>,
    pub hardware_fingerprint_hash: String,
    pub runtime_fingerprint_hash: String,
    pub registered_at: DateTime<Utc>,
    pub status: WorkerStatus,
    pub trust_score: f64,
    pub slashing_events: Vec<SlashingEvent>,
    pub successful_inferences: u64,
    pub failed_challenges: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WorkerStatus {
    Active,
    Suspended,
    Banned,
    Pending,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SlashingEvent {
    pub event_type: SlashingType,
    pub reason: String,
    pub severity: SlashingSeverity,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SlashingType {
    SignatureFraud,
    FabricatedReceipt,
    ChallengeFailure,
    HardwareMismatch,
    RuntimeMismatch,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SlashingSeverity {
    Minor,
    Major,
    Critical,
}

impl WorkerRegistry {
    pub fn new() -> Self {
        Self {
            workers: Arc::new(DashMap::new()),
            pubkey_to_worker: Arc::new(DashMap::new()),
            owner_to_workers: Arc::new(DashMap::new()),
        }
    }

    /// Register a new worker
    pub fn register_worker(
        &self,
        worker_id: String,
        public_key: String,
        owner_wallet: String,
        model_capabilities: Vec<String>,
        supported_model_cids: Vec<String>,
        hardware_fingerprint_hash: String,
        runtime_fingerprint_hash: String,
    ) -> Result<(), String> {
        // Check if worker already exists
        if self.workers.contains_key(&worker_id) {
            return Err("Worker already registered".to_string());
        }

        // Check if public key already registered
        if self.pubkey_to_worker.contains_key(&public_key) {
            return Err("Public key already registered".to_string());
        }

        let identity = WorkerIdentity {
            worker_id: worker_id.clone(),
            public_key: public_key.clone(),
            owner_wallet: owner_wallet.clone(),
            model_capabilities,
            supported_model_cids,
            hardware_fingerprint_hash,
            runtime_fingerprint_hash,
            registered_at: Utc::now(),
            status: WorkerStatus::Pending,
            trust_score: 0.5, // Start at 50% trust
            slashing_events: Vec::new(),
            successful_inferences: 0,
            failed_challenges: 0,
        };

        self.workers.insert(worker_id.clone(), identity);
        self.pubkey_to_worker.insert(public_key, worker_id.clone());
        
        // Add to owner's worker list
        self.owner_to_workers
            .entry(owner_wallet)
            .or_insert_with(Vec::new)
            .push(worker_id);

        Ok(())
    }

    /// Get worker by ID
    pub fn get_worker(&self, worker_id: &str) -> Option<WorkerIdentity> {
        self.workers.get(worker_id).map(|w| w.clone())
    }

    /// Get worker by public key
    pub fn get_worker_by_pubkey(&self, public_key: &str) -> Option<WorkerIdentity> {
        if let Some(worker_id) = self.pubkey_to_worker.get(public_key) {
            self.get_worker(worker_id.as_str())
        } else {
            None
        }
    }

    /// Update worker status
    pub fn update_status(&self, worker_id: &str, status: WorkerStatus) -> Result<(), String> {
        if let Some(mut worker) = self.workers.get_mut(worker_id) {
            worker.status = status;
            Ok(())
        } else {
            Err("Worker not found".to_string())
        }
    }

    /// Add slashing event
    pub fn add_slashing_event(
        &self,
        worker_id: &str,
        event_type: SlashingType,
        reason: String,
        severity: SlashingSeverity,
    ) -> Result<(), String> {
        if let Some(mut worker) = self.workers.get_mut(worker_id) {
            // Check before move
            let is_critical = matches!(severity, SlashingSeverity::Critical);
            let event = SlashingEvent {
                event_type,
                reason,
                severity,
                timestamp: Utc::now(),
            };
            worker.slashing_events.push(event);
            
            // Auto-ban on critical severity
            if is_critical {
                worker.status = WorkerStatus::Banned;
            }
            
            Ok(())
        } else {
            Err("Worker not found".to_string())
        }
    }

    /// Increment successful inferences
    pub fn increment_inferences(&self, worker_id: &str) {
        if let Some(mut worker) = self.workers.get_mut(worker_id) {
            worker.successful_inferences += 1;
        }
    }

    /// Increment failed challenges
    pub fn increment_failed_challenges(&self, worker_id: &str) {
        if let Some(mut worker) = self.workers.get_mut(worker_id) {
            worker.failed_challenges += 1;
        }
    }

    /// Get all workers for an owner
    pub fn get_owner_workers(&self, owner_wallet: &str) -> Vec<WorkerIdentity> {
        if let Some(worker_ids) = self.owner_to_workers.get(owner_wallet) {
            worker_ids
                .iter()
                .filter_map(|id| self.get_worker(id))
                .collect()
        } else {
            Vec::new()
        }
    }
}

/// Reputation Ledger
pub struct ReputationLedger {
    /// Worker reputation records
    reputations: Arc<DashMap<String, WorkerReputation>>,
    /// Base identity score for new workers
    base_identity_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkerReputation {
    pub worker_id: String,
    pub valid_poi_count: u64,
    pub invalid_poi_count: u64,
    pub challenge_pass_count: u64,
    pub challenge_fail_count: u64,
    pub uptime_score: f64,
    pub latency_score: f64,
    pub model_consistency_score: f64,
    pub hardware_consistency_score: f64,
    pub semantic_quality_score: f64,
    pub trust_score: f64,
    pub last_updated: DateTime<Utc>,
}

impl ReputationLedger {
    pub fn new(base_identity_score: f64) -> Self {
        Self {
            reputations: Arc::new(DashMap::new()),
            base_identity_score,
        }
    }

    /// Get or create reputation record
    pub fn get_or_create(&self, worker_id: &str) -> WorkerReputation {
        if let Some(rep) = self.reputations.get(worker_id) {
            rep.clone()
        } else {
            let rep = WorkerReputation {
                worker_id: worker_id.to_string(),
                valid_poi_count: 0,
                invalid_poi_count: 0,
                challenge_pass_count: 0,
                challenge_fail_count: 0,
                uptime_score: 1.0,
                latency_score: 1.0,
                model_consistency_score: 1.0,
                hardware_consistency_score: 1.0,
                semantic_quality_score: 0.5,
                trust_score: self.base_identity_score,
                last_updated: Utc::now(),
            };
            self.reputations.insert(worker_id.to_string(), rep.clone());
            rep
        }
    }

    /// Compute trust score from reputation metrics
    pub fn compute_trust_score(&self, reputation: &WorkerReputation) -> f64 {
        let total_poi = reputation.valid_poi_count + reputation.invalid_poi_count;
        let proof_validity_rate = if total_poi > 0 {
            reputation.valid_poi_count as f64 / total_poi as f64
        } else {
            1.0
        };

        let total_challenges = reputation.challenge_pass_count + reputation.challenge_fail_count;
        let challenge_success_rate = if total_challenges > 0 {
            reputation.challenge_pass_count as f64 / total_challenges as f64
        } else {
            1.0
        };

        let uptime_factor = reputation.uptime_score;
        let model_consistency = reputation.model_consistency_score;
        let decay_factor = 1.0; // TODO: implement time-based decay

        let trust_score = self.base_identity_score
            * proof_validity_rate
            * challenge_success_rate
            * uptime_factor
            * model_consistency
            * decay_factor;

        // Clamp between 0.05 and 1.00
        trust_score.max(0.05).min(1.0)
    }

    /// Update reputation after valid PoI
    pub fn record_valid_poi(&self, worker_id: &str) {
        let mut rep = self.get_or_create(worker_id);
        rep.valid_poi_count += 1;
        rep.trust_score = self.compute_trust_score(&rep);
        rep.last_updated = Utc::now();
        self.reputations.insert(worker_id.to_string(), rep);
    }

    /// Update reputation after invalid PoI
    pub fn record_invalid_poi(&self, worker_id: &str) {
        let mut rep = self.get_or_create(worker_id);
        rep.invalid_poi_count += 1;
        rep.trust_score = self.compute_trust_score(&rep);
        rep.last_updated = Utc::now();
        self.reputations.insert(worker_id.to_string(), rep);
    }

    /// Update reputation after challenge pass
    pub fn record_challenge_pass(&self, worker_id: &str) {
        let mut rep = self.get_or_create(worker_id);
        rep.challenge_pass_count += 1;
        rep.trust_score = self.compute_trust_score(&rep);
        rep.last_updated = Utc::now();
        self.reputations.insert(worker_id.to_string(), rep);
    }

    /// Update reputation after challenge fail
    pub fn record_challenge_fail(&self, worker_id: &str) {
        let mut rep = self.get_or_create(worker_id);
        rep.challenge_fail_count += 1;
        rep.trust_score = self.compute_trust_score(&rep);
        rep.last_updated = Utc::now();
        self.reputations.insert(worker_id.to_string(), rep);
    }

    /// Get trust multiplier for collateral scoring
    pub fn get_trust_multiplier(&self, worker_id: &str) -> f64 {
        let rep = self.get_or_create(worker_id);
        let trust = rep.trust_score;

        if trust >= 0.90 {
            1.00
        } else if trust >= 0.75 {
            0.75
        } else if trust >= 0.50 {
            0.40
        } else if trust >= 0.25 {
            0.15
        } else {
            0.0
        }
    }

    /// Get reputation record
    pub fn get_reputation(&self, worker_id: &str) -> Option<WorkerReputation> {
        self.reputations.get(worker_id).map(|r| r.clone())
    }

    /// Directly set trust score (for seeding established worker state in demos / tests)
    pub fn set_trust_score(&self, worker_id: &str, trust: f64) {
        let mut rep = self.get_or_create(worker_id);
        rep.trust_score = trust.max(0.05).min(1.0);
        rep.last_updated = Utc::now();
        self.reputations.insert(worker_id.to_string(), rep);
    }
}

/// Challenge System
pub struct ChallengeSystem {
    /// Active challenges
    active_challenges: Arc<DashMap<String, Challenge>>,
    /// Challenge history
    challenge_history: Arc<DashMap<String, Vec<ChallengeResult>>>,
    /// Canary prompts pool
    canary_prompts: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Challenge {
    pub challenge_id: String,
    pub worker_id: String,
    pub challenge_type: ChallengeType,
    pub prompt: String,
    pub expected_token_hash: Option<String>,
    pub seed: u64,
    pub sampler_params: SamplerState,
    pub model_cid: String,
    pub created_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub status: ChallengeStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ChallengeType {
    Deterministic,
    Redundant,
    Replay,
    Canary,
    HardwareRuntime,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ChallengeStatus {
    Pending,
    Passed,
    Failed,
    Expired,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChallengeResult {
    pub challenge_id: String,
    pub worker_id: String,
    pub challenge_type: ChallengeType,
    pub passed: bool,
    pub mismatch_reason: Option<String>,
    pub severity: ChallengeSeverity,
    pub completed_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ChallengeSeverity {
    Minor,
    Major,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SamplerState {
    pub temperature: f32,
    pub top_p: f32,
    pub top_k: u32,
}

impl ChallengeSystem {
    pub fn new() -> Self {
        Self {
            active_challenges: Arc::new(DashMap::new()),
            challenge_history: Arc::new(DashMap::new()),
            canary_prompts: vec![
                "The capital of France is".to_string(),
                "2 + 2 equals".to_string(),
                "The color of the sky is".to_string(),
            ],
        }
    }

    /// Generate deterministic challenge
    pub fn generate_deterministic_challenge(
        &self,
        worker_id: String,
        model_cid: String,
        prompt: String,
        seed: u64,
        expected_token_hash: String,
    ) -> Challenge {
        let challenge_id = format!("det_{}", hex::encode(Sha256::digest(format!("{}{}{}", worker_id, prompt, seed).as_bytes())));
        
        Challenge {
            challenge_id: challenge_id.clone(),
            worker_id,
            challenge_type: ChallengeType::Deterministic,
            prompt,
            expected_token_hash: Some(expected_token_hash),
            seed,
            sampler_params: SamplerState {
                temperature: 0.0,
                top_p: 1.0,
                top_k: 1,
            },
            model_cid,
            created_at: Utc::now(),
            expires_at: Utc::now() + Duration::minutes(5),
            status: ChallengeStatus::Pending,
        }
    }

    /// Generate redundant challenge (same task to multiple workers)
    pub fn generate_redundant_challenge(
        &self,
        worker_id: String,
        model_cid: String,
        prompt: String,
        seed: u64,
    ) -> Challenge {
        let challenge_id = format!("red_{}", hex::encode(Sha256::digest(format!("{}{}{}", worker_id, prompt, seed).as_bytes())));
        
        Challenge {
            challenge_id: challenge_id.clone(),
            worker_id,
            challenge_type: ChallengeType::Redundant,
            prompt,
            expected_token_hash: None, // Will compare across workers
            seed,
            sampler_params: SamplerState {
                temperature: 0.7,
                top_p: 0.9,
                top_k: 40,
            },
            model_cid,
            created_at: Utc::now(),
            expires_at: Utc::now() + Duration::minutes(10),
            status: ChallengeStatus::Pending,
        }
    }

    /// Generate replay challenge (reproduce previous inference)
    pub fn generate_replay_challenge(
        &self,
        worker_id: String,
        model_cid: String,
        original_prompt: String,
        original_seed: u64,
        original_token_hash: String,
    ) -> Challenge {
        let challenge_id = format!("rep_{}", hex::encode(Sha256::digest(format!("{}{}{}", worker_id, original_prompt, original_seed).as_bytes())));
        
        Challenge {
            challenge_id: challenge_id.clone(),
            worker_id,
            challenge_type: ChallengeType::Replay,
            prompt: original_prompt,
            expected_token_hash: Some(original_token_hash),
            seed: original_seed,
            sampler_params: SamplerState {
                temperature: 0.0,
                top_p: 1.0,
                top_k: 1,
            },
            model_cid,
            created_at: Utc::now(),
            expires_at: Utc::now() + Duration::minutes(5),
            status: ChallengeStatus::Pending,
        }
    }

    /// Generate canary challenge (hidden protocol-generated prompt)
    pub fn generate_canary_challenge(&self, worker_id: String, model_cid: String) -> Challenge {
        let mut rng = rand::thread_rng();
        let prompt = self.canary_prompts[rng.gen_range(0..self.canary_prompts.len())].clone();
        let seed = rng.gen();
        
        let challenge_id = format!("can_{}", hex::encode(Sha256::digest(format!("{}{}{}", worker_id, prompt, seed).as_bytes())));
        
        Challenge {
            challenge_id: challenge_id.clone(),
            worker_id,
            challenge_type: ChallengeType::Canary,
            prompt,
            expected_token_hash: None, // Known expected output
            seed,
            sampler_params: SamplerState {
                temperature: 0.0,
                top_p: 1.0,
                top_k: 1,
            },
            model_cid,
            created_at: Utc::now(),
            expires_at: Utc::now() + Duration::minutes(3),
            status: ChallengeStatus::Pending,
        }
    }

    /// Submit challenge response
    pub fn submit_challenge_response(
        &self,
        challenge_id: String,
        actual_tokens: Vec<u32>,
    ) -> Result<ChallengeResult, String> {
        if let Some(mut challenge) = self.active_challenges.get_mut(&challenge_id) {
            // Check if expired
            if Utc::now() > challenge.expires_at {
                challenge.status = ChallengeStatus::Expired;
                return Err("Challenge expired".to_string());
            }

            // Verify deterministic challenge
            if let ChallengeType::Deterministic = challenge.challenge_type {
                if let Some(expected_hash) = &challenge.expected_token_hash {
                    let actual_hash = Self::compute_token_hash(&actual_tokens);
                    let passed = actual_hash == *expected_hash;
                    
                    let result = ChallengeResult {
                        challenge_id: challenge_id.clone(),
                        worker_id: challenge.worker_id.clone(),
                        challenge_type: challenge.challenge_type.clone(),
                        passed,
                        mismatch_reason: if !passed { Some("Token hash mismatch".to_string()) } else { None },
                        severity: if passed { ChallengeSeverity::Minor } else { ChallengeSeverity::Major },
                        completed_at: Utc::now(),
                    };
                    
                    challenge.status = if passed { ChallengeStatus::Passed } else { ChallengeStatus::Failed };
                    self.record_result(challenge.worker_id.clone(), result.clone());
                    return Ok(result);
                }
            }

            // For other challenge types, implement similar logic
            Ok(ChallengeResult {
                challenge_id,
                worker_id: challenge.worker_id.clone(),
                challenge_type: challenge.challenge_type.clone(),
                passed: true,
                mismatch_reason: None,
                severity: ChallengeSeverity::Minor,
                completed_at: Utc::now(),
            })
        } else {
            Err("Challenge not found".to_string())
        }
    }

    fn compute_token_hash(tokens: &[u32]) -> String {
        hex::encode(Sha256::digest(
            &tokens.iter().flat_map(|t| t.to_be_bytes().to_vec()).collect::<Vec<u8>>()
        ))
    }

    fn record_result(&self, worker_id: String, result: ChallengeResult) {
        self.challenge_history
            .entry(worker_id)
            .or_insert_with(Vec::new)
            .push(result);
    }

    /// Get challenge history for worker
    pub fn get_worker_history(&self, worker_id: &str) -> Vec<ChallengeResult> {
        self.challenge_history.get(worker_id).map(|h| h.clone()).unwrap_or_default()
    }
}
