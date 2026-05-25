use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use parking_lot::RwLock;
use sha2::{Digest, Sha256};

/// Emergent Pricing Engine
///
/// Converts emergent reuse scores into lamport prices.
/// Also manages semantic clusters for cosine-proxy similarity scoring.
///
/// Pricing formula:
///   base_price   = token_count * BASE_LAMPORTS_PER_TOKEN + layer_count * BASE_LAMPORTS_PER_LAYER
///   market_price = base_price * (1 + score * SCORE_MULTIPLIER) * worker_trust
///
/// Semantic similarity uses the embedding fingerprint (SHA256 of first 256 token IDs)
/// as a Hamming-distance proxy for cluster cohesion.

const BASE_LAMPORTS_PER_TOKEN: u64 = 5;
const BASE_LAMPORTS_PER_LAYER: u64 = 200;
const SCORE_MULTIPLIER: f64 = 9.0; // max 10x at score=1.0
const MIN_LAMPORTS: u64 = 1_000;

/// Cluster bucket: memories grouped by model_cid + fingerprint prefix
#[derive(Debug, Clone)]
pub struct SemanticCluster {
    pub model_cid: String,
    /// fingerprint prefix (first 4 bytes) used as cluster key
    pub prefix: [u8; 4],
    /// member memory CIDs
    pub members: Vec<String>,
}

pub struct EmergentPricingEngine {
    /// model_cid → (prefix_hex → cluster)
    clusters: Arc<RwLock<HashMap<String, HashMap<String, SemanticCluster>>>>,
    /// memory_cid → cluster key (for fast reverse lookup)
    cid_to_cluster: Arc<DashMap<String, (String, String)>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PricingParams {
    pub base_lamports_per_token: u64,
    pub base_lamports_per_layer: u64,
    pub score_multiplier: f64,
    pub min_lamports: u64,
}

impl EmergentPricingEngine {
    pub fn new() -> Self {
        Self {
            clusters: Arc::new(RwLock::new(HashMap::new())),
            cid_to_cluster: Arc::new(DashMap::new()),
        }
    }

    /// Compute base price (no score applied yet)
    pub fn compute_base_price(&self, token_count: u32, layer_count: u32, worker_trust: f64) -> u64 {
        let base = token_count as u64 * BASE_LAMPORTS_PER_TOKEN
            + layer_count as u64 * BASE_LAMPORTS_PER_LAYER;
        let trusted = (base as f64 * worker_trust) as u64;
        trusted.max(MIN_LAMPORTS)
    }

    /// Convert emergent reuse score → market price in lamports
    pub fn score_to_price(&self, score: f64, token_count: u32, layer_count: u32) -> u64 {
        let base = token_count as u64 * BASE_LAMPORTS_PER_TOKEN
            + layer_count as u64 * BASE_LAMPORTS_PER_LAYER;
        let multiplied = (base as f64 * (1.0 + score * SCORE_MULTIPLIER)) as u64;
        multiplied.max(MIN_LAMPORTS)
    }

    /// Register a memory in its semantic cluster (model_cid + fingerprint prefix)
    pub fn register_in_cluster(
        &self,
        memory_cid: String,
        model_cid: String,
        fingerprint: [u8; 32],
    ) {
        let prefix: [u8; 4] = fingerprint[..4].try_into().unwrap_or([0u8; 4]);
        let prefix_hex = hex::encode(prefix);

        let mut clusters = self.clusters.write();
        let model_clusters = clusters.entry(model_cid.clone()).or_insert_with(HashMap::new);

        let cluster = model_clusters.entry(prefix_hex.clone()).or_insert_with(|| SemanticCluster {
            model_cid: model_cid.clone(),
            prefix,
            members: Vec::new(),
        });

        if !cluster.members.contains(&memory_cid) {
            cluster.members.push(memory_cid.clone());
        }

        self.cid_to_cluster.insert(memory_cid, (model_cid, prefix_hex));
    }

    /// Cluster cohesion score for a memory CID.
    ///
    /// Cohesion = cluster_size_score * density_bonus
    /// cluster_size_score = sigmoid(members / COHESION_TARGET)
    /// This rewards memories in dense clusters (many similar memories = higher demand domain).
    pub fn cluster_cohesion(&self, memory_cid: &str) -> f64 {
        const COHESION_TARGET: f64 = 20.0;

        if let Some(entry) = self.cid_to_cluster.get(memory_cid) {
            let (model_cid, prefix_hex) = entry.value();
            let clusters = self.clusters.read();
            if let Some(model_clusters) = clusters.get(model_cid) {
                if let Some(cluster) = model_clusters.get(prefix_hex) {
                    let size = cluster.members.len() as f64;
                    // Soft sigmoid: 1 / (1 + e^(-k*(x - target/2)))
                    let k = 0.3;
                    let x = size - COHESION_TARGET / 2.0;
                    let cohesion = 1.0 / (1.0 + (-k * x).exp());
                    return cohesion.clamp(0.0, 1.0);
                }
            }
        }
        0.0
    }

    /// Hamming distance between two fingerprints (used in testing / cross-cluster checks)
    pub fn fingerprint_hamming(a: &[u8; 32], b: &[u8; 32]) -> u32 {
        a.iter().zip(b.iter()).map(|(x, y)| (x ^ y).count_ones()).sum()
    }

    /// Normalized similarity from Hamming distance: 1.0 = identical, 0.0 = maximally different
    pub fn fingerprint_similarity(a: &[u8; 32], b: &[u8; 32]) -> f64 {
        let hamming = Self::fingerprint_hamming(a, b) as f64;
        let max_distance = 256.0; // 32 bytes × 8 bits
        1.0 - (hamming / max_distance)
    }

    /// Get current pricing params
    pub fn params() -> PricingParams {
        PricingParams {
            base_lamports_per_token: BASE_LAMPORTS_PER_TOKEN,
            base_lamports_per_layer: BASE_LAMPORTS_PER_LAYER,
            score_multiplier: SCORE_MULTIPLIER,
            min_lamports: MIN_LAMPORTS,
        }
    }

    /// Cluster size for a given memory CID
    pub fn cluster_size(&self, memory_cid: &str) -> usize {
        if let Some(entry) = self.cid_to_cluster.get(memory_cid) {
            let (model_cid, prefix_hex) = entry.value();
            let clusters = self.clusters.read();
            if let Some(model_clusters) = clusters.get(model_cid) {
                if let Some(cluster) = model_clusters.get(prefix_hex) {
                    return cluster.members.len();
                }
            }
        }
        0
    }
}

impl Default for EmergentPricingEngine {
    fn default() -> Self {
        Self::new()
    }
}
