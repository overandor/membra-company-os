use dashmap::DashMap;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use chrono::{DateTime, Duration, Utc};
use sha2::{Digest, Sha256};

pub mod retrieval;
pub mod reference_graph;
pub mod attention_density;
pub mod pricing_engine;

pub use retrieval::RetrievalTracker;
pub use reference_graph::ReferenceGraph;
pub use attention_density::AttentionDensityTracker;
pub use pricing_engine::EmergentPricingEngine;

/// Phase 3: Emergent Memory Market
///
/// reuse_score transitions from heuristic → emergent:
///   score = f(retrieval_frequency, downstream_references, semantic_similarity, attention_reuse_density)
///
/// Worker trust (Phase 2) gates all score contributions.
pub struct MemoryMarket {
    /// Retrieval frequency tracker
    retrieval: Arc<RetrievalTracker>,
    /// Downstream reference graph
    references: Arc<ReferenceGraph>,
    /// Attention reuse density tracker
    attention_density: Arc<AttentionDensityTracker>,
    /// Emergent pricing engine
    pricing: Arc<EmergentPricingEngine>,
    /// Memory catalog: memory_cid → MarketRecord
    catalog: Arc<DashMap<String, MarketRecord>>,
    /// Price history for each memory_cid
    price_history: Arc<DashMap<String, Vec<PricePoint>>>,
}

/// Full market record for a memory object
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketRecord {
    pub memory_cid: String,
    pub model_cid: String,
    pub owner_pubkey: String,
    pub worker_id: String,
    /// Embedding fingerprint: SHA256 of first 256 tokens' IDs (proxy for semantic similarity)
    pub embedding_fingerprint: [u8; 32],
    /// Token count of the memory object
    pub token_count: u32,
    /// Layer count (from KV state if available)
    pub layer_count: u32,
    pub registered_at: DateTime<Utc>,
    /// Current emergent reuse score (0.0 – 1.0)
    pub emergent_reuse_score: f64,
    /// Breakdown of score components
    pub score_breakdown: ScoreBreakdown,
    /// Derived market price in lamports
    pub market_price_lamports: u64,
    /// Total number of times retrieved
    pub retrieval_count: u64,
    /// Number of downstream inferences that referenced this memory
    pub downstream_reference_count: u64,
}

/// Score component breakdown for transparency
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScoreBreakdown {
    /// Normalized retrieval frequency (0.0 – 1.0)
    pub retrieval_frequency: f64,
    /// Downstream reference density (0.0 – 1.0)
    pub reference_density: f64,
    /// Semantic cluster cohesion (0.0 – 1.0)
    pub semantic_similarity: f64,
    /// Attention reuse density from KV-state (0.0 – 1.0)
    pub attention_reuse_density: f64,
    /// Worker trust multiplier from Phase 2 (0.0 – 1.0)
    pub worker_trust_multiplier: f64,
    /// Final weighted composite
    pub composite_score: f64,
}

