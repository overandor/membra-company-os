use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::sync::Arc;
use chrono::{DateTime, Duration, Utc};

/// Downstream reference graph.
///
/// Tracks which inferences (by inference_id) referenced a given memory CID.
/// Reference density = unique_references_in_window / REF_DENSITY_CAP.
///
/// A "downstream reference" is when:
///   - Inference B uses a KV-state prefill that originated from Memory A
///   - Or inference B's prompt overlaps semantically with Memory A's context
const REF_WINDOW_HOURS: i64 = 48;
const REF_DENSITY_CAP: f64 = 50.0;

#[derive(Debug)]
pub struct ReferenceGraph {
    /// memory_cid → set of (inference_id, timestamp)
    refs: Arc<DashMap<String, Vec<ReferenceEdge>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReferenceEdge {
    pub inference_id: String,
    pub referenced_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReferenceStats {
    pub total_references: usize,
    pub unique_inferences: usize,
    pub window_references: usize,
    pub density_score: f64,
}

impl ReferenceGraph {
    pub fn new() -> Self {
        Self {
            refs: Arc::new(DashMap::new()),
        }
    }

    /// Add a reference edge: inference `referencing_inference_id` referenced `source_memory_cid`
    pub fn add_reference(&self, source_memory_cid: &str, referencing_inference_id: &str) {
        let edge = ReferenceEdge {
            inference_id: referencing_inference_id.to_string(),
            referenced_at: Utc::now(),
        };

        self.refs
            .entry(source_memory_cid.to_string())
            .or_insert_with(Vec::new)
            .push(edge);
    }

    /// Reference density in [0.0, 1.0] using a 48h window of unique downstream inferences
    pub fn reference_density(&self, memory_cid: &str) -> f64 {
        if let Some(edges) = self.refs.get(memory_cid) {
            let cutoff = Utc::now() - Duration::hours(REF_WINDOW_HOURS);
            let unique: HashSet<&str> = edges
                .iter()
                .filter(|e| e.referenced_at >= cutoff)
                .map(|e| e.inference_id.as_str())
                .collect();
            (unique.len() as f64 / REF_DENSITY_CAP).min(1.0)
        } else {
            0.0
        }
    }

    /// Full reference stats for a memory CID
    pub fn stats(&self, memory_cid: &str) -> ReferenceStats {
        if let Some(edges) = self.refs.get(memory_cid) {
            let cutoff = Utc::now() - Duration::hours(REF_WINDOW_HOURS);
            let total = edges.len();
            let all_ids: HashSet<&str> = edges.iter().map(|e| e.inference_id.as_str()).collect();
            let window_edges: Vec<&ReferenceEdge> = edges.iter().filter(|e| e.referenced_at >= cutoff).collect();
            let window_ids: HashSet<&str> = window_edges.iter().map(|e| e.inference_id.as_str()).collect();
            let density = (window_ids.len() as f64 / REF_DENSITY_CAP).min(1.0);

            ReferenceStats {
                total_references: total,
                unique_inferences: all_ids.len(),
                window_references: window_edges.len(),
                density_score: density,
            }
        } else {
            ReferenceStats {
                total_references: 0,
                unique_inferences: 0,
                window_references: 0,
                density_score: 0.0,
            }
        }
    }

    /// Outbound fan-out: how many *other* memories does a given inference reference?
    /// Used for cross-reference depth analysis.
    pub fn memories_referenced_by(&self, inference_id: &str) -> Vec<String> {
        self.refs
            .iter()
            .filter(|entry| entry.value().iter().any(|e| e.inference_id == inference_id))
            .map(|entry| entry.key().clone())
            .collect()
    }
}

impl Default for ReferenceGraph {
    fn default() -> Self {
        Self::new()
    }
}
