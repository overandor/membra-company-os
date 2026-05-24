use membra_genesis_rust::genesis::GenesisOrchestrator;
use tracing::{info, error};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    
    let node_id = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "membra-genesis-001".to_string());
    
    info!("╔══════════════════════════════════════════════════════════════╗");
    info!("║  MEMBRA GENESIS — Multi-Language Validator Network          ║");
    info!("║  C++ Core | Go P2P | Rust Orchestrator | Solana Fallback    ║");
    info!("╚══════════════════════════════════════════════════════════════╝");
    
    let (mut orchestrator, tx_sender, proof_sender) = GenesisOrchestrator::new(&node_id);
    
    // Spawn the orchestrator
    let handle = tokio::spawn(async move {
        orchestrator.run().await;
    });
    
    info!("Genesis node {} starting. Press Ctrl+C to stop.", node_id);
    
    tokio::signal::ctrl_c().await?;
    error!("Shutdown signal received. Stopping genesis node...");
    
    handle.abort();
    
    Ok(())
}
