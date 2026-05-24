use serde::{Deserialize, Serialize};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::mpsc;
use tokio_tungstenite::{accept_async, tungstenite::Message};
use tracing::{info, warn, error};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::consensus::{ConsensusEngine, InferenceProof};
use crate::transaction::TransactionPool;
use crate::state::GlobalState;

/// P2P Network node for inter-agent communication
pub struct P2PNetwork {
    node_id: String,
    peers: Arc<RwLock<HashMap<String, PeerConnection>>>,
    tx_pool: Arc<TransactionPool>,
    consensus: Arc<ConsensusEngine>,
    state: Arc<GlobalState>,
    command_tx: mpsc::Sender<NetworkCommand>,
}

#[derive(Debug, Clone)]
struct PeerConnection {
    id: String,
    address: String,
    last_seen: i64,
}

#[derive(Debug)]
enum NetworkCommand {
    Broadcast(Vec<u8>),
    Connect(String),
    Disconnect(String),
}

#[derive(Debug, Serialize, Deserialize)]
struct NetworkMessage {
    msg_type: String,
    sender: String,
    payload: serde_json::Value,
    timestamp: i64,
}

impl P2PNetwork {
    pub fn new(
        node_id: String,
        tx_pool: Arc<TransactionPool>,
        consensus: Arc<ConsensusEngine>,
        state: Arc<GlobalState>,
    ) -> (Self, mpsc::Receiver<NetworkCommand>) {
        let (command_tx, command_rx) = mpsc::channel(1000);
        
        let network = Self {
            node_id,
            peers: Arc::new(RwLock::new(HashMap::new())),
            tx_pool,
            consensus,
            state,
            command_tx,
        };
        
        (network, command_rx)
    }
    
    pub async fn start_listener(&self, port: u16) -> anyhow::Result<()> {
        let addr = format!("0.0.0.0:{}", port);
        let listener = TcpListener::bind(&addr).await?;
        info!("P2P listening on {}", addr);
        
        let peers = self.peers.clone();
        let node_id = self.node_id.clone();
        
        tokio::spawn(async move {
            loop {
                match listener.accept().await {
                    Ok((stream, addr)) => {
                        let peer_id = format!("peer-{}", addr);
                        let peers_clone = peers.clone();
                        let node_id_clone = node_id.clone();
                        
                        tokio::spawn(async move {
                            if let Err(e) = handle_connection(stream, peer_id, peers_clone, node_id_clone).await {
                                warn!("Connection error: {}", e);
                            }
                        });
                    }
                    Err(e) => {
                        error!("Accept error: {}", e);
                    }
                }
            }
        });
        
        Ok(())
    }
    
    pub async fn broadcast_proof(&self, batch_id: &str, proof: InferenceProof) {
        let msg = NetworkMessage {
            msg_type: "consensus_proof".to_string(),
            sender: self.node_id.clone(),
            payload: serde_json::json!({
                "batch_id": batch_id,
                "proof": proof,
            }),
            timestamp: chrono::Utc::now().timestamp_millis(),
        };
        
        self.broadcast(msg).await;
    }
    
    pub async fn broadcast_tx_batch(&self, batch: Vec<crate::transaction::Transaction>) {
        let msg = NetworkMessage {
            msg_type: "tx_batch".to_string(),
            sender: self.node_id.clone(),
            payload: serde_json::to_value(batch).unwrap_or_default(),
            timestamp: chrono::Utc::now().timestamp_millis(),
        };
        
        self.broadcast(msg).await;
    }
    
    async fn broadcast(&self, msg: NetworkMessage) {
        let data = match serde_json::to_vec(&msg) {
            Ok(d) => d,
            Err(e) => {
                error!("Serialize error: {}", e);
                return;
            }
        };
        
        // In production: send to all connected WebSocket peers
        // Simplified: just log for now
        info!("Broadcast {} to peers (payload: {} bytes)", msg.msg_type, data.len());
    }
    
    pub async fn peer_count(&self) -> usize {
        let peers = self.peers.read().await;
        peers.len()
    }
}

