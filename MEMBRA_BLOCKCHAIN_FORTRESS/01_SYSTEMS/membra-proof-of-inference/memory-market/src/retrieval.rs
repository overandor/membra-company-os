use dashmap::DashMap;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::sync::Arc;
use chrono::{DateTime, Duration, Utc};

/// Sliding-window retrieval frequency tracker.
///
/// Uses a 24-hour sliding window of timestamped retrieval events per memory CID.
/// Normalized frequency = retrievals_in_window / WINDOW_MAX_RETRIEVALS (soft cap).
const WINDOW_HOURS: i64 = 24;
const WINDOW_MAX_RETRIEVALS: f64 = 100.0; // soft normalization cap

#[derive(Debug)]
pub struct RetrievalTracker {
    /// memory_cid → deque of (timestamp, retriever_worker_id)
    events: Arc<DashMap<String, RwLock<VecDeque<RetrievalEvent>>>>,
    /// Global retrieval count across all CIDs (for market-wide normalization)
    global_total: Arc<std::sync::atomic::AtomicU64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetrievalEvent {
    pub timestamp: DateTime<Utc>,
    pub worker_id: String,
}

impl RetrievalTracker {
    pub fn new() -> Self {
        Self {
            events: Arc::new(DashMap::new()),
            global_total: Arc::new(std::sync::atomic::AtomicU64::new(0)),
        }
    }

    /// Record a retrieval event for a memory CID
    pub fn record(&self, memory_cid: &str, worker_id: &str) {
        let event = RetrievalEvent {
            timestamp: Utc::now(),
            worker_id: worker_id.to_string(),
        };

        self.events
            .entry(memory_cid.to_string())
            .or_insert_with(|| RwLock::new(VecDeque::new()))
            .write()
            .push_back(event);

        self.global_total.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        self.prune_window(memory_cid);
    }

    /// Normalized frequency in [0.0, 1.0] based on 24h sliding window
    pub fn normalized_frequency(&self, memory_cid: &str) -> f64 {
        if let Some(entry) = self.events.get(memory_cid) {
            let mut queue = entry.write();
            Self::prune_queue(&mut queue);
            let count = queue.len() as f64;
            (count / WINDOW_MAX_RETRIEVALS).min(1.0)
        } else {
            0.0
        }
    }

    /// Raw retrieval count in the current window
    pub fn window_count(&self, memory_cid: &str) -> usize {
        if let Some(entry) = self.events.get(memory_cid) {
            let mut queue = entry.write();
            Self::prune_queue(&mut queue);
            queue.len()
        } else {
            0
        }
    }

    /// Recent retrievals per hour (velocity metric)
    pub fn retrieval_velocity(&self, memory_cid: &str) -> f64 {
        if let Some(entry) = self.events.get(memory_cid) {
            let mut queue = entry.write();
            Self::prune_queue(&mut queue);
            let one_hour_ago = Utc::now() - Duration::hours(1);
            let recent = queue.iter().filter(|e| e.timestamp >= one_hour_ago).count();
            recent as f64
        } else {
            0.0
        }
    }

    fn prune_window(&self, memory_cid: &str) {
        if let Some(entry) = self.events.get(memory_cid) {
            let mut queue = entry.write();
            Self::prune_queue(&mut queue);
        }
    }

    fn prune_queue(queue: &mut VecDeque<RetrievalEvent>) {
        let cutoff = Utc::now() - Duration::hours(WINDOW_HOURS);
        while let Some(front) = queue.front() {
            if front.timestamp < cutoff {
                queue.pop_front();
            } else {
                break;
            }
        }
    }
}

impl Default for RetrievalTracker {
    fn default() -> Self {
        Self::new()
    }
}
