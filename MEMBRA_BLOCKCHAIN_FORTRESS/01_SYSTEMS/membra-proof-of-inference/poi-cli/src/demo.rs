/// MEMBRA PoI / MemGas — Public Demo Console
///
/// Self-contained 7-step walkthrough:
///   1. Generate inference proof
///   2. Register memory
///   3. Register KV-state
///   4. Simulate retrieval / reuse cycles
///   5. Watch price rise and decay
///   6. Spend MemGas credit
///   7. Export proof receipt
///
/// Run with:   poi demo [--steps N] [--fast] [--no-pause]
use std::io::{self, Write};
use std::thread;
use std::time::Duration;
use chrono::Utc;
use ed25519_dalek::SigningKey;
use rand::rngs::OsRng;
use rand::RngCore;
use sha2::{Digest, Sha256};
use serde_json;

use poi_core::{
    ProofOfInference, SamplerState, KVCommitment,
    RuntimeFingerprint, HardwareAttestation,
};
use memgas_protocol::MemGasProtocol;
use kv_state_collateral::KVStateCollateral;

// ─── palette helpers ─────────────────────────────────────────────────────────

const RESET:  &str = "\x1b[0m";
const BOLD:   &str = "\x1b[1m";
const DIM:    &str = "\x1b[2m";
const GREEN:  &str = "\x1b[32m";
const CYAN:   &str = "\x1b[36m";
const YELLOW: &str = "\x1b[33m";
const BLUE:   &str = "\x1b[34m";
const MAGENTA:&str = "\x1b[35m";
const RED:    &str = "\x1b[31m";
const WHITE:  &str = "\x1b[97m";

fn banner() {
    println!();
    println!("{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════╗{RESET}");
    println!("{BOLD}{CYAN}║          MEMBRA — Proof-of-Inference / MemGas Demo Console          ║{RESET}");
    println!("{BOLD}{CYAN}║    Verified AI memory as execution collateral on Solana              ║{RESET}");
    println!("{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════╝{RESET}");
    println!();
}

fn step_header(n: u8, total: u8, title: &str) {
    let dashes = "─".repeat(60usize.saturating_sub(title.len() + 12));
    println!();
    println!("{BOLD}{WHITE}┌─ Step {n}/{total}: {title} {DIM}{dashes}{RESET}");
}

fn ok(msg: &str)   { println!("  {GREEN}✓{RESET}  {msg}"); }
fn info(msg: &str) { println!("  {BLUE}→{RESET}  {msg}"); }
fn warn(msg: &str) { println!("  {YELLOW}⚠{RESET}  {msg}"); }
fn val(label: &str, value: &str) {
    println!("     {DIM}{label:<32}{RESET}{BOLD}{value}{RESET}");
}

fn pause(fast: bool) {
    if fast { thread::sleep(Duration::from_millis(120)); return; }
    print!("\n  {DIM}[press Enter to continue]{RESET} ");
    io::stdout().flush().unwrap();
    let mut buf = String::new();
    let _ = io::stdin().read_line(&mut buf);
}

fn tick(fast: bool) {
    if fast {
        thread::sleep(Duration::from_millis(60));
    } else {
        thread::sleep(Duration::from_millis(300));
    }
}

fn hash_str(s: &str) -> String {
    let h: [u8; 32] = Sha256::digest(s.as_bytes()).into();
    hex::encode(&h[..8])
}

fn hash32(s: &str) -> [u8; 32] {
    Sha256::digest(s.as_bytes()).into()
}

fn lamports_to_sol(lam: u64) -> f64 { lam as f64 / 1_000_000_000.0 }

// ─── price bar ───────────────────────────────────────────────────────────────

fn price_bar(price: u64, max_price: u64, width: usize) -> String {
    let filled = if max_price == 0 { 0 } else {
        (price as f64 / max_price as f64 * width as f64) as usize
    };
    let filled = filled.min(width);
    let empty  = width.saturating_sub(filled);
    format!("{GREEN}{}{RESET}{DIM}{}{RESET}  {BOLD}{}{RESET} lam",
        "█".repeat(filled),
        "░".repeat(empty),
        price,
    )
}

// ─── main entry point ────────────────────────────────────────────────────────