/// Historical price point for a memory object
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PricePoint {
    pub timestamp: DateTime<Utc>,
    pub price_lamports: u64,
    pub reuse_score: f64,
    pub trigger: PriceTrigger,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PriceTrigger {
    Retrieval,
    DownstreamReference,
    AttentionReuse,
    SemanticClusterUpdate,
    WorkerTrustUpdate,
    Expiry,
}

impl MemoryMarket {
    pub fn new() -> Self {
        Self {
            retrieval: Arc::new(RetrievalTracker::new()),
            references: Arc::new(ReferenceGraph::new()),
            attention_density: Arc::new(AttentionDensityTracker::new()),
            pricing: Arc::new(EmergentPricingEngine::new()),
            catalog: Arc::new(DashMap::new()),
            price_history: Arc::new(DashMap::new()),
        }
    }

    /// Register a new memory object in the market
    pub fn register_memory(
        &self,
        memory_cid: String,
        model_cid: String,
        owner_pubkey: String,
        worker_id: String,
        token_ids: &[u32],
        layer_count: u32,
        worker_trust: f64,
    ) -> Result<MarketRecord, String> {
        if self.catalog.contains_key(&memory_cid) {
            return Err("Memory already registered".to_string());
        }

        let embedding_fingerprint = Self::compute_embedding_fingerprint(token_ids);
        let token_count = token_ids.len() as u32;

        let score_breakdown = ScoreBreakdown {
            retrieval_frequency: 0.0,
            reference_density: 0.0,
            semantic_similarity: 0.0,
            attention_reuse_density: 0.0,
            worker_trust_multiplier: worker_trust,
            composite_score: 0.0,
        };

        let market_price_lamports = self.pricing.compute_base_price(token_count, layer_count, worker_trust);

        let record = MarketRecord {
            memory_cid: memory_cid.clone(),
            model_cid: model_cid.clone(),
            owner_pubkey,
            worker_id: worker_id.clone(),
            embedding_fingerprint,
            token_count,
            layer_count,
            registered_at: Utc::now(),
            emergent_reuse_score: 0.0,
            score_breakdown,
            market_price_lamports,
            retrieval_count: 0,
            downstream_reference_count: 0,
        };

        self.catalog.insert(memory_cid.clone(), record.clone());

        // Register in semantic cluster
        self.pricing.register_in_cluster(
            memory_cid.clone(),
            model_cid,
            embedding_fingerprint,
        );

        Ok(record)
    }

    /// Record a retrieval event — updates frequency score and reprices
    pub fn record_retrieval(
        &self,
        memory_cid: &str,
        retriever_worker_id: &str,
        worker_trust: f64,
    ) -> Result<PricePoint, String> {
        self.retrieval.record(memory_cid, retriever_worker_id);

        if let Some(mut record) = self.catalog.get_mut(memory_cid) {
            record.retrieval_count += 1;
            let freq_score = self.retrieval.normalized_frequency(memory_cid);
            record.score_breakdown.retrieval_frequency = freq_score;
            record.score_breakdown.worker_trust_multiplier = worker_trust;
            self.recompute_score(&mut record);

            let price_point = PricePoint {
                timestamp: Utc::now(),
                price_lamports: record.market_price_lamports,
                reuse_score: record.emergent_reuse_score,
                trigger: PriceTrigger::Retrieval,
            };

            self.price_history
                .entry(memory_cid.to_string())
                .or_insert_with(Vec::new)
                .push(price_point.clone());

            Ok(price_point)
        } else {
            Err("Memory not found".to_string())
        }
    }

    /// Record a downstream reference: inference B referenced memory A
    pub fn record_downstream_reference(
        &self,
        source_memory_cid: &str,
        referencing_inference_id: &str,
        referencing_worker_trust: f64,
    ) -> Result<PricePoint, String> {
        self.references.add_reference(source_memory_cid, referencing_inference_id);

        if let Some(mut record) = self.catalog.get_mut(source_memory_cid) {
            record.downstream_reference_count += 1;
            let ref_density = self.references.reference_density(source_memory_cid);
            record.score_breakdown.reference_density = ref_density;
            record.score_breakdown.worker_trust_multiplier = referencing_worker_trust;
            self.recompute_score(&mut record);

            let price_point = PricePoint {
                timestamp: Utc::now(),
                price_lamports: record.market_price_lamports,
                reuse_score: record.emergent_reuse_score,
                trigger: PriceTrigger::DownstreamReference,
            };

            self.price_history
                .entry(source_memory_cid.to_string())
                .or_insert_with(Vec::new)
                .push(price_point.clone());

            Ok(price_point)
        } else {
            Err("Memory not found".to_string())
        }
    }

    /// Record attention reuse from KV-state layer activations
    pub fn record_attention_reuse(
        &self,
        memory_cid: &str,
        layer_activation_count: u32,
        total_layers: u32,
        worker_trust: f64,
    ) -> Result<PricePoint, String> {
        self.attention_density.record_activation(memory_cid, layer_activation_count, total_layers);

        if let Some(mut record) = self.catalog.get_mut(memory_cid) {
            let density = self.attention_density.density(memory_cid);
            record.score_breakdown.attention_reuse_density = density;
            record.score_breakdown.worker_trust_multiplier = worker_trust;
            self.recompute_score(&mut record);

            let price_point = PricePoint {
                timestamp: Utc::now(),
                price_lamports: record.market_price_lamports,
                reuse_score: record.emergent_reuse_score,
                trigger: PriceTrigger::AttentionReuse,
            };

            self.price_history
                .entry(memory_cid.to_string())
                .or_insert_with(Vec::new)
                .push(price_point.clone());

            Ok(price_point)
        } else {
            Err("Memory not found".to_string())
        }
    }

    /// Update semantic similarity score by recomputing cluster cohesion
    pub fn update_semantic_cluster(
        &self,
        memory_cid: &str,
        worker_trust: f64,
    ) -> Result<PricePoint, String> {
        let similarity = self.pricing.cluster_cohesion(memory_cid);

        if let Some(mut record) = self.catalog.get_mut(memory_cid) {
            record.score_breakdown.semantic_similarity = similarity;
            record.score_breakdown.worker_trust_multiplier = worker_trust;
            self.recompute_score(&mut record);

            let price_point = PricePoint {
                timestamp: Utc::now(),
                price_lamports: record.market_price_lamports,
                reuse_score: record.emergent_reuse_score,
                trigger: PriceTrigger::SemanticClusterUpdate,
            };

            self.price_history
                .entry(memory_cid.to_string())
                .or_insert_with(Vec::new)
                .push(price_point.clone());

            Ok(price_point)
        } else {
            Err("Memory not found".to_string())
        }
    }

    /// Get current market record
    pub fn get_record(&self, memory_cid: &str) -> Option<MarketRecord> {
        self.catalog.get(memory_cid).map(|r| r.clone())
    }

    /// Mutable access to a catalog record (for updating token/layer counts after KV-state link)
    pub fn catalog_mut(&self, memory_cid: &str) -> Option<dashmap::mapref::one::RefMut<'_, String, MarketRecord>> {
        self.catalog.get_mut(memory_cid)
    }

    /// Get price history for a memory
    pub fn get_price_history(&self, memory_cid: &str) -> Vec<PricePoint> {
        self.price_history
            .get(memory_cid)
            .map(|h| h.clone())
            .unwrap_or_default()
    }

    /// Get top-N memories by emergent reuse score
    pub fn top_memories_by_score(&self, n: usize) -> Vec<MarketRecord> {
        let mut records: Vec<MarketRecord> = self.catalog
            .iter()
            .map(|r| r.clone())
            .collect();
        records.sort_by(|a, b| b.emergent_reuse_score.partial_cmp(&a.emergent_reuse_score).unwrap());
        records.truncate(n);
        records
    }

    /// Get market liquidity: total priced lamports across all memory objects
    pub fn total_market_liquidity(&self) -> u64 {
        self.catalog.iter().map(|r| r.market_price_lamports).sum()
    }

    /// Recompute composite score and market price from breakdown components.
    /// Called internally after any score signal update.
    fn recompute_score(&self, record: &mut MarketRecord) {
        let bd = &record.score_breakdown;

        // Weighted composite — weights determined by signal reliability:
        // Retrieval frequency:      30% (direct observed demand)
        // Downstream references:    25% (verified cross-inference coupling)
        // Semantic similarity:      20% (cluster cohesion, lazy proxy)
        // Attention reuse density:  25% (strongest KV-state signal)
        let raw_score = bd.retrieval_frequency       * 0.30
            + bd.reference_density                   * 0.25
            + bd.semantic_similarity                 * 0.20
            + bd.attention_reuse_density             * 0.25;

        // Worker trust gates all signals (Phase 2 weighting layer)
        let gated_score = raw_score * bd.worker_trust_multiplier;
        let composite = gated_score.clamp(0.0, 1.0);

        record.score_breakdown.composite_score = composite;
        record.emergent_reuse_score = composite;
        record.market_price_lamports = self.pricing.score_to_price(
            composite,
            record.token_count,
            record.layer_count,
        );
    }

    /// Compute embedding fingerprint: SHA256 of first 256 token IDs
    fn compute_embedding_fingerprint(token_ids: &[u32]) -> [u8; 32] {
        let sample: Vec<u8> = token_ids
            .iter()
            .take(256)
            .flat_map(|t| t.to_be_bytes().to_vec())
            .collect();
        Sha256::digest(&sample).into()
    }
}

impl Default for MemoryMarket {
    fn default() -> Self {
        Self::new()
    }
}