async fn handle_connection(
    stream: TcpStream,
    peer_id: String,
    peers: Arc<RwLock<HashMap<String, PeerConnection>>>,
    node_id: String,
) -> anyhow::Result<()> {
    let ws = accept_async(stream).await?;
    info!("Peer {} connected", peer_id);
    
    {
        let mut p = peers.write().await;
        p.insert(peer_id.clone(), PeerConnection {
            id: peer_id.clone(),
            address: "unknown".to_string(),
            last_seen: chrono::Utc::now().timestamp_millis(),
        });
    }
    
    // Connection handling loop would go here
    // Simplified for this implementation
    
    Ok(())
}

/// Main node orchestrator
pub struct Node {
    id: String,
    network: P2PNetwork,
    command_rx: mpsc::Receiver<NetworkCommand>,
    tx_pool: Arc<TransactionPool>,
    consensus: Arc<ConsensusEngine>,
    state: Arc<GlobalState>,
    running: bool,
}

impl Node {
    pub async fn new(id: &str) -> anyhow::Result<Self> {
        let tx_pool = Arc::new(TransactionPool::new());
        let consensus = Arc::new(ConsensusEngine::new());
        let state = Arc::new(GlobalState::new());
        
        let (network, command_rx) = P2PNetwork::new(
            id.to_string(),
            tx_pool.clone(),
            consensus.clone(),
            state.clone(),
        );
        
        Ok(Self {
            id: id.to_string(),
            network,
            command_rx,
            tx_pool,
            consensus,
            state,
            running: false,
        })
    }
    
    pub fn id(&self) -> &str {
        &self.id
    }
    
    pub async fn start(&mut self) -> anyhow::Result<()> {
        self.running = true;
        
        // Start P2P listener
        self.network.start_listener(42425).await?;
        
        // Start processing loops
        let tx_pool = self.tx_pool.clone();
        let consensus = self.consensus.clone();
        let state = self.state.clone();
        
        tokio::spawn(async move {
            processing_loop(tx_pool, consensus, state).await;
        });
        
        info!("Node {} started successfully", self.id);
        Ok(())
    }
    
    pub async fn stop(&mut self) -> anyhow::Result<()> {
        self.running = false;
        info!("Node {} stopped", self.id);
        Ok(())
    }
    
    pub async fn submit_prompt(&self, from: &str, prompt: &str, model: &str) {
        let tx = crate::transaction::Transaction::new_prompt(from, prompt, model);
        self.tx_pool.submit(tx.clone()).await;
        self.state.increment_tx();
        info!("Prompt tx submitted: {}", &tx.tx_hash[..16]);
    }
    
    pub fn get_stats(&self) -> serde_json::Value {
        let stats = self.state.stats();
        serde_json::json!({
            "node_id": self.id,
            "running": self.running,
            "peers": 0, // Would query network
            "state": stats,
        })
    }
}

async fn processing_loop(
    tx_pool: Arc<TransactionPool>,
    consensus: Arc<ConsensusEngine>,
    state: Arc<GlobalState>,
) {
    let mut interval = tokio::time::interval(tokio::time::Duration::from_millis(100));
    
    loop {
        interval.tick().await;
        
        // Drain batch and form consensus
        let batch_size = 1000;
        let txs = tx_pool.drain_batch(batch_size).await;
        
        if !txs.is_empty() {
            let batch = consensus.form_batch(txs).await;
            
            // In production: submit proofs from LLM agents
            // For now, auto-finalize with self-proof
            let proof = InferenceProof {
                agent_id: "runtime".to_string(),
                prompt_hash: batch.root_hash.clone(),
                response_hash: batch.root_hash.clone(),
                confidence: 1.0,
                timestamp: chrono::Utc::now().timestamp_millis(),
            };
            
            consensus.submit_proof(&batch.batch_id, proof).await;
            
            if consensus.check_consensus(&batch.batch_id).await {
                consensus.finalize_batch(batch).await;
                state.increment_block();
            }
        }
    }
}