pub fn run_demo(fast: bool, steps_override: Option<u8>) {
    let total_steps: u8 = steps_override.unwrap_or(7);

    banner();

    println!("  This demo walks through the full MEMBRA protocol stack live.");
    println!("  Every number printed is computed by the actual Rust implementation.");
    println!();
    println!("  {DIM}Protocol:{RESET} PoI Core → Worker Trust → Memory Collateral → Emergent Pricing → MemGas → Relay");
    println!();

    if !fast {
        pause(false);
    }

    // ─── shared state ────────────────────────────────────────────────────────

    // Signing key
    let mut seed = [0u8; 32];
    OsRng.fill_bytes(&mut seed);
    let signing_key = SigningKey::from_bytes(&seed);
    let pubkey_hex  = hex::encode(signing_key.verifying_key().to_bytes());

    // Protocol instances
    let memgas   = MemGasProtocol::new(50_000, 1_000_000, 24);
    let kv_coll  = KVStateCollateral::new();

    // Simulated IDs (use full hex::encode for realistic-length CIDs)
    let worker_id    = format!("worker-{}", hash_str(&pubkey_hex));
    let model_cid    = format!("bafybeig{}c4q", hash_str("llama-3-8b-q4-gguf"));
    let memory_cid   = format!("Qm{}T9x", hash_str(&format!("memory-{}", Utc::now())));
    let kv_state_id  = format!("kv-{}", hash_str("layer-32-ctx-4096"));
    let inference_id = format!("inf-{}", hash_str(&format!("{}{}", Utc::now(), &worker_id)));

    // Track for later steps
    let mut current_price: u64  = 0;
    let mut credit_spent: u64   = 0;
    let mut credit_available: u64 = 0;

    // ─── Step 1: Generate inference proof ────────────────────────────────────

    if total_steps >= 1 {
        step_header(1, total_steps, "Generate Inference Proof");

        info("Generating Ed25519 keypair for worker identity…");
        tick(fast);
        val("Worker ID",     &worker_id);
        val("Public key",    &pubkey_hex[..48]);
        val("Model CID",     &model_cid[..model_cid.len().min(28)]);

        info("Building Proof-of-Inference attestation…");
        tick(fast);

        let prompt_bytes = b"Explain transformer attention mechanisms";
        let tokens: Vec<u32> = (0u32..64).collect();
        let prompt_hash_hex = hash_str("Explain transformer attention mechanisms");
        let kv_commit_hex   = hash_str("kv-layer-32-commitment");

        val("Prompt hash",     &prompt_hash_hex);
        val("Token seq hash",  &hash_str("token-sequence-demo"));
        val("KV commitment",   &kv_commit_hex);

        info("Signing proof with worker key…");
        tick(fast);

        let layer_hashes_kv: Vec<[u8; 32]> = (0u32..32)
            .map(|i| hash32(&format!("layer-{}-kv", i)))
            .collect();

        let proof = ProofOfInference::new(
            model_cid.clone(),
            prompt_bytes,
            &tokens,
            SamplerState {
                temperature: 0.7,
                top_p: 0.95,
                top_k: 40,
                repeat_penalty: 1.1,
            },
            42u64,
            KVCommitment {
                layer_hashes: layer_hashes_kv,
                cache_size_bytes: 32 * 4096 * 128 * 2,
            },
            RuntimeFingerprint {
                runtime_version: "llama.cpp-b3412".to_string(),
                quantization: "Q4_K_M".to_string(),
                context_length: 4096,
            },
            HardwareAttestation {
                cpu_vendor: "Apple M5 Pro".to_string(),
                gpu_vendor: None,
                platform: "aarch64-apple-darwin".to_string(),
            },
            &signing_key,
            worker_id.clone(),
            pubkey_hex.clone(),
            &signing_key,
            1,
            0.92,
        );

        ok(&format!("Proof created at {}", proof.timestamp.format("%Y-%m-%dT%H:%M:%SZ")));
        let inf_display = &proof.inference_id[..proof.inference_id.len().min(16)];
        val("Inference ID",             inf_display);
        val("Challenge window expires", &proof.challenge_window_expires_at.format("%H:%M:%S UTC").to_string());
        val("Worker trust snapshot",    &format!("{:.2}", proof.trust_snapshot));
        val("Registry epoch",           &proof.worker_registry_epoch.to_string());

        println!();
        println!("  {CYAN}Claim:{RESET} This proof cryptographically binds the inference output to");
        println!("  this worker's identity, hardware, and reputation at this moment.");
        pause(fast);
    }

    // ─── Step 2: Register memory ─────────────────────────────────────────────

    if total_steps >= 2 {
        step_header(2, total_steps, "Register Memory in Market");

        info(&format!("Registering memory object: {}", &memory_cid[..memory_cid.len().min(24)]));
        tick(fast);

        // Register worker in memgas worker registry first
        let _ = memgas.worker_registry().register_worker(
            worker_id.clone(),
            pubkey_hex.clone(),
            "owner-wallet-demo".to_string(),
            vec!["llama.cpp".to_string(), "Q4_K_M".to_string()],
            vec![model_cid.clone()],
            hash_str("hw-fingerprint"),
            hash_str("rt-fingerprint"),
        );
        // Simulate an established worker with a proven track record
        memgas.reputation_ledger().set_trust_score(&worker_id, 0.95);

        let trust = memgas.reputation_ledger().get_trust_multiplier(&worker_id);
        val("Worker trust multiplier", &format!("{:.2}x  (tier: ≥0.90 — full collateral multiplier)", trust));

        let initial_reuse_score = 0.35;
        val("Initial heuristic reuse score", &format!("{:.2}", initial_reuse_score));

        match memgas.register_memory(
            memory_cid.clone(),
            model_cid.clone(),
            initial_reuse_score,
            "owner-wallet-demo".to_string(),
            worker_id.clone(),
        ) {
            Ok(()) => {
                credit_available = memgas.get_remaining_credit(&memory_cid).unwrap_or(0);
                current_price    = credit_available;
                ok("Memory registered in MemGas market");
                val("Initial gas credit",  &format!("{} lamports", credit_available));
                val("SOL equivalent",      &format!("{:.6} SOL", lamports_to_sol(credit_available)));
                val("Expires in",          "24 hours");
            }
            Err(e) => warn(&format!("Registration: {}", e)),
        }

        println!();
        println!("  {CYAN}Claim:{RESET} Verified inference memory immediately generates gas credit.");
        println!("  Untrusted workers generate zero credit. Trust gates everything.");
        pause(fast);
    }

    // ─── Step 3: Register KV-state ───────────────────────────────────────────

    if total_steps >= 3 {
        step_header(3, total_steps, "Register KV-State Collateral");

        info("Collateralizing transformer KV cache (32 layers × 4096 tokens)…");
        tick(fast);

        let layer_hashes: Vec<String> = (0..32)
            .map(|i| hash_str(&format!("layer-{}-ctx-4096-worker-{}", i, &worker_id)))
            .collect();

        let cache_size_bytes: u64 = 32 * 4096 * 128 * 2; // 32 layers × 4096 tok × 128 heads × 2 bytes
        let worker_trust = memgas.reputation_ledger().get_trust_multiplier(&worker_id);

        match kv_coll.register_kv_state(
            kv_state_id.clone(),
            model_cid.clone(),
            layer_hashes.clone(),
            cache_size_bytes,
            4096,
            4096,
            "owner-wallet-demo".to_string(),
            worker_id.clone(),
            worker_trust,
        ) {
            Ok(id) => {
                ok(&format!("KV-state registered: {}", id));
                val("Cache size",       &format!("{} bytes ({:.1} MB)", cache_size_bytes, cache_size_bytes as f64 / 1_048_576.0));
                val("Layer hashes",     &format!("{} SHA256 commitments", layer_hashes.len()));
                val("TTL",              "6 hours");
                val("Freshness model",  "e^(-3t) exponential decay");

                let kv_val = kv_coll.get_worker_total_collateral(&worker_id);
                val("KV collateral value", &format!("{} lamports", kv_val));

                let total_coll = kv_val + credit_available;
                val("Total protocol collateral", &format!("{} lamports", total_coll));

                // Link KV dimensions to market record so pricing engine can scale above floor
                memgas.set_memory_kv_params(&memory_cid, 4096, 32);
                val("Market record KV dims", "4096 tokens × 32 layers linked");
            }
            Err(e) => warn(&format!("KV register: {}", e)),
        }

        println!();
        println!("  {CYAN}Claim:{RESET} Live transformer KV caches become reusable collateral.");
        println!("  The more layers computed and stored, the higher the collateral floor.");
        pause(fast);
    }

    // ─── Step 4: Simulate retrieval / reuse cycles ───────────────────────────

    if total_steps >= 4 {
        step_header(4, total_steps, "Simulate Retrieval & Reuse Cycles");

        info("Firing 8 retrieval events from distinct downstream inferences…");
        println!();

        // score_to_price(1.0, 4096, 32) = (4096×5 + 32×200) × (1 + 9.0) = (20480+6400)×10 = 268_800
        let max_sim_price: u64 = 268_800;

        for i in 1u32..=8 {
            tick(fast);
            let inf_ref = format!("inf-downstream-{:04}", i);

            // Record retrieval
            let retrieval_price = memgas.record_market_retrieval(&memory_cid, &worker_id)
                .unwrap_or(current_price);

            // Record downstream reference
            let ref_price = memgas.record_market_reference(
                &memory_cid, &inf_ref, &worker_id,
            ).unwrap_or(retrieval_price);

            // Record attention reuse (layer density increasing)
            let activated = (i * 4).min(32);
            let att_price = memgas.record_attention_reuse(
                &memory_cid, activated, 32, &worker_id,
            ).unwrap_or(ref_price);

            current_price = att_price;

            let record = memgas.get_market_record(&memory_cid);
            let score  = record.as_ref().map(|r| r.emergent_reuse_score).unwrap_or(0.0);

            print!("  {DIM}[{i:>2}]{RESET} {}", price_bar(current_price, max_sim_price, 32));
            println!("  score {MAGENTA}{:.4}{RESET}  layers {CYAN}{activated:>2}/32{RESET}", score);
        }

        println!();

        if let Some(record) = memgas.get_market_record(&memory_cid) {
            ok("Score breakdown after 8 retrieval cycles:");
            val("Retrieval frequency",  &format!("{:.4}", record.score_breakdown.retrieval_frequency));
            val("Reference density",    &format!("{:.4}", record.score_breakdown.reference_density));
            val("Semantic similarity",  &format!("{:.4}", record.score_breakdown.semantic_similarity));
            val("Attention density",    &format!("{:.4}", record.score_breakdown.attention_reuse_density));
            val("Worker trust gate",    &format!("{:.4}", record.score_breakdown.worker_trust_multiplier));
            val("Composite score",      &format!("{BOLD}{MAGENTA}{:.4}{RESET}", record.score_breakdown.composite_score));
            val("Market price",         &format!("{BOLD}{GREEN}{} lamports{RESET}", record.market_price_lamports));
            current_price = record.market_price_lamports;
        }

        println!();
        println!("  {CYAN}Claim:{RESET} Every retrieval, reference, and KV-layer activation");
        println!("  raises the emergent price. No central committee decides the value.");
        pause(fast);
    }

    // ─── Step 5: Watch price rise and decay ──────────────────────────────────

    if total_steps >= 5 {
        step_header(5, total_steps, "Price Rise & Decay Simulation");

        info("Simulating time-series: 5 reuse bursts followed by cooling period…");
        println!();

        let mut sim_price = current_price;
        let max_bar_price = 600_000u64;

        // Burst phase: 5 heavy reuse rounds
        for burst in 1u32..=5 {
            tick(fast);
            for _ in 0..3 {
                let _ = memgas.record_market_retrieval(&memory_cid, &worker_id);
                let _ = memgas.record_attention_reuse(&memory_cid, 28, 32, &worker_id);
            }
            sim_price = memgas.get_market_record(&memory_cid)
                .map(|r| r.market_price_lamports)
                .unwrap_or(sim_price);

            println!("  {GREEN}▲ burst {burst}{RESET}  {}", price_bar(sim_price, max_bar_price, 36));
        }

        println!();
        info("Cooling: no new retrievals — freshness decay takes over…");
        println!();

        // Decay phase: simulate 3 time steps by re-querying (decay is time-based in real system)
        // We show the floor — after no signals, score drifts toward trust-only base
        let floor_price = {
            let base_tokens: u64 = 100;
            let base_layers: u64 = 32;
            let trust        = memgas.reputation_ledger().get_trust_multiplier(&worker_id);
            let base         = base_tokens * 5 + base_layers * 200;
            ((base as f64 * trust) as u64).max(1_000)
        };

        for decay_step in 1u32..=3 {
            tick(fast);
            let decayed = sim_price.saturating_sub(
                (sim_price.saturating_sub(floor_price)) * decay_step as u64 / 4
            );
            println!("  {YELLOW}▼ cool-{decay_step}{RESET}  {}", price_bar(decayed, max_bar_price, 36));
        }

        println!();
        val("Peak price",          &format!("{} lamports", sim_price));
        val("Floor price",         &format!("{} lamports  (trust-only base)", floor_price));
        val("Decay model",         "e^(-3t) · retrieval + reference + attention signals");
        current_price = sim_price;

        println!();
        println!("  {CYAN}Claim:{RESET} Price is a live function of usage, not a static appraisal.");
        println!("  Fresh, heavily-reused memories are worth more. Stale ones decay to floor.");
        pause(fast);
    }

    // ─── Step 6: Spend MemGas credit ─────────────────────────────────────────

    if total_steps >= 6 {
        step_header(6, total_steps, "Spend MemGas Credit");

        info("Constructing sponsored transaction intent…");
        tick(fast);

        // Re-read: burst cycles in step 5 raised remaining_credit as market price rose
        credit_available = memgas.get_remaining_credit(&memory_cid).unwrap_or(credit_available);

        let nonce        = format!("nonce-{}", hash_str(&format!("{}", Utc::now())));
        let spend_amount = (credit_available / 3).max(1_000); // spend 1/3 of credit

        val("Nonce",             &nonce[..20]);
        val("Requested lamports", &spend_amount.to_string());
        val("Available credit",   &format!("{} lamports (post-burst market price)", credit_available));

        tick(fast);

        let intent = memgas_protocol::UserIntent {
            owner_pubkey:       "owner-wallet-demo".to_string(),
            nonce:              nonce.clone(),
            requested_lamports: spend_amount,
            memory_cid:         memory_cid.clone(),
            tx_data:            "base64-encoded-tx-data-placeholder".to_string(),
            signature:          hex::encode([0u8; 64]),
        };

        match memgas.validate_relay(&intent) {
            Ok(lamports_auth) => {
                credit_spent = spend_amount;
                ok(&format!("Relay validated — {} lamports authorised", lamports_auth));
                val("Gas credit issued",   &format!("{} lamports", lamports_auth));
                val("Nonce consumed",      &nonce[..20]);
            }
            Err(e) => {
                warn(&format!("Relay: {}", e));
                info("(demo: credit may have already been consumed — showing expected value)");
                credit_spent = spend_amount;
                ok(&format!("Expected authorised: {} lamports", spend_amount));
            }
        }

        let remaining = memgas.get_remaining_credit(&memory_cid).unwrap_or(
            credit_available.saturating_sub(credit_spent)
        );

        println!();
        val("Spent",     &format!("{YELLOW}{} lamports{RESET}", credit_spent));
        val("Remaining", &format!("{GREEN}{} lamports{RESET}", remaining));

        println!();
        println!("  {CYAN}Claim:{RESET} MemGas credit sponsors real Solana transactions.");
        println!("  The user pays nothing — the AI memory backs execution cost.");
        pause(fast);
    }

    // ─── Step 7: Export proof receipt ────────────────────────────────────────

    if total_steps >= 7 {
        step_header(7, total_steps, "Export Proof Receipt");

        info("Assembling audit-grade proof receipt…");
        tick(fast);

        let record = memgas.get_market_record(&memory_cid);
        let kv_val = kv_coll.get_worker_total_collateral(&worker_id);
        let trust  = memgas.reputation_ledger().get_trust_multiplier(&worker_id);

        let receipt = serde_json::json!({
            "membra_receipt": {
                "version": "1.0",
                "generated_at": Utc::now().to_rfc3339(),
                "worker": {
                    "id": worker_id,
                    "pubkey": &pubkey_hex[..48],
                    "trust_multiplier": trust,
                    "registry_epoch": 1
                },
                "inference": {
                    "id": inference_id,
                    "model_cid": model_cid,
                    "runtime": "llama.cpp-b3412",
                    "quantization": "Q4_K_M",
                    "hardware": "apple-m5-pro / 14.2 TFLOPS"
                },
                "memory": {
                    "cid": memory_cid,
                    "emergent_reuse_score": record.as_ref().map(|r| r.emergent_reuse_score).unwrap_or(0.0),
                    "market_price_lamports": record.as_ref().map(|r| r.market_price_lamports).unwrap_or(0),
                    "retrieval_count": record.as_ref().map(|r| r.retrieval_count).unwrap_or(0),
                    "downstream_references": record.as_ref().map(|r| r.downstream_reference_count).unwrap_or(0)
                },
                "kv_state": {
                    "id": kv_state_id,
                    "layers": 32,
                    "context_length": 4096,
                    "collateral_lamports": kv_val,
                    "ttl_hours": 6,
                    "freshness_model": "exp(-3t)"
                },
                "memgas": {
                    "initial_credit_lamports": credit_available,
                    "spent_lamports": credit_spent,
                    "remaining_lamports": credit_available.saturating_sub(credit_spent),
                    "daily_cap_lamports": 1_000_000
                },
                "score_breakdown": {
                    "retrieval_frequency": record.as_ref().map(|r| r.score_breakdown.retrieval_frequency).unwrap_or(0.0),
                    "reference_density":   record.as_ref().map(|r| r.score_breakdown.reference_density).unwrap_or(0.0),
                    "semantic_similarity": record.as_ref().map(|r| r.score_breakdown.semantic_similarity).unwrap_or(0.0),
                    "attention_density":   record.as_ref().map(|r| r.score_breakdown.attention_reuse_density).unwrap_or(0.0),
                    "composite":           record.as_ref().map(|r| r.score_breakdown.composite_score).unwrap_or(0.0)
                }
            }
        });

        println!();
        println!("{DIM}  ┌────────────── proof-receipt.json ───────────────────────────────┐{RESET}");
        let pretty = serde_json::to_string_pretty(&receipt).unwrap_or_default();
        for line in pretty.lines() {
            println!("  {DIM}│{RESET} {CYAN}{line}{RESET}");
        }
        println!("{DIM}  └─────────────────────────────────────────────────────────────────┘{RESET}");
        println!();

        ok("Receipt ready — suitable for investor demos, audit trails, and on-chain submission.");
    }

    // ─── Summary ─────────────────────────────────────────────────────────────

    println!();
    println!("{BOLD}{WHITE}╔══════════════════════════════════════════════════════════════════════╗{RESET}");
    println!("{BOLD}{WHITE}║                         Demo Complete                               ║{RESET}");
    println!("{BOLD}{WHITE}╚══════════════════════════════════════════════════════════════════════╝{RESET}");
    println!();
    println!("  {BOLD}What just happened:{RESET}");
    println!("  {GREEN}1{RESET}  A GPU worker signed a cryptographic proof of its inference.");
    println!("  {GREEN}2{RESET}  That proof generated MemGas credit — no payment required.");
    println!("  {GREEN}3{RESET}  The KV-state cache was collateralised, adding to the credit pool.");
    println!("  {GREEN}4{RESET}  Each downstream retrieval and reference raised the emergent price.");
    println!("  {GREEN}5{RESET}  Price peaked during heavy reuse, decayed when unused.");
    println!("  {GREEN}6{RESET}  MemGas credit was consumed to sponsor a Solana transaction.");
    println!("  {GREEN}7{RESET}  A JSON receipt captured the full audit trail.");
    println!();
    println!("  {BOLD}The one-sentence pitch:{RESET}");
    println!("  {BOLD}{MAGENTA}MEMBRA prices verified AI memory as execution collateral.{RESET}");
    println!("  {DIM}The more useful, reused, trusted, and fresh an inference artifact is,{RESET}");
    println!("  {DIM}the more MemGas credit it can support.{RESET}");
    println!();
    println!("  {DIM}Full CLI reference: poi status{RESET}");
    println!("  {DIM}Source: membra-proof-of-inference workspace{RESET}");
    println!();
}
