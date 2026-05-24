//! Membra Genesis Node — Orchestrator
//! Bridges C++ hot path, Go P2P, and Solana fallback

use crate::ffi::{CTransaction, CInferenceProof, GenesisWrapper};
use crate::solana_fallback::SolanaFallback;
use tokio::sync::mpsc;
use tracing::{info, warn, error};
use std::time::{Duration, Instant};

pub struct GenesisOrchestrator {
    node_id: String,
    core: GenesisWrapper,
    solana: SolanaFallback,
    tx_rx: mpsc::Receiver<CTransaction>,
    proof_rx: mpsc::Receiver<CInferenceProof>,
    finalized: u64,
    last_fallback: Option<Instant>,
}

impl GenesisOrchestrator {
    pub fn new(node_id: &str) -> (Self, mpsc::Sender<CTransaction>, mpsc::Sender<CInferenceProof>) {
        let core = GenesisWrapper::new(node_id);
        let solana = SolanaFallback::new();
        let (tx_tx, tx_rx) = mpsc::channel(10000);
        let (proof_tx, proof_rx) = mpsc::channel(1000);
        
        let orchestrator = Self {
            node_id: node_id.to_string(),
            core,
            solana,
            tx_rx,
            proof_rx,
            finalized: 0,
            last_fallback: None,
        };
        
        (orchestrator, tx_tx, proof_tx)
    }
    
    pub async fn run(&mut self) {
        info!("╔══════════════════════════════════════════════════════════════╗");
        info!("║  MEMBRA GENESIS NODE — Multi-Language Orchestrator          ║");
        info!("║  C++ Core | Go P2P | Rust Runtime | Solana Fallback          ║");
        info!("╚══════════════════════════════════════════════════════════════╝");
        info!("Node ID: {}", self.node_id);
        
        // Check Solana fallback availability
        match self.solana.is_reachable().await {
            true => info!("[GENESIS] Solana fallback: AVAILABLE"),
            false => warn!("[GENESIS] Solana fallback: UNREACHABLE (operating standalone)"),
        }
        
        let mut batch_timer = tokio::time::interval(Duration::from_millis(100));
        let mut fallback_timer = tokio::time::interval(Duration::from_secs(30));
        
        loop {
            tokio::select! {
                _ = batch_timer.tick() => {
                    self.process_batch().await;
                }
                _ = fallback_timer.tick() => {
                    self.check_fallback().await;
                }
                Some(tx) = self.tx_rx.recv() => {
                    self.core.submit_tx(&tx);
                }
                Some(proof) = self.proof_rx.recv() => {
                    // Queue proof for next batch
                }
            }
        }
    }
    
    async fn process_batch(&mut self) {
        let pool_size = self.core.pool_size();
        if pool_size == 0 {
            return;
        }
        
        info!("[BATCH] Processing {} transactions", pool_size);
        
        // In production: drain actual txs from C++ pool
        // For now, simulate batch formation
        
        // Check consensus
        let batch_ptr = std::ptr::null_mut(); // Would be real batch pointer
        let consensus_reached = false; // Would check C++ consensus
        
        if consensus_reached {
            self.finalized += 1;
            info!("[BATCH] Finalized. Total: {}", self.finalized);
        } else if pool_size > 100 {
            // Not enough local consensus — try Solana fallback
            warn!("[BATCH] Local consensus failed, attempting Solana fallback...");
            self.attempt_fallback().await;
        }
    }
    
    async fn attempt_fallback(&mut self) {
        if self.last_fallback.map(|t| t.elapsed() < Duration::from_secs(60)).unwrap_or(false) {
            return; // Rate limit fallback attempts
        }
        
        let state_root = format!("batch-{}", self.finalized);
        
        match self.solana.query_consensus(&state_root).await {
            Ok(true) => {
                info!("[FALLBACK] Solana validators confirmed consensus!");
                self.finalized += 1;
                self.last_fallback = Some(Instant::now());
                
                // Post settlement proof
                match self.solana.post_settlement(&state_root).await {
                    Ok(tx_hash) => info!("[FALLBACK] Settlement tx: {}", tx_hash),
                    Err(e) => warn!("[FALLBACK] Settlement failed: {}", e),
                }
            }
            Ok(false) => {
                warn!("[FALLBACK] Solana validators did not confirm");
            }
            Err(e) => {
                error!("[FALLBACK] Solana query error: {}", e);
            }
        }
    }
    
    async fn check_fallback(&mut self) {
        let (total_tx, total_tokens, finalized) = self.core.stats();
        
        info!(
            "[STATS] tx={} tokens={} finalized={} pool={}",
            total_tx, total_tokens, finalized, self.core.pool_size()
        );
    }
    
    pub fn get_stats(&self) -> serde_json::Value {
        let (total_tx, total_tokens, finalized) = self.core.stats();
        serde_json::json!({
            "node_id": self.node_id,
            "total_tx": total_tx,
            "total_tokens": total_tokens,
            "finalized_batches": finalized,
            "pool_size": self.core.pool_size(),
            "solana_fallback_available": self.last_fallback.is_some(),
        })
    }
}
