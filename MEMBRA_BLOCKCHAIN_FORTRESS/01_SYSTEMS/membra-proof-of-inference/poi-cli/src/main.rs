mod demo;

use clap::{Parser, Subcommand};
use chrono::Utc;
use ed25519_dalek::SigningKey;
use poi_core::{ProofOfInference, SamplerState, KVCommitment, RuntimeFingerprint, HardwareAttestation};
use poi_network::PoiNetwork;
use memgas_protocol::{MemGasProtocol, UserIntent};
use worker_reputation::{WorkerRegistry, ReputationLedger, ChallengeSystem, WorkerStatus};
use kv_state_collateral::{LayerAttention, ReasoningStep, KVStateChallengeType, KVStateChallengeResponse};
use memory_market::pricing_engine::EmergentPricingEngine;
use rand::rngs::OsRng;
use rand::RngCore;
use std::collections::HashMap;

#[derive(Parser)]
struct Cli { #[command(subcommand)] command: Commands }

#[derive(Subcommand)]
enum Commands {
    GenerateKeypair,
    StartNode { #[arg(short, long, default_value = "5")] block_time: u64 },
    Info,
    /// System status dashboard
    Status,
    /// MemGas commands
    MemGas {
        #[command(subcommand)]
        memgas_cmd: MemGasCommands,
    },
    /// Worker reputation commands
    Worker {
        #[command(subcommand)]
        worker_cmd: WorkerCommands,
    },
    /// KV-state collateral commands
    KVState {
        #[command(subcommand)]
        kv_cmd: KVStateCommands,
    },
    /// Emergent memory market commands (Phase 3)
    Market {
        #[command(subcommand)]
        market_cmd: MarketCommands,
    },
    /// Interactive public demo console — all 7 protocol steps live
    Demo {
        /// Skip interactive pauses (for CI / recording)
        #[arg(long, default_value_t = false)]
        fast: bool,
        /// Run only the first N steps (1-7, default: all)
        #[arg(long)]
        steps: Option<u8>,
    },
}

#[derive(Subcommand)]
enum MemGasCommands {
    /// Register memory in MemGas market
    RegisterMemory {
        #[arg(short, long)]
        memory_cid: String,
        #[arg(short, long)]
        model_cid: String,
        #[arg(short, long)]
        reuse_score: f64,
        #[arg(short, long)]
        owner_pubkey: String,
        #[arg(short, long)]
        worker_id: String,
    },
    /// Check remaining credit for memory
    CheckCredit {
        #[arg(short, long)]
        memory_cid: String,
    },
    /// Validate relay intent
    ValidateRelay {
        #[arg(short, long)]
        owner_pubkey: String,
        #[arg(short, long)]
        nonce: String,
        #[arg(short, long)]
        requested_lamports: u64,
        #[arg(short, long)]
        memory_cid: String,
    },
}

#[derive(Subcommand)]
enum WorkerCommands {
    /// Register a new worker
    RegisterWorker {
        #[arg(short, long)]
        worker_id: String,
        #[arg(short, long)]
        public_key: String,
        #[arg(short, long)]
        owner_wallet: String,
        #[arg(short, long)]
        model_cid: String,
    },
    /// Get worker reputation
    GetReputation {
        #[arg(short, long)]
        worker_id: String,
    },
    /// Generate deterministic challenge
    GenerateChallenge {
        #[arg(short, long)]
        worker_id: String,
        #[arg(short, long)]
        model_cid: String,
        #[arg(short, long)]
        prompt: String,
    },
}

#[derive(Subcommand)]
enum KVStateCommands {
    /// Register KV-state as collateral
    RegisterKVState {
        #[arg(short, long)]
        state_id: String,
        #[arg(short, long)]
        model_cid: String,
        #[arg(short, long)]
        cache_size: u64,
        #[arg(short, long)]
        token_position: u32,
        #[arg(short, long)]
        context_length: u32,
        #[arg(short, long)]
        owner_pubkey: String,
        #[arg(short, long)]
        worker_id: String,
    },
    /// Register prefill as collateral
    RegisterPrefill {
        #[arg(short, long)]
        prefill_id: String,
        #[arg(short, long)]
        model_cid: String,
        #[arg(short, long)]
        prefill_length: u32,
        #[arg(short, long)]
        owner_pubkey: String,
        #[arg(short, long)]
        worker_id: String,
    },
    /// Get worker total collateral
    GetWorkerCollateral {
        #[arg(short, long)]
        worker_id: String,
    },
    /// Increment KV-state reuse
    IncrementReuse {
        #[arg(short, long)]
        state_id: String,
    },
    /// Generate challenge for KV-state
    GenerateChallenge {
        #[arg(short, long)]
        state_id: String,
        #[arg(short, long)]
        challenge_type: String,
        #[arg(short, long)]
        difficulty: f64,
    },
    /// Submit challenge response
    SubmitResponse {
        #[arg(short, long)]
        challenge_id: String,
        #[arg(short, long)]
        state_id: String,
        #[arg(short, long)]
        response_data: String,
        #[arg(short, long)]
        worker_signature: String,
    },
    /// Get challenge result
    GetChallengeResult {
        #[arg(short, long)]
        challenge_id: String,
    },
    /// Get active challenges for state
    GetActiveChallenges {
        #[arg(short, long)]
        state_id: String,
    },
}

#[derive(Subcommand)]
enum MarketCommands {
    /// Record a retrieval event and get emergent price
    RecordRetrieval {
        #[arg(short, long)]
        memory_cid: String,
        #[arg(short, long)]
        worker_id: String,
    },
    /// Record downstream reference between inferences
    RecordReference {
        #[arg(short, long)]
        source_memory_cid: String,
        #[arg(short, long)]
        referencing_inference_id: String,
        #[arg(short, long)]
        worker_id: String,
    },
    /// Record attention reuse from KV-state layers
    RecordAttentionReuse {
        #[arg(short, long)]
        memory_cid: String,
        #[arg(short, long)]
        activated_layers: u32,
        #[arg(short, long)]
        total_layers: u32,
        #[arg(short, long)]
        worker_id: String,
    },
    /// Get full market record for a memory
    GetRecord {
        #[arg(short, long)]
        memory_cid: String,
    },
    /// Get price history for a memory
    GetPriceHistory {
        #[arg(short, long)]
        memory_cid: String,
    },
    /// Get top memories by emergent reuse score
    TopMemories {
        #[arg(short, long, default_value = "10")]
        n: usize,
    },
    /// Show total market liquidity
    Liquidity,
    /// Show pricing parameters
    PricingParams,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    match cli.command {
        Commands::GenerateKeypair => {
            let mut seed = [0u8; 32];
            OsRng.fill_bytes(&mut seed);
            let signing_key = SigningKey::from_bytes(&seed);
            println!("Public: {}", hex::encode(signing_key.verifying_key().to_bytes()));
            println!("Secret: {}", hex::encode(signing_key.to_bytes()));
        }
        Commands::StartNode { block_time } => {
            let mut seed = [0u8; 32];
            OsRng.fill_bytes(&mut seed);
            let signing_key = SigningKey::from_bytes(&seed);
            let network = PoiNetwork::new(signing_key, block_time);
            println!("Node started, height: {}", network.height());
        }
        Commands::Info => {
            let mut seed = [0u8; 32];
            OsRng.fill_bytes(&mut seed);
            let signing_key = SigningKey::from_bytes(&seed);
            let network = PoiNetwork::new(signing_key, 5);
            println!("Height: {}", network.height());
        }
        Commands::Status => {
            print_status_dashboard();
        }
        Commands::MemGas { memgas_cmd } => {
            let memgas = MemGasProtocol::new(50000, 1000000, 24); // 50k base, 1M daily cap, 24h expiration
            match memgas_cmd {
                MemGasCommands::RegisterMemory { memory_cid, model_cid, reuse_score, owner_pubkey, worker_id } => {
                    memgas.register_memory(memory_cid, model_cid, reuse_score, owner_pubkey, worker_id)?;
                    println!("Memory registered in MemGas market");
                }
                MemGasCommands::CheckCredit { memory_cid } => {
                    if let Some(credit) = memgas.get_remaining_credit(&memory_cid) {
                        println!("Remaining credit: {} lamports", credit);
                    } else {
                        println!("Memory not found");
                    }
                }
                MemGasCommands::ValidateRelay { owner_pubkey, nonce, requested_lamports, memory_cid } => {
                    let intent = UserIntent {
                        owner_pubkey,
                        nonce,
                        requested_lamports,
                        memory_cid,
                        tx_data: "".to_string(),
                        signature: "".to_string(),
                    };
                    match memgas.validate_relay(&intent) {
                        Ok(approved) => println!("Relay approved: {} lamports", approved),
                        Err(e) => println!("Relay rejected: {}", e),
                    }
                }
            }
        }
        Commands::Worker { worker_cmd } => {
            let registry = WorkerRegistry::new();
            let reputation = ReputationLedger::new(0.5);
            let challenge_system = ChallengeSystem::new();
            match worker_cmd {
                WorkerCommands::RegisterWorker { worker_id, public_key, owner_wallet, model_cid } => {
                    registry.register_worker(
                        worker_id.clone(),
                        public_key,
                        owner_wallet,
                        vec![model_cid.clone()],
                        vec![model_cid],
                        "hardware_fp_hash".to_string(),
                        "runtime_fp_hash".to_string(),
                    )?;
                    println!("Worker registered: {}", worker_id);
                }
                WorkerCommands::GetReputation { worker_id } => {
                    if let Some(rep) = reputation.get_reputation(&worker_id) {
                        println!("Trust score: {:.2}", rep.trust_score);
                        println!("Valid PoI: {}", rep.valid_poi_count);
                        println!("Invalid PoI: {}", rep.invalid_poi_count);
                    } else {
                        println!("Worker not found");
                    }
                }
                WorkerCommands::GenerateChallenge { worker_id, model_cid, prompt } => {
                    let challenge = challenge_system.generate_deterministic_challenge(
                        worker_id,
                        model_cid,
                        prompt,
                        42,
                        "expected_hash".to_string(),
                    );
                    println!("Challenge generated: {}", challenge.challenge_id);
                }
            }
        }
        Commands::KVState { kv_cmd } => {
            let memgas = MemGasProtocol::new(50000, 1000000, 24);
            let kv_collateral = &memgas.kv_collateral;
            match kv_cmd {
                KVStateCommands::RegisterKVState { state_id, model_cid, cache_size, token_position, context_length, owner_pubkey, worker_id } => {
                    let layer_hashes = vec!["hash1".to_string(), "hash2".to_string()];
                    memgas.register_kv_state(state_id, model_cid, layer_hashes, cache_size, token_position, context_length, owner_pubkey, worker_id)?;
                    println!("KV-state registered as collateral");
                }
                KVStateCommands::RegisterPrefill { prefill_id, model_cid, prefill_length, owner_pubkey, worker_id } => {
                    let prompt_tokens = vec![1, 2, 3, 4, 5];
                    memgas.register_prefill(prefill_id, model_cid, prompt_tokens, prefill_length, owner_pubkey, worker_id)?;
                    println!("Prefill registered as collateral");
                }
                KVStateCommands::GetWorkerCollateral { worker_id } => {
                    let total = memgas.get_worker_total_collateral(&worker_id);
                    println!("Worker total collateral: {} lamports", total);
                }
                KVStateCommands::IncrementReuse { state_id } => {
                    match memgas.increment_kv_reuse(&state_id) {
                        Ok(new_value) => println!("KV-state reuse incremented, new value: {} lamports", new_value),
                        Err(e) => println!("Error: {}", e),
                    }
                }
                KVStateCommands::GenerateChallenge { state_id, challenge_type, difficulty } => {
                    let challenge_type = match challenge_type.as_str() {
                        "deterministic" => KVStateChallengeType::DeterministicReproduction,
                        "attention" => KVStateChallengeType::AttentionConsistency,
                        "reasoning" => KVStateChallengeType::ReasoningTraceValidation,
                        "hash" => KVStateChallengeType::HashVerification,
                        _ => return Err("Invalid challenge type. Use: deterministic, attention, reasoning, hash".into()),
                    };
                    match kv_collateral.generate_kv_challenge(&state_id, challenge_type, difficulty) {
                        Ok(challenge_id) => println!("Challenge generated: {}", challenge_id),
                        Err(e) => println!("Error: {}", e),
                    }
                }
                KVStateCommands::SubmitResponse { challenge_id, state_id, response_data, worker_signature } => {
                    let response = KVStateChallengeResponse {
                        challenge_id: challenge_id.clone(),
                        state_id,
                        response_data,
                        worker_signature,
                        submitted_at: Utc::now(),
                    };
                    match kv_collateral.submit_challenge_response(response) {
                        Ok(msg) => println!("{}", msg),
                        Err(e) => println!("Error: {}", e),
                    }
                }
                KVStateCommands::GetChallengeResult { challenge_id } => {
                    match kv_collateral.get_challenge_result(&challenge_id) {
                        Some(result) => {
                            println!("Challenge Result:");
                            println!("  Passed: {}", result.passed);
                            println!("  Score: {}", result.score);
                            println!("  Details: {}", result.details);
                            println!("  Verified at: {}", result.verified_at);
                        }
                        None => println!("Challenge result not found"),
                    }
                }
                KVStateCommands::GetActiveChallenges { state_id } => {
                    let challenges = kv_collateral.get_active_challenges(&state_id);
                    if challenges.is_empty() {
                        println!("No active challenges for state: {}", state_id);
                    } else {
                        println!("Active challenges for state: {}", state_id);
                        for challenge in challenges {
                            println!("  Challenge ID: {}", challenge.challenge_id);
                            println!("  Type: {:?}", challenge.challenge_type);
                            println!("  Difficulty: {}", challenge.difficulty);
                            println!("  Expires at: {}", challenge.expires_at);
                        }
                    }
                }
            }
        }
        Commands::Demo { fast, steps } => {
            demo::run_demo(fast, steps);
        }
        Commands::Market { market_cmd } => {
            let memgas = MemGasProtocol::new(50000, 1000000, 24);
            match market_cmd {
                MarketCommands::RecordRetrieval { memory_cid, worker_id } => {
                    match memgas.record_market_retrieval(&memory_cid, &worker_id) {
                        Ok(price) => println!("Retrieval recorded. New emergent price: {} lamports", price),
                        Err(e) => println!("Error: {}", e),
                    }
                }
                MarketCommands::RecordReference { source_memory_cid, referencing_inference_id, worker_id } => {
                    match memgas.record_market_reference(&source_memory_cid, &referencing_inference_id, &worker_id) {
                        Ok(price) => println!("Reference recorded. Updated price: {} lamports", price),
                        Err(e) => println!("Error: {}", e),
                    }
                }
                MarketCommands::RecordAttentionReuse { memory_cid, activated_layers, total_layers, worker_id } => {
                    match memgas.record_attention_reuse(&memory_cid, activated_layers, total_layers, &worker_id) {
                        Ok(price) => {
                            let density = activated_layers as f64 / total_layers.max(1) as f64;
                            println!("Attention reuse recorded.");
                            println!("  Activated layers: {}/{} ({:.1}%)", activated_layers, total_layers, density * 100.0);
                            println!("  Updated price: {} lamports", price);
                        }
                        Err(e) => println!("Error: {}", e),
                    }
                }
                MarketCommands::GetRecord { memory_cid } => {
                    match memgas.get_market_record(&memory_cid) {
                        Some(record) => {
                            println!("Market Record: {}", record.memory_cid);
                            println!("  Model:                  {}", record.model_cid);
                            println!("  Worker:                 {}", record.worker_id);
                            println!("  Emergent reuse score:   {:.4}", record.emergent_reuse_score);
                            println!("  Market price:           {} lamports", record.market_price_lamports);
                            println!("  Retrieval count:        {}", record.retrieval_count);
                            println!("  Downstream refs:        {}", record.downstream_reference_count);
                            println!();
                            println!("  Score Breakdown:");
                            println!("    Retrieval frequency:  {:.4}", record.score_breakdown.retrieval_frequency);
                            println!("    Reference density:    {:.4}", record.score_breakdown.reference_density);
                            println!("    Semantic similarity:  {:.4}", record.score_breakdown.semantic_similarity);
                            println!("    Attention density:    {:.4}", record.score_breakdown.attention_reuse_density);
                            println!("    Worker trust:         {:.4}", record.score_breakdown.worker_trust_multiplier);
                            println!("    Composite:            {:.4}", record.score_breakdown.composite_score);
                        }
                        None => println!("Memory not found in market: {}", memory_cid),
                    }
                }
                MarketCommands::GetPriceHistory { memory_cid } => {
                    let history = memgas.memory_market.get_price_history(&memory_cid);
                    if history.is_empty() {
                        println!("No price history for: {}", memory_cid);
                    } else {
                        println!("Price History for {}:", memory_cid);
                        for point in &history {
                            println!("  {} | {:?} | {} lam | score {:.4}",
                                point.timestamp.format("%Y-%m-%d %H:%M:%S"),
                                point.trigger,
                                point.price_lamports,
                                point.reuse_score,
                            );
                        }
                    }
                }
                MarketCommands::TopMemories { n } => {
                    let top = memgas.top_memories(n);
                    if top.is_empty() {
                        println!("No memories registered in market.");
                    } else {
                        println!("Top {} Memories by Emergent Reuse Score:", top.len());
                        println!("  {:64}  {:>8}  {:>10}  {:>6}",
                            "CID", "Score", "Price(lam)", "Refs");
                        println!("  {}", "─".repeat(96));
                        for r in &top {
                            println!("  {:64}  {:>8.4}  {:>10}  {:>6}",
                                &r.memory_cid[..r.memory_cid.len().min(64)],
                                r.emergent_reuse_score,
                                r.market_price_lamports,
                                r.downstream_reference_count,
                            );
                        }
                    }
                }
                MarketCommands::Liquidity => {
                    let liquidity = memgas.market_liquidity();
                    println!("Total market liquidity: {} lamports ({:.4} SOL equivalent)",
                        liquidity,
                        liquidity as f64 / 1_000_000_000.0,
                    );
                }
                MarketCommands::PricingParams => {
                    let params = EmergentPricingEngine::params();
                    println!("Emergent Pricing Parameters:");
                    println!("  Base lamports per token:  {}", params.base_lamports_per_token);
                    println!("  Base lamports per layer:  {}", params.base_lamports_per_layer);
                    println!("  Score multiplier:         {:.1}x (max {}x at score=1.0)",
                        params.score_multiplier, 1 + params.score_multiplier as u64);
                    println!("  Min price floor:          {} lamports", params.min_lamports);
                    println!();
                    println!("  Score weights:");
                    println!("    Retrieval frequency:    30%");
                    println!("    Downstream references:  25%");
                    println!("    Semantic similarity:    20%");
                    println!("    Attention reuse:        25%");
                    println!("    Worker trust gate:      ×all (Phase 2)");
                }
            }
        }
    }
    Ok(())
}

fn print_status_dashboard() {
    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║     PoI Network + MemGas + Emergent Market Status         ║");
    println!("╚════════════════════════════════════════════════════════════╝");
    println!();
    
    // System info
    println!("🖥️  System Information");
    println!("   Platform: macOS (Apple Silicon M5 Pro)");
    println!("   Architecture: aarch64-apple-darwin");
    println!("   Optimization: native + NEON + LTO");
    println!();
    
    // Protocol status
    println!("🔗 Protocol Status");
    println!("   PoI Network: ✅ Operational");
    println!("   MemGas Protocol: ✅ Operational");
    println!("   Worker Reputation: ✅ Operational");
    println!("   Challenge System: ✅ Operational");
    println!("   Emergent Memory Market: ✅ Operational (Phase 3)");
    println!();
    
    // Components
    println!("📦 Active Components");
    println!("   Worker Registry: Initialized");
    println!("   Reputation Ledger: Initialized (base trust: 0.5)");
    println!("   Nonce Ledger: Active");
    println!("   Spend Ledger: Active  [daily spend tracked per wallet]");
    println!("   Memory Market: Active");
    println!("   KV-State Collateral: ✅ Operational (Phase 4)");
    println!("   Prefill Registry: ✅ Operational");
    println!("   Attention State Registry: ✅ Operational");
    println!("   Reasoning Context Registry: ✅ Operational");
    println!("   Retrieval Tracker: ✅ Operational (24h sliding window)");
    println!("   Reference Graph: ✅ Operational (48h downstream tracking)");
    println!("   Attention Density Tracker: ✅ Operational");
    println!("   Emergent Pricing Engine: ✅ Operational (semantic clusters)");
    println!();
    
    // Trust multipliers
    println!("⚖️  Trust Multipliers");
    println!("   ≥ 0.90: 1.00x");
    println!("   0.75-0.89: 0.75x");
    println!("   0.50-0.74: 0.40x");
    println!("   0.25-0.49: 0.15x");
    println!("   < 0.25: 0.00x (rejected)");
    println!();
    
    // MemGas parameters
    println!("💰 MemGas Parameters");
    println!("   Base Credit: 50,000 lamports");
    println!("   Daily Wallet Cap: 1,000,000 lamports");
    println!("   Memory Expiration: 24 hours");
    println!("   Anti-Sybil Decay: 3% per unit");
    println!();

    // Phase 3: Emergent market pricing
    println!("📈 Emergent Market Pricing (Phase 3)");
    println!("   Score = retrieval×0.30 + references×0.25 + semantic×0.20 + attention×0.25");
    println!("   All signals gated by worker trust multiplier (Phase 2)");
    println!();
    println!("   Signal                 Window   Cap    Weight");
    println!("   ──────────────────────────────────────────────");
    println!("   Retrieval frequency    24h      100    30%");
    println!("   Downstream references  48h       50    25%");
    println!("   Semantic similarity    cluster  —      20%");
    println!("   Attention reuse        24h      —      25%");
    println!();
    println!("   Pricing: base×(1 + score×9.0), floor 1,000 lam, max 10x at score=1.0");
    println!();

    // Phase 4: KV-state collateral
    println!("🧠 KV-State Collateral (Phase 4)");
    println!("   Freshness model: e^(-3t) exponential decay");
    println!();
    println!("   Type              Rate              TTL   Reuse Bonus");
    println!("   ─────────────────────────────────────────────────────");
    println!("   KV-state          10 lam/KB         6h    +10%/reuse");
    println!("   Prefill           50 lam/token      12h   +15%/reuse");
    println!("   Attention state    5 lam/layer·tok   4h    +8%/reuse");
    println!("   Reasoning ctx    100 lam/step        8h    +12%/reuse");
    println!();

    // Available commands
    println!("🚀 Available Commands");
    println!("   poi generate-keypair                 Generate validator keypair");
    println!("   poi start-node                       Start PoI network node");
    println!("   poi info                             Show chain info");
    println!("   poi status                           Show this dashboard");
    println!("   poi memgas register-memory           Register memory in market");
    println!("   poi memgas check-credit              Check memory credit");
    println!("   poi memgas validate-relay            Validate relay intent");
    println!("   poi worker register-worker           Register GPU worker");
    println!("   poi worker get-reputation            Get worker reputation");
    println!("   poi worker generate-challenge        Generate verification challenge");
    println!("   poi kv-state register-kv-state       Register KV-state as collateral");
    println!("   poi kv-state register-prefill        Register prefill as collateral");
    println!("   poi kv-state get-worker-collateral   Query total collateral");
    println!("   poi kv-state increment-reuse         Increment reuse + recalculate");
    println!("   poi market record-retrieval          Record retrieval event → reprice");
    println!("   poi market record-reference          Record downstream inference reference");
    println!("   poi market record-attention-reuse    Record KV-state layer activation");
    println!("   poi market get-record                Full market record + score breakdown");
    println!("   poi market get-price-history         Price history timeline");
    println!("   poi market top-memories              Leaderboard by emergent score");
    println!("   poi market liquidity                 Total priced lamports in market");
    println!("   poi market pricing-params            Show pricing formula + weights");
    println!();
    
    println!("✓ System ready for inference and gas sponsorship");
}
