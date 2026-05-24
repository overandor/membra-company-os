use membra_l3_runtime::{ConsensusEngine, Node, TransactionPool};
use tracing::{info, warn};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    
    info!("╔══════════════════════════════════════════════════════════════╗");
    info!("║  MEMBRA L3 RUNTIME — Proof-of-Proof Consensus Engine         ║");
    info!("║  Rust Core | Solana + Sui + Berachain | LLM = TX           ║");
    info!("╚══════════════════════════════════════════════════════════════╝");
    
    let mut node = Node::new("m5-pro-001").await?;
    node.start().await?;
    
    info!("Node {} running. Press Ctrl+C to stop.", node.id());
    
    tokio::signal::ctrl_c().await?;
    warn!("Shutting down Membra L3 runtime...");
    node.stop().await?;
    
    Ok(())
}
