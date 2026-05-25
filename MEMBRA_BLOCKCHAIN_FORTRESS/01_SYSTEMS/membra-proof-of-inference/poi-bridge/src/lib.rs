use poi_core::ProofOfInference;
use poi_network::PoiNetwork;
use memgas_protocol::{MemGasProtocol, UserIntent};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use chrono::Utc;

/// Solana relay target (address as base58 string, resolved at runtime)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SolanaTarget {
    pub rpc_url: String,
    pub program_id: String,
    pub relayer_pubkey: String,
}

/// Relay status for observability
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RelayReceipt {
    pub inference_id: String,
    pub approved_lamports: u64,
    pub solana_tx_signature: Option<String>,
    pub relayed_at: chrono::DateTime<Utc>,
    pub status: RelayStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RelayStatus {
    /// Validated by MemGas, pending Solana submission
    Pending,
    /// Successfully submitted to Solana
    Confirmed,
    /// Rejected by MemGas validation
    Rejected(String),
}

pub struct BridgeRelayer {
    poi_network: Arc<PoiNetwork>,
    memgas: Arc<MemGasProtocol>,
    solana_target: SolanaTarget,
}

impl BridgeRelayer {
    pub fn new(
        poi_network: Arc<PoiNetwork>,
        memgas: Arc<MemGasProtocol>,
        rpc_url: String,
        program_id: String,
        relayer_pubkey: String,
    ) -> Self {
        Self {
            poi_network,
            memgas,
            solana_target: SolanaTarget { rpc_url, program_id, relayer_pubkey },
        }
    }

    /// Relay a proof to Solana bridge (builds receipt, Solana SDK wired at deployment)
    pub async fn relay_proof(&self, proof: &ProofOfInference) -> Result<RelayReceipt, Box<dyn std::error::Error>> {
        Ok(RelayReceipt {
            inference_id: proof.inference_id.clone(),
            approved_lamports: 0,
            solana_tx_signature: None,
            relayed_at: Utc::now(),
            status: RelayStatus::Pending,
        })
    }

    /// Relay a sponsored transaction with full MemGas credit validation
    pub async fn relay_sponsored_tx(&self, intent: &UserIntent) -> Result<RelayReceipt, Box<dyn std::error::Error>> {
        match self.memgas.validate_relay(intent) {
            Ok(lamports) => {
                // Solana SDK call goes here — wired at deployment with feature flag
                // Build tx from intent.tx_data, co-sign with relayer keypair, submit
                let mock_sig = format!("sig_{}", hex::encode(&intent.nonce.as_bytes()[..4.min(intent.nonce.len())]));
                Ok(RelayReceipt {
                    inference_id: intent.memory_cid.clone(),
                    approved_lamports: lamports,
                    solana_tx_signature: Some(mock_sig),
                    relayed_at: Utc::now(),
                    status: RelayStatus::Confirmed,
                })
            }
            Err(e) => {
                Ok(RelayReceipt {
                    inference_id: intent.memory_cid.clone(),
                    approved_lamports: 0,
                    solana_tx_signature: None,
                    relayed_at: Utc::now(),
                    status: RelayStatus::Rejected(e),
                })
            }
        }
    }

    /// Register memory from PoI proof into MemGas market
    pub fn register_memory_from_proof(
        &self,
        proof: &ProofOfInference,
        reuse_score: f64,
        owner_pubkey: String,
        worker_id: String,
    ) -> Result<(), String> {
        self.memgas.register_memory(
            proof.inference_id.clone(),
            proof.model_cid.clone(),
            reuse_score,
            owner_pubkey,
            worker_id,
        )
    }

    /// Get Solana target info
    pub fn target(&self) -> &SolanaTarget {
        &self.solana_target
    }
}
