use dashmap::DashMap;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use chrono::{DateTime, Utc, Duration};
use sha2::{Digest, Sha256};
use worker_reputation::{ReputationLedger, WorkerRegistry, WorkerStatus};
use kv_state_collateral::KVStateCollateral;
use memory_market::MemoryMarket;

/// MemGas Protocol: memory-collateralized gas abstraction
pub struct MemGasProtocol {
    /// Nonce ledger: prevents replay attacks
    nonce_ledger: Arc<DashMap<String, NonceRecord>>,
    
    /// Spend ledger: tracks memory credit spending
    spend_ledger: Arc<DashMap<String, SpendRecord>>,
    
    /// Memory market ledger: tracks collateral accounting
    memory_ledger: Arc<DashMap<String, MemoryMarketRecord>>,
    
    /// Worker registry
    worker_registry: Arc<WorkerRegistry>,
    
    /// Reputation ledger
    reputation_ledger: Arc<ReputationLedger>,
    
    /// KV-state collateral system (Phase 4)
    pub kv_collateral: Arc<KVStateCollateral>,

    /// Emergent memory market (Phase 3)
    pub memory_market: Arc<MemoryMarket>,
    
    /// Daily wallet caps
    daily_caps: Arc<RwLock<HashMap<String, u64>>>,
    
    /// Base credit per memory object (in lamports)
    base_credit: u64,
    
    /// Daily wallet cap (in lamports)
    daily_wallet_cap: u64,
    
