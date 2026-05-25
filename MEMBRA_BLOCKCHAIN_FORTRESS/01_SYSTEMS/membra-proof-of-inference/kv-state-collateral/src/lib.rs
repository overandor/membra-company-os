use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use chrono::{DateTime, Utc, Duration};
use sha2::{Digest, Sha256};
use bincode;

/// KV-State Collateral: live transformer state as collateral
pub struct KVStateCollateral {
    /// KV-state registry
    kv_states: Arc<DashMap<String, KVStateRecord>>,
    /// Prefill registry
    prefills: Arc<DashMap<String, PrefillRecord>>,
    /// Attention state registry
    attention_states: Arc<DashMap<String, AttentionStateRecord>>,
    /// Reasoning context registry
    reasoning_contexts: Arc<DashMap<String, ReasoningContextRecord>>,
    /// Active challenges
    challenges: Arc<DashMap<String, KVStateChallenge>>,
    /// Challenge results
    challenge_results: Arc<DashMap<String, KVStateChallengeResult>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KVStateRecord {
    pub state_id: String,
    pub model_cid: String,
    pub layer_hashes: Vec<String>,
    pub cache_size_bytes: u64,
    pub token_position: u32,
    pub context_length: u32,
    pub created_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub reuse_count: u64,
    pub collateral_value: u64,
    pub owner_pubkey: String,
    pub worker_id: String,
    pub state_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrefillRecord {
    pub prefill_id: String,
    pub model_cid: String,
    pub prompt_tokens: Vec<u32>,
    pub prefill_length: u32,
    pub computed_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub reuse_count: u64,
    pub collateral_value: u64,
    pub owner_pubkey: String,
    pub worker_id: String,
    pub prefill_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AttentionStateRecord {
    pub attention_id: String,
    pub model_cid: String,
    pub layer_attention: Vec<LayerAttention>,
    pub sequence_length: u32,
    pub computed_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub reuse_count: u64,
    pub collateral_value: u64,
    pub owner_pubkey: String,
    pub worker_id: String,
    pub attention_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LayerAttention {
    pub layer_index: u32,
    pub attention_pattern: Vec<f32>,
    pub head_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReasoningContextRecord {
    pub context_id: String,
    pub model_cid: String,
    pub reasoning_trace: Vec<ReasoningStep>,
    pub context_window: Vec<u32>,
    pub computed_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub reuse_count: u64,
    pub collateral_value: u64,
    pub owner_pubkey: String,
    pub worker_id: String,
    pub context_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReasoningStep {
    pub step_index: u32,
    pub hidden_state_hash: String,
    pub attention_hash: String,
    pub token_id: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KVStateCollateralValue {
    pub base_value: u64,
    pub reuse_multiplier: f64,
    pub freshness_multiplier: f64,
    pub complexity_multiplier: f64,
    pub worker_trust_multiplier: f64,
    pub final_value: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum KVStateChallengeType {
    /// Deterministic reproduction - reproduce KV-state from same prompt
    DeterministicReproduction,
    /// Attention pattern consistency - verify attention patterns match
    AttentionConsistency,
    /// Reasoning trace validation - verify reasoning steps are valid
    ReasoningTraceValidation,
    /// Hash verification - verify state hash matches claimed hash
    HashVerification,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KVStateChallenge {
    pub challenge_id: String,
    pub state_id: String,
    pub challenge_type: KVStateChallengeType,
    pub challenge_data: String,
    pub created_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub difficulty: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KVStateChallengeResponse {
    pub challenge_id: String,
    pub state_id: String,
    pub response_data: String,
    pub worker_signature: String,
    pub submitted_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KVStateChallengeResult {
    pub challenge_id: String,
    pub state_id: String,
    pub passed: bool,
    pub score: f64,
    pub details: String,
    pub verified_at: DateTime<Utc>,
}

impl KVStateCollateral {
    pub fn new() -> Self {
        Self {
            kv_states: Arc::new(DashMap::new()),
            prefills: Arc::new(DashMap::new()),
            attention_states: Arc::new(DashMap::new()),
            reasoning_contexts: Arc::new(DashMap::new()),
            challenges: Arc::new(DashMap::new()),
            challenge_results: Arc::new(DashMap::new()),
        }
    }

    /// Register a KV-state as collateral
    pub fn register_kv_state(
        &self,
        state_id: String,
        model_cid: String,
        layer_hashes: Vec<String>,
        cache_size_bytes: u64,
        token_position: u32,
        context_length: u32,
        owner_pubkey: String,
        worker_id: String,
        worker_trust: f64,
    ) -> Result<String, String> {
        let state_hash = self.compute_state_hash(&state_id, &model_cid, &layer_hashes, token_position);
        let now = Utc::now();
        let expires_at = now + Duration::hours(6);
        let collateral_value = self.calculate_kv_collateral(
            cache_size_bytes,
            context_length,
            0,
            worker_trust,
            &now,
        );

        let record = KVStateRecord {
            state_id: state_id.clone(),
            model_cid,
            layer_hashes,
            cache_size_bytes,
            token_position,
            context_length,
            created_at: now,
            expires_at,
            reuse_count: 0,
            collateral_value,
            owner_pubkey,
            worker_id,
            state_hash,
        };

        self.kv_states.insert(state_id.clone(), record);
        Ok(state_id)
    }

    /// Register a prefill as collateral
    pub fn register_prefill(
        &self,
        prefill_id: String,
        model_cid: String,
        prompt_tokens: Vec<u32>,
        prefill_length: u32,
        owner_pubkey: String,
        worker_id: String,
        worker_trust: f64,
    ) -> Result<String, String> {
        let prefill_hash = self.compute_prefill_hash(&prefill_id, &model_cid, &prompt_tokens);
        let now = Utc::now();
        let expires_at = now + Duration::hours(12);
        let collateral_value = self.calculate_prefill_collateral(
            prefill_length,
            prompt_tokens.len() as u32,
            0,
            worker_trust,
            &now,
        );

        let record = PrefillRecord {
            prefill_id: prefill_id.clone(),
            model_cid,
            prompt_tokens,
            prefill_length,
            computed_at: now,
            expires_at,
            reuse_count: 0,
            collateral_value,
            owner_pubkey,
            worker_id,
            prefill_hash,
        };

        self.prefills.insert(prefill_id.clone(), record);
        Ok(prefill_id)
    }

    /// Register an attention state as collateral
    pub fn register_attention_state(
        &self,
        attention_id: String,
        model_cid: String,
        layer_attention: Vec<LayerAttention>,
        sequence_length: u32,
        owner_pubkey: String,
        worker_id: String,
        worker_trust: f64,
    ) -> Result<String, String> {
        let attention_hash = self.compute_attention_hash(&attention_id, &model_cid, &layer_attention);
        let now = Utc::now();
        let expires_at = now + Duration::hours(4);
        let collateral_value = self.calculate_attention_collateral(
            layer_attention.len() as u32,
            sequence_length,
            0,
            worker_trust,
            &now,
        );

        let record = AttentionStateRecord {
            attention_id: attention_id.clone(),
            model_cid,
            layer_attention,
            sequence_length,
            computed_at: now,
            expires_at,
            reuse_count: 0,
            collateral_value,
            owner_pubkey,
            worker_id,
            attention_hash,
        };

        self.attention_states.insert(attention_id.clone(), record);
        Ok(attention_id)
    }

    /// Register a reasoning context as collateral
    pub fn register_reasoning_context(
        &self,
        context_id: String,
        model_cid: String,
        reasoning_trace: Vec<ReasoningStep>,
        context_window: Vec<u32>,
        owner_pubkey: String,
        worker_id: String,
        worker_trust: f64,
    ) -> Result<String, String> {
        let context_hash = self.compute_context_hash(&context_id, &model_cid, &reasoning_trace);
        let now = Utc::now();
        let expires_at = now + Duration::hours(8);
        let collateral_value = self.calculate_context_collateral(
            reasoning_trace.len() as u32,
            context_window.len() as u32,
            0,
            worker_trust,
            &now,
        );

        let record = ReasoningContextRecord {
            context_id: context_id.clone(),
            model_cid,
            reasoning_trace,
            context_window,
            computed_at: now,
            expires_at,
            reuse_count: 0,
            collateral_value,
            owner_pubkey,
            worker_id,
            context_hash,
        };

        self.reasoning_contexts.insert(context_id.clone(), record);
        Ok(context_id)
    }

    /// Compute exponential freshness decay: 1.0 at creation → 0.0 at expiry_hours
    fn freshness_decay(created_at: &DateTime<Utc>, expiry_hours: i64) -> f64 {
        let age_secs = (Utc::now() - *created_at).num_seconds().max(0) as f64;
        let total_secs = (expiry_hours * 3600) as f64;
        let ratio = (age_secs / total_secs).min(1.0);
        // Exponential decay: e^(-3 * ratio) — reaches ~0.05 at full expiry
        (-3.0 * ratio).exp()
    }

    /// Calculate KV-state collateral value
    fn calculate_kv_collateral(
        &self,
        cache_size_bytes: u64,
        context_length: u32,
        reuse_count: u64,
        worker_trust: f64,
        created_at: &DateTime<Utc>,
    ) -> u64 {
        let base_value = (cache_size_bytes / 1024) * 10; // 10 lamports per KB
        let reuse_multiplier = 1.0 + (reuse_count as f64 * 0.1);
        let freshness_multiplier = Self::freshness_decay(created_at, 6);
        let complexity_multiplier = (context_length as f64 / 8192.0).clamp(0.5, 2.0);
        
        let final_value = (base_value as f64) * reuse_multiplier * freshness_multiplier * complexity_multiplier * worker_trust;
        final_value as u64
    }

    /// Calculate prefill collateral value
    fn calculate_prefill_collateral(
        &self,
        prefill_length: u32,
        total_tokens: u32,
        reuse_count: u64,
        worker_trust: f64,
        created_at: &DateTime<Utc>,
    ) -> u64 {
        let base_value = prefill_length as u64 * 50; // 50 lamports per prefill token
        let reuse_multiplier = 1.0 + (reuse_count as f64 * 0.15); // Higher reuse bonus for prefills
        let freshness_multiplier = Self::freshness_decay(created_at, 12);
        let complexity_multiplier = (total_tokens as f64 / 4096.0).clamp(0.5, 1.5);
        
        let final_value = (base_value as f64) * reuse_multiplier * freshness_multiplier * complexity_multiplier * worker_trust;
        final_value as u64
    }

    /// Calculate attention state collateral value
    fn calculate_attention_collateral(
        &self,
        layer_count: u32,
        sequence_length: u32,
        reuse_count: u64,
        worker_trust: f64,
        created_at: &DateTime<Utc>,
    ) -> u64 {
        let base_value = layer_count as u64 * sequence_length as u64 * 5; // 5 lamports per layer-token
        let reuse_multiplier = 1.0 + (reuse_count as f64 * 0.08);
        let freshness_multiplier = Self::freshness_decay(created_at, 4);
        let complexity_multiplier = (layer_count as f64 / 32.0).clamp(0.5, 2.0);
        
        let final_value = (base_value as f64) * reuse_multiplier * freshness_multiplier * complexity_multiplier * worker_trust;
        final_value as u64
    }

    /// Calculate reasoning context collateral value
    fn calculate_context_collateral(
        &self,
        step_count: u32,
        context_window_size: u32,
        reuse_count: u64,
        worker_trust: f64,
        created_at: &DateTime<Utc>,
    ) -> u64 {
        let base_value = step_count as u64 * 100 + context_window_size as u64 * 20;
        let reuse_multiplier = 1.0 + (reuse_count as f64 * 0.12);
        let freshness_multiplier = Self::freshness_decay(created_at, 8);
        let complexity_multiplier = (step_count as f64 / 100.0).clamp(0.5, 3.0);
        
        let final_value = (base_value as f64) * reuse_multiplier * freshness_multiplier * complexity_multiplier * worker_trust;
        final_value as u64
    }

    /// Compute state hash
    fn compute_state_hash(&self, state_id: &str, model_cid: &str, layer_hashes: &[String], token_position: u32) -> String {
        let data = format!("{}{}{}{}", state_id, model_cid, layer_hashes.join(""), token_position);
        hex::encode(Sha256::digest(data.as_bytes()))
    }

    /// Compute prefill hash
    fn compute_prefill_hash(&self, prefill_id: &str, model_cid: &str, prompt_tokens: &[u32]) -> String {
        let data = format!("{}{}{}", prefill_id, model_cid, hex::encode(bincode::serialize(prompt_tokens).unwrap()));
        hex::encode(Sha256::digest(data.as_bytes()))
    }

    /// Compute attention hash
    fn compute_attention_hash(&self, attention_id: &str, model_cid: &str, layer_attention: &[LayerAttention]) -> String {
        let data = format!("{}{}{}", attention_id, model_cid, hex::encode(bincode::serialize(layer_attention).unwrap()));
        hex::encode(Sha256::digest(data.as_bytes()))
    }

    /// Compute context hash
    fn compute_context_hash(&self, context_id: &str, model_cid: &str, reasoning_trace: &[ReasoningStep]) -> String {
        let data = format!("{}{}{}", context_id, model_cid, hex::encode(bincode::serialize(reasoning_trace).unwrap()));
        hex::encode(Sha256::digest(data.as_bytes()))
    }

    /// Get KV-state record
    pub fn get_kv_state(&self, state_id: &str) -> Option<KVStateRecord> {
        self.kv_states.get(state_id).map(|r| r.clone())
    }

    /// Get prefill record
    pub fn get_prefill(&self, prefill_id: &str) -> Option<PrefillRecord> {
        self.prefills.get(prefill_id).map(|r| r.clone())
    }

    /// Get attention state record
    pub fn get_attention_state(&self, attention_id: &str) -> Option<AttentionStateRecord> {
        self.attention_states.get(attention_id).map(|r| r.clone())
    }

    /// Get reasoning context record
    pub fn get_reasoning_context(&self, context_id: &str) -> Option<ReasoningContextRecord> {
        self.reasoning_contexts.get(context_id).map(|r| r.clone())
    }

    /// Increment reuse count and recalculate collateral with live freshness decay
    pub fn increment_kv_reuse(&self, state_id: &str) -> Result<u64, String> {
        if let Some(mut record) = self.kv_states.get_mut(state_id) {
            if Utc::now() > record.expires_at {
                return Err("KV-state expired".to_string());
            }
            record.reuse_count += 1;
            record.collateral_value = self.calculate_kv_collateral(
                record.cache_size_bytes,
                record.context_length,
                record.reuse_count,
                1.0, // worker_trust re-fetched at relay validation time
                &record.created_at,
            );
            Ok(record.collateral_value)
        } else {
            Err("KV-state not found".to_string())
        }
    }

    /// Check if KV-state is expired
    pub fn is_kv_expired(&self, state_id: &str) -> bool {
        if let Some(record) = self.kv_states.get(state_id) {
            Utc::now() > record.expires_at
        } else {
            true
        }
    }

    /// Get total collateral value for a worker
    pub fn get_worker_total_collateral(&self, worker_id: &str) -> u64 {
        let mut total = 0u64;
        
        for kv in self.kv_states.iter() {
            if kv.worker_id == worker_id && !self.is_kv_expired(&kv.state_id) {
                total += kv.collateral_value;
            }
        }
        
        for prefill in self.prefills.iter() {
            if prefill.worker_id == worker_id && Utc::now() <= prefill.expires_at {
                total += prefill.collateral_value;
            }
        }
        
        for attention in self.attention_states.iter() {
            if attention.worker_id == worker_id && Utc::now() <= attention.expires_at {
                total += attention.collateral_value;
            }
        }
        
        for context in self.reasoning_contexts.iter() {
            if context.worker_id == worker_id && Utc::now() <= context.expires_at {
                total += context.collateral_value;
            }
        }
        
        total
    }

    /// Generate a challenge for a KV-state
    pub fn generate_kv_challenge(
        &self,
        state_id: &str,
        challenge_type: KVStateChallengeType,
        difficulty: f64,
    ) -> Result<String, String> {
        let record = self.kv_states.get(state_id)
            .ok_or("KV-state not found")?;
        
        if self.is_kv_expired(state_id) {
            return Err("KV-state is expired".to_string());
        }

        let challenge_id = format!("challenge_{}_{}", state_id, Utc::now().timestamp());
        let challenge_data = match challenge_type {
            KVStateChallengeType::DeterministicReproduction => {
                format!("reproduce_state:{}:{}", record.model_cid, record.token_position)
            }
            KVStateChallengeType::AttentionConsistency => {
                format!("verify_attention:{}:{}", record.model_cid, record.layer_hashes.join(","))
            }
            KVStateChallengeType::ReasoningTraceValidation => {
                format!("validate_trace:{}:{}", record.model_cid, record.context_length)
            }
            KVStateChallengeType::HashVerification => {
                format!("verify_hash:{}", record.state_hash)
            }
        };

        let now = Utc::now();
        let expires_at = now + Duration::minutes(30); // Challenges expire in 30 minutes

        let challenge = KVStateChallenge {
            challenge_id: challenge_id.clone(),
            state_id: state_id.to_string(),
            challenge_type,
            challenge_data,
            created_at: now,
            expires_at,
            difficulty,
        };

        self.challenges.insert(challenge_id.clone(), challenge);
        Ok(challenge_id)
    }

    /// Submit a challenge response
    pub fn submit_challenge_response(
        &self,
        response: KVStateChallengeResponse,
    ) -> Result<String, String> {
        let challenge = self.challenges.get(&response.challenge_id)
            .ok_or("Challenge not found")?;
        
        if Utc::now() > challenge.expires_at {
            return Err("Challenge has expired".to_string());
        }

        if challenge.state_id != response.state_id {
            return Err("State ID mismatch".to_string());
        }

        // Verify challenge response
        let result = self.verify_challenge_response(&challenge, &response);
        
        self.challenge_results.insert(
            response.challenge_id.clone(),
            result.clone()
        );
        
        // Remove completed challenge
        self.challenges.remove(&response.challenge_id);

        if result.passed {
            Ok(format!("Challenge passed with score: {}", result.score))
        } else {
            Err(format!("Challenge failed: {}", result.details))
        }
    }

    /// Verify a challenge response
    fn verify_challenge_response(
        &self,
        challenge: &KVStateChallenge,
        response: &KVStateChallengeResponse,
    ) -> KVStateChallengeResult {
        let now = Utc::now();
        
        match challenge.challenge_type {
            KVStateChallengeType::HashVerification => {
                // Verify the response contains the correct hash
                let record = self.kv_states.get(&challenge.state_id);
                if let Some(record) = record {
                    let expected_hash = record.state_hash.clone();
                    let passed = response.response_data.contains(&expected_hash);
                    
                    KVStateChallengeResult {
                        challenge_id: challenge.challenge_id.clone(),
                        state_id: challenge.state_id.clone(),
                        passed,
                        score: if passed { 1.0 } else { 0.0 },
                        details: if passed {
                            "Hash verification successful".to_string()
                        } else {
                            format!("Hash mismatch. Expected: {}", expected_hash)
                        },
                        verified_at: now,
                    }
                } else {
                    KVStateChallengeResult {
                        challenge_id: challenge.challenge_id.clone(),
                        state_id: challenge.state_id.clone(),
                        passed: false,
                        score: 0.0,
                        details: "State record not found".to_string(),
                        verified_at: now,
                    }
                }
            }
            KVStateChallengeType::DeterministicReproduction => {
                // In production, this would actually run the model and compare outputs
                // For now, we do a basic validation
                let passed = !response.response_data.is_empty();
                
                KVStateChallengeResult {
                    challenge_id: challenge.challenge_id.clone(),
                    state_id: challenge.state_id.clone(),
                    passed,
                    score: if passed { 0.9 } else { 0.0 },
                    details: if passed {
                        "Deterministic reproduction validated (stub)".to_string()
                    } else {
                        "Empty response data".to_string()
                    },
                    verified_at: now,
                }
            }
            KVStateChallengeType::AttentionConsistency => {
                // In production, this would compare attention patterns
                let passed = response.response_data.contains("attention");
                
                KVStateChallengeResult {
                    challenge_id: challenge.challenge_id.clone(),
                    state_id: challenge.state_id.clone(),
                    passed,
                    score: if passed { 0.85 } else { 0.0 },
                    details: if passed {
                        "Attention consistency validated (stub)".to_string()
                    } else {
                        "Attention pattern verification failed".to_string()
                    },
                    verified_at: now,
                }
            }
            KVStateChallengeType::ReasoningTraceValidation => {
                // In production, this would validate the reasoning trace
                let passed = response.response_data.contains("trace");
                
                KVStateChallengeResult {
                    challenge_id: challenge.challenge_id.clone(),
                    state_id: challenge.state_id.clone(),
                    passed,
                    score: if passed { 0.8 } else { 0.0 },
                    details: if passed {
                        "Reasoning trace validated (stub)".to_string()
                    } else {
                        "Reasoning trace validation failed".to_string()
                    },
                    verified_at: now,
                }
            }
        }
    }

    /// Get challenge result
    pub fn get_challenge_result(&self, challenge_id: &str) -> Option<KVStateChallengeResult> {
        self.challenge_results.get(challenge_id).map(|r| r.clone())
    }

    /// Get active challenges for a state
    pub fn get_active_challenges(&self, state_id: &str) -> Vec<KVStateChallenge> {
        self.challenges.iter()
            .filter(|c| c.state_id == state_id && Utc::now() <= c.expires_at)
            .map(|c| c.clone())
            .collect()
    }

    /// Clean up expired challenges
    pub fn cleanup_expired_challenges(&self) {
        let now = Utc::now();
        self.challenges.retain(|_, c| now <= c.expires_at);
    }
}
