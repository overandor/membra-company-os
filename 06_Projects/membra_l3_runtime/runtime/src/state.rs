use serde::{Deserialize, Serialize};
use dashmap::DashMap;
use std::sync::atomic::{AtomicU64, Ordering};

/// Global state with lock-free reads for 1M+ TPS
#[derive(Debug)]
pub struct GlobalState {
    /// Account balances — lock-free concurrent map
    balances: DashMap<String, AtomicU64>,
    /// Total transactions processed
    total_tx: AtomicU64,
    /// Total tokens generated (inference micro-txs)
    total_tokens: AtomicU64,
    /// Current block height
    block_height: AtomicU64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountState {
    pub address: String,
    pub balance: u64,
    pub nonce: u64,
    pub total_prompts: u64,
    pub total_tokens_generated: u64,
    pub reputation: f64,
}

impl GlobalState {
    pub fn new() -> Self {
        Self {
            balances: DashMap::new(),
            total_tx: AtomicU64::new(0),
            total_tokens: AtomicU64::new(0),
            block_height: AtomicU64::new(0),
        }
    }
    
    /// Credit balance — lock-free for high throughput
    pub fn credit(&self, address: &str, amount: u64) {
        let entry = self.balances.entry(address.to_string()).or_insert_with(|| AtomicU64::new(0));
        entry.value().fetch_add(amount, Ordering::Relaxed);
    }
    
    /// Debit balance
    pub fn debit(&self, address: &str, amount: u64) -> bool {
        if let Some(entry) = self.balances.get(address) {
            let current = entry.value().load(Ordering::Relaxed);
            if current >= amount {
                entry.value().store(current - amount, Ordering::Relaxed);
                return true;
            }
        }
        false
    }
    
    pub fn get_balance(&self, address: &str) -> u64 {
        self.balances.get(address)
            .map(|e| e.value().load(Ordering::Relaxed))
            .unwrap_or(0)
    }
    
    pub fn increment_tx(&self) -> u64 {
        self.total_tx.fetch_add(1, Ordering::Relaxed)
    }
    
    pub fn increment_tokens(&self, count: u64) -> u64 {
        self.total_tokens.fetch_add(count, Ordering::Relaxed)
    }
    
    pub fn increment_block(&self) -> u64 {
        self.block_height.fetch_add(1, Ordering::Relaxed)
    }
    
    pub fn stats(&self) -> StateStats {
        StateStats {
            total_tx: self.total_tx.load(Ordering::Relaxed),
            total_tokens: self.total_tokens.load(Ordering::Relaxed),
            block_height: self.block_height.load(Ordering::Relaxed),
            account_count: self.balances.len() as u64,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct StateStats {
    pub total_tx: u64,
    pub total_tokens: u64,
    pub block_height: u64,
    pub account_count: u64,
}
