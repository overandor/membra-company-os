use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use chrono::{DateTime, Duration, Utc};

/// Attention reuse density tracker.
///
/// Measures what fraction of a memory's KV-state layers were actually activated
/// during downstream inference reuse events.
///
/// density = sum(activated_layers) / sum(total_layers) across all reuse events in 24h window
const DENSITY_WINDOW_HOURS: i64 = 24;

#[derive(Debug)]
pub struct AttentionDensityTracker {
    /// memory_cid → deque of activation samples
    samples: Arc<DashMap<String, Vec<ActivationSample>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActivationSample {
    pub activated_layers: u32,
    pub total_layers: u32,
    pub sampled_at: DateTime<Utc>,
}

impl ActivationSample {
    pub fn layer_ratio(&self) -> f64 {
        if self.total_layers == 0 {
            0.0
        } else {
            (self.activated_layers as f64 / self.total_layers as f64).min(1.0)
        }
    }
}

impl AttentionDensityTracker {
    pub fn new() -> Self {
        Self {
            samples: Arc::new(DashMap::new()),
        }
    }

    /// Record a KV-state activation event for a memory
    pub fn record_activation(&self, memory_cid: &str, activated_layers: u32, total_layers: u32) {
        let sample = ActivationSample {
            activated_layers,
            total_layers,
            sampled_at: Utc::now(),
        };

        self.samples
            .entry(memory_cid.to_string())
            .or_insert_with(Vec::new)
            .push(sample);

        self.prune(memory_cid);
    }

    /// Density in [0.0, 1.0]: average layer activation ratio over the 24h window
    pub fn density(&self, memory_cid: &str) -> f64 {
        if let Some(samples) = self.samples.get(memory_cid) {
            let cutoff = Utc::now() - Duration::hours(DENSITY_WINDOW_HOURS);
            let windowed: Vec<&ActivationSample> = samples
                .iter()
                .filter(|s| s.sampled_at >= cutoff)
                .collect();

            if windowed.is_empty() {
                return 0.0;
            }

            let total_ratio: f64 = windowed.iter().map(|s| s.layer_ratio()).sum();
            total_ratio / windowed.len() as f64
        } else {
            0.0
        }
    }

    /// Peak density: max single-sample activation ratio (spike indicator)
    pub fn peak_density(&self, memory_cid: &str) -> f64 {
        if let Some(samples) = self.samples.get(memory_cid) {
            let cutoff = Utc::now() - Duration::hours(DENSITY_WINDOW_HOURS);
            samples
                .iter()
                .filter(|s| s.sampled_at >= cutoff)
                .map(|s| s.layer_ratio())
                .fold(0.0_f64, f64::max)
        } else {
            0.0
        }
    }

    /// Total activation events in window
    pub fn activation_count(&self, memory_cid: &str) -> usize {
        if let Some(samples) = self.samples.get(memory_cid) {
            let cutoff = Utc::now() - Duration::hours(DENSITY_WINDOW_HOURS);
            samples.iter().filter(|s| s.sampled_at >= cutoff).count()
        } else {
            0
        }
    }

    fn prune(&self, memory_cid: &str) {
        if let Some(mut samples) = self.samples.get_mut(memory_cid) {
            let cutoff = Utc::now() - Duration::hours(DENSITY_WINDOW_HOURS);
            samples.retain(|s| s.sampled_at >= cutoff);
        }
    }
}

impl Default for AttentionDensityTracker {
    fn default() -> Self {
        Self::new()
    }
}
