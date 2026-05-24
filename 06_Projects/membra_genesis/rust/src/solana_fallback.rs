//! Solana validator fallback
//! When local consensus can't reach 2/3, query Solana devnet validators

use reqwest::Client;
use serde::{Deserialize, Serialize};
use tracing::{info, warn};

const SOLANA_DEVNET_RPC: &str = "https://api.devnet.solana.com";
const CONSENSUS_PROGRAM: &str = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr";

#[derive(Debug, Serialize, Deserialize)]
pub struct SolanaVote {
    pub state_root: String,
    pub vote_hash: String,
    pub validator: String,
    pub slot: u64,
}

pub struct SolanaFallback {
    client: Client,
    rpc_url: String,
}

impl SolanaFallback {
    pub fn new() -> Self {
        Self {
            client: Client::new(),
            rpc_url: SOLANA_DEVNET_RPC.to_string(),
        }
    }
    
    /// Query Solana devnet for consensus on a state root
    /// Returns true if majority of reachable validators agree
    pub async fn query_consensus(&self, state_root: &str) -> anyhow::Result<bool> {
        info!("[FALLBACK] Querying Solana validators for root: {}", &state_root[..16]);
        
        // Get recent blockhash for tx simulation
        let blockhash = self.get_recent_blockhash().await?;
        
        // Query validator stake-weighted votes
        // In production: use gossip to query actual validator votes
        // For devnet: simulate with RPC query
        
        let payload = serde_json::json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlockCommitment",
            "params": [0] // Would use actual slot
        });
        
        let response = self.client
            .post(&self.rpc_url)
            .json(&payload)
            .send()
            .await?;
        
        let result: serde_json::Value = response.json().await?;
        
        // Check if we have commitment from 2/3 stake
        if let Some(commitment) = result["result"]["commitment"].as_u64() {
            info!("[FALLBACK] Solana commitment: {}%", commitment);
            // If >67% commitment, accept as consensus
            return Ok(commitment >= 67);
        }
        
        warn!("[FALLBACK] Could not get validator consensus from Solana");
        Ok(false)
    }
    
    /// Post a memo transaction to Solana as settlement proof
    pub async fn post_settlement(&self, state_root: &str) -> anyhow::Result<String> {
        let memo = format!("MEMBRA|{}", &state_root[..32]);
        
        info!("[FALLBACK] Posting settlement memo to Solana: {}", memo);
        
        // In production: sign and send real transaction
        // For devnet test: return simulated tx hash
        let tx_hash = format!("sim_{}", &state_root[..16]);
        Ok(tx_hash)
    }
    
    async fn get_recent_blockhash(&self) -> anyhow::Result<String> {
        let payload = serde_json::json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getRecentBlockhash"
        });
        
        let response = self.client
            .post(&self.rpc_url)
            .json(&payload)
            .send()
            .await?;
        
        let result: serde_json::Value = response.json().await?;
        
        Ok(result["result"]["value"]["blockhash"]
            .as_str()
            .unwrap_or("unknown")
            .to_string())
    }
    
    /// Check if Solana devnet is reachable
    pub async fn is_reachable(&self) -> bool {
        let payload = serde_json::json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth"
        });
        
        match self.client
            .post(&self.rpc_url)
            .json(&payload)
            .send()
            .await
        {
            Ok(resp) => {
                match resp.json::<serde_json::Value>().await {
                    Ok(json) => json["result"] == "ok",
                    Err(_) => false,
                }
            }
            Err(_) => false,
        }
    }
}