    /// Memory expiration time (hours)
    memory_expiration_hours: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NonceRecord {
    pub owner_pubkey: String,
    pub nonce: String,
    pub used_at: DateTime<Utc>,
    pub tx_signature: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpendRecord {
    pub memory_cid: String,
    pub owner_pubkey: String,
    pub total_credit: u64,
    pub remaining_credit: u64,
    pub created_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryMarketRecord {
    pub memory_cid: String,
    pub model_cid: String,
    pub reuse_score: f64,
    pub decay_rate: f64,
    pub collateral_value: u64,
    pub total_uses: u64,
    pub last_used_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GasCredit {
    pub memory_cid: String,
    pub available_lamports: u64,
    pub expires_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserIntent {
    pub owner_pubkey: String,
    pub nonce: String,
    pub requested_lamports: u64,
    pub memory_cid: String,
    pub tx_data: String,
    pub signature: String,
}

impl MemGasProtocol {
    pub fn new(base_credit: u64, daily_wallet_cap: u64, memory_expiration_hours: i64) -> Self {
        Self {
            nonce_ledger: Arc::new(DashMap::new()),
            spend_ledger: Arc::new(DashMap::new()),
            memory_ledger: Arc::new(DashMap::new()),
            worker_registry: Arc::new(WorkerRegistry::new()),
            reputation_ledger: Arc::new(ReputationLedger::new(0.5)),
            kv_collateral: Arc::new(KVStateCollateral::new()),
            memory_market: Arc::new(MemoryMarket::new()),
            daily_caps: Arc::new(RwLock::new(HashMap::new())),
            base_credit,
            daily_wallet_cap,
            memory_expiration_hours,
        }
    }
    
    /// Register a new memory object in the market with worker trust weighting
    pub fn register_memory(
        &self,
        memory_cid: String,
        model_cid: String,
        reuse_score: f64,
        owner_pubkey: String,
        worker_id: String,
    ) -> Result<(), String> {
        // Check if worker is registered (Acceptance Criteria 1)
        let worker = self.worker_registry.get_worker(&worker_id)
            .ok_or("Worker not registered")?;
        
        // Check if worker is banned (Acceptance Criteria 5)
        if matches!(worker.status, WorkerStatus::Banned) {
            return Err("Worker is banned - cannot generate gas credit".to_string());
        }
        
        // Get worker trust multiplier
        let worker_trust_multiplier = self.reputation_ledger.get_trust_multiplier(&worker_id);
        
        // If multiplier is 0, reject (Acceptance Criteria 5)
        if worker_trust_multiplier == 0.0 {
            return Err("Worker trust too low - cannot generate gas credit".to_string());
        }
        
        // Phase 3: register in emergent memory market (empty token_ids — will be populated via record_retrieval)
        // reuse_score from caller used as initial heuristic until emergent signals accumulate
        let _ = self.memory_market.register_memory(
            memory_cid.clone(),
            model_cid.clone(),
            owner_pubkey.clone(),
            worker_id.clone(),
            &[],   // token_ids populated later via attention reuse events
            0,     // layer_count populated later
            worker_trust_multiplier,
        );

        // Calculate collateral value: blend heuristic reuse_score with emergent score
        // On first registration emergent score = 0 so heuristic dominates; converges as signals arrive
        let emergent_score = self.memory_market
            .get_record(&memory_cid)
            .map(|r| r.emergent_reuse_score)
            .unwrap_or(0.0);
        let blended_score = reuse_score * 0.6 + emergent_score * 0.4;

        let collateral_value = self.calculate_collateral_value_with_worker(
            blended_score,
            worker_trust_multiplier,
            1.0,
        );
        
        let now = Utc::now();
        let expires_at = now + Duration::hours(self.memory_expiration_hours);
        
        let record = MemoryMarketRecord {
            memory_cid: memory_cid.clone(),
            model_cid,
            reuse_score: blended_score,
            decay_rate: 0.03,
            collateral_value,
            total_uses: 0,
            last_used_at: now,
        };
        
        self.memory_ledger.insert(memory_cid.clone(), record);
        
        let spend_record = SpendRecord {
            memory_cid: memory_cid.clone(),
            owner_pubkey,
            total_credit: collateral_value,
            remaining_credit: collateral_value,
            created_at: now,
            expires_at,
        };
        
        self.spend_ledger.insert(memory_cid, spend_record);
        
        Ok(())
    }

    /// Record a retrieval event and reprice the memory via emergent market
    pub fn record_market_retrieval(
        &self,
        memory_cid: &str,
        worker_id: &str,
    ) -> Result<u64, String> {
        let worker_trust = self.reputation_ledger.get_trust_multiplier(worker_id);
        let price_point = self.memory_market.record_retrieval(memory_cid, worker_id, worker_trust)
            .map_err(|e| format!("Market retrieval failed: {}", e))?;

        // Sync updated market price back into spend ledger credit
        if let Some(mut spend) = self.spend_ledger.get_mut(memory_cid) {
            let new_credit = price_point.price_lamports.max(spend.total_credit);
            spend.total_credit = new_credit;
            if spend.remaining_credit < new_credit {
                spend.remaining_credit = new_credit;
            }
        }
        Ok(price_point.price_lamports)
    }

    /// Record downstream reference between inferences
    pub fn record_market_reference(
        &self,
        source_memory_cid: &str,
        referencing_inference_id: &str,
        worker_id: &str,
    ) -> Result<u64, String> {
        let worker_trust = self.reputation_ledger.get_trust_multiplier(worker_id);
        let price_point = self.memory_market.record_downstream_reference(
            source_memory_cid,
            referencing_inference_id,
            worker_trust,
        ).map_err(|e| format!("Market reference failed: {}", e))?;
        Ok(price_point.price_lamports)
    }

    /// Record attention reuse from KV-state layers (Phase 3 + Phase 4 integration point)
    pub fn record_attention_reuse(
        &self,
        memory_cid: &str,
        layer_activation_count: u32,
        total_layers: u32,
        worker_id: &str,
    ) -> Result<u64, String> {
        let worker_trust = self.reputation_ledger.get_trust_multiplier(worker_id);
        let price_point = self.memory_market.record_attention_reuse(
            memory_cid,
            layer_activation_count,
            total_layers,
            worker_trust,
        ).map_err(|e| format!("Attention reuse failed: {}", e))?;
        Ok(price_point.price_lamports)
    }

    /// Get emergent market record for a memory CID
    pub fn get_market_record(&self, memory_cid: &str) -> Option<memory_market::MarketRecord> {
        self.memory_market.get_record(memory_cid)
    }

    /// Get top memories by emergent reuse score
    pub fn top_memories(&self, n: usize) -> Vec<memory_market::MarketRecord> {
        self.memory_market.top_memories_by_score(n)
    }

    /// Get total market liquidity (lamports priced across all memory objects)
    pub fn market_liquidity(&self) -> u64 {
        self.memory_market.total_market_liquidity()
    }
    
    /// Calculate collateral value from scoring factors
    fn calculate_collateral_value(&self, reuse_score: f64, worker_trust: f64, proof_validity: f64) -> u64 {
        let base = self.base_credit as f64;
        let decay = 1.0 - 0.03; // 3% decay
        let anti_sybil = 1.0;
        
        let credit = base * proof_validity * reuse_score * worker_trust * decay * anti_sybil;
        credit as u64
    }
    
    /// Calculate collateral value with worker trust multiplier (Phase 2E)
    fn calculate_collateral_value_with_worker(&self, reuse_score: f64, worker_trust_multiplier: f64, proof_validity: f64) -> u64 {
        let base = self.base_credit as f64;
        let decay = 1.0 - 0.03;
        let anti_sybil = 1.0;
        
        let credit = base * proof_validity * reuse_score * worker_trust_multiplier * decay * anti_sybil;
        credit as u64
    }
    
    /// Check if nonce is already used
    pub fn is_nonce_used(&self, owner_pubkey: &str, nonce: &str) -> bool {
        let key = format!("{}:{}", owner_pubkey, nonce);
        self.nonce_ledger.contains_key(&key)
    }
    
    /// Mark nonce as used
    pub fn mark_nonce_used(&self, owner_pubkey: String, nonce: String, tx_signature: Option<String>) {
        let key = format!("{}:{}", owner_pubkey, nonce);
        let record = NonceRecord {
            owner_pubkey,
            nonce,
            used_at: Utc::now(),
            tx_signature,
        };
        self.nonce_ledger.insert(key, record);
    }
    
    /// Get remaining credit for a memory object
    pub fn get_remaining_credit(&self, memory_cid: &str) -> Option<u64> {
        self.spend_ledger.get(memory_cid).map(|r| r.remaining_credit)
    }
    
    /// Check if memory is expired
    pub fn is_memory_expired(&self, memory_cid: &str) -> bool {
        if let Some(record) = self.spend_ledger.get(memory_cid) {
            Utc::now() > record.expires_at
        } else {
            true
        }
    }
    
    /// Get daily spend for a wallet (keyed by wallet + UTC date)
    pub fn get_daily_spend(&self, pubkey: &str) -> u64 {
        let today = chrono::Utc::now().format("%Y-%m-%d").to_string();
        let key = format!("wallet:{}:daily_spend:{}", pubkey, today);
        self.daily_caps.read().get(&key).copied().unwrap_or(0)
    }
    
    /// Check if wallet exceeds daily cap
    pub fn exceeds_daily_cap(&self, pubkey: &str, additional: u64) -> bool {
        let current = self.get_daily_spend(pubkey);
        current + additional > self.daily_wallet_cap
    }
    
    /// Validate and execute relay request
    pub fn validate_relay(&self, intent: &UserIntent) -> Result<u64, String> {
        // Check nonce not replayed
        if self.is_nonce_used(&intent.owner_pubkey, &intent.nonce) {
            return Err("Nonce already used".to_string());
        }
        
        // Check memory not expired
        if self.is_memory_expired(&intent.memory_cid) {
            return Err("Memory expired".to_string());
        }
        
        // Check sufficient credit
        let remaining = self.get_remaining_credit(&intent.memory_cid)
            .ok_or("Memory not found")?;
        
        if intent.requested_lamports > remaining {
            return Err("Insufficient credit".to_string());
        }
        
        // Check daily cap
        if self.exceeds_daily_cap(&intent.owner_pubkey, intent.requested_lamports) {
            return Err("Daily cap exceeded".to_string());
        }
        
        // Mark nonce as used
        self.mark_nonce_used(intent.owner_pubkey.clone(), intent.nonce.clone(), None);
        
        // Deduct credit
        self.deduct_credit(&intent.memory_cid, intent.requested_lamports)?;
        
        // Update daily spend
        self.update_daily_spend(&intent.owner_pubkey, intent.requested_lamports);
        
        Ok(intent.requested_lamports)
    }
    
    /// Deduct credit from memory
    fn deduct_credit(&self, memory_cid: &str, amount: u64) -> Result<(), String> {
        if let Some(mut record) = self.spend_ledger.get_mut(memory_cid) {
            if record.remaining_credit < amount {
                return Err("Insufficient credit".to_string());
            }
            record.remaining_credit -= amount;
            Ok(())
        } else {
            Err("Memory not found".to_string())
        }
    }
    
    /// Update daily spend for wallet
    fn update_daily_spend(&self, pubkey: &str, amount: u64) {
        let today = chrono::Utc::now().format("%Y-%m-%d").to_string();
        let key = format!("wallet:{}:daily_spend:{}", pubkey, today);
        let mut caps = self.daily_caps.write();
        let entry = caps.entry(key).or_insert(0);
        *entry += amount;
    }
    
    /// Register KV-state as collateral (Phase 4)
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
    ) -> Result<String, String> {
        let worker = self.worker_registry.get_worker(&worker_id)
            .ok_or("Worker not registered")?;
        
        if matches!(worker.status, WorkerStatus::Banned) {
            return Err("Worker is banned".to_string());
        }
        
        let worker_trust = self.reputation_ledger.get_trust_multiplier(&worker_id);
        if worker_trust == 0.0 {
            return Err("Worker trust too low".to_string());
        }
        
        self.kv_collateral.register_kv_state(
            state_id.clone(),
            model_cid,
            layer_hashes,
            cache_size_bytes,
            token_position,
            context_length,
            owner_pubkey,
            worker_id,
            worker_trust,
        )
    }
    
    /// Register prefill as collateral (Phase 4)
    pub fn register_prefill(
        &self,
        prefill_id: String,
        model_cid: String,
        prompt_tokens: Vec<u32>,
        prefill_length: u32,
        owner_pubkey: String,
        worker_id: String,
    ) -> Result<String, String> {
        let worker_trust = self.reputation_ledger.get_trust_multiplier(&worker_id);
        self.kv_collateral.register_prefill(
            prefill_id.clone(),
            model_cid,
            prompt_tokens,
            prefill_length,
            owner_pubkey,
            worker_id,
            worker_trust,
        )
    }
    
    /// Get total collateral for a worker (memory + KV-state)
    pub fn get_worker_total_collateral(&self, worker_id: &str) -> u64 {
        self.kv_collateral.get_worker_total_collateral(worker_id)
    }
    
    /// Increment KV-state reuse and recalculate value
    pub fn increment_kv_reuse(&self, state_id: &str) -> Result<u64, String> {
        self.kv_collateral.increment_kv_reuse(state_id)
    }
    
    /// Update token_count and layer_count on an already-registered market record.
    /// Call this after KV-state registration so score_to_price has real dimensions.
    pub fn set_memory_kv_params(&self, memory_cid: &str, token_count: u32, layer_count: u32) {
        if let Some(mut record) = self.memory_market.catalog_mut(memory_cid) {
            record.token_count = token_count;
            record.layer_count = layer_count;
        }
    }

    /// Expose worker registry for demo / integration use
    pub fn worker_registry(&self) -> &WorkerRegistry {
        &self.worker_registry
    }

    /// Expose reputation ledger for demo / integration use
    pub fn reputation_ledger(&self) -> &ReputationLedger {
        &self.reputation_ledger
    }

    /// Mutable spend record accessor (for demo credit adjustment)
    pub fn spend_ledger_mut(&self, memory_cid: &str) -> Option<dashmap::mapref::one::RefMut<'_, String, SpendRecord>> {
        self.spend_ledger.get_mut(memory_cid)
    }

    /// Update memory reuse score
    pub fn update_reuse_score(&self, memory_cid: String, new_score: f64) {
        if let Some(mut record) = self.memory_ledger.get_mut(&memory_cid) {
            record.reuse_score = new_score;
            record.total_uses += 1;
            record.last_used_at = Utc::now();
            
            let new_value = self.calculate_collateral_value(
                new_score,
                1.0,
                1.0,
            );
            record.collateral_value = new_value;
        }
    }
}
