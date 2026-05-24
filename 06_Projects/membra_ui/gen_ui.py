#!/usr/bin/env python3
"""MEMBRA UI Generator — builds landing.html + dashboard.html from fragments."""
from pathlib import Path

BASE = Path("/Users/alep/Downloads/membra_ui")
BASE.mkdir(parents=True, exist_ok=True)

def write(name, parts):
    path = BASE / name
    path.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {path} ({path.stat().st_size:,} bytes)")

H = [
    "<!doctype html><html lang='en'><head>",
    "<meta charset='utf-8'/>",
    "<meta name='viewport' content='width=device-width,initial-scale=1'/>",
    "<link rel='stylesheet' href='/ui/membra.css'/>",
]

L = H + [
    "<title>MEMBRA — Chat-to-Chain Human Value Infrastructure</title></head><body>",
    "<div class='bg-ambient'></div>",
    "<section class='hero'>",
    "<div class='hero-badge'>LIVE PROOF • QR GATEWAY • SOLANA LIQUIDITY</div>",
    "<h1>MEMBRA <span>CHAT → CHAIN</span></h1>",
    "<p>MEMBRA turns chats, builds, prompts, proofs, and terminal work into verifiable contribution artifacts routed through QR support, Solana receipts, and policy-gated settlement.</p>",
    "<div><a class='btn btn-primary' href='/dashboard'>Open Dashboard</a> <a class='btn btn-outline' href='/api/state'>View State API</a></div>",
    "</section>",
    "<section class='features'>",
    "<div class='feature-card'><div class='feature-icon'>💬</div><h3>Chat as Interface</h3><p>Every conversation becomes structured proof, artifact metadata, and optional token thesis.</p></div>",
    "<div class='feature-card'><div class='feature-icon'>⌘</div><h3>Terminal as Executor</h3><p>The LLM can guide builds, hashes, commits, receipts, and deployment workflows.</p></div>",
    "<div class='feature-card'><div class='feature-icon'>◎</div><h3>Solana as Receipt Layer</h3><p>Devnet rehearsal first. Mainnet only with human or multisig approval.</p></div>",
    "</section>",
    "<footer>Proof ≠ Money • Token ≠ Profit • Mainnet Requires Signature • Funding Source Is Money</footer>",
    "</body></html>",
]

D = H + [
    "<title>MEMBRA Dashboard</title></head><body>",
    "<div class='bg-ambient'></div>",
    "<main class='dashboard'>",
    "<header class='header'><div><div class='eyebrow'>MEMBRA LIVE</div><h1>Chat-to-Chain Dashboard</h1><p>Neo-neomorphic glass membrane control center for proof, QR allocation, Solana receipts, and settlement discipline.</p></div><div class='status-pill'>MCHAT STATUS: MANIFESTED, NOT MINTED</div></header>",
    "<section class='grid'>",
    "<div class='card'><div class='label'>Mint Address</div><div class='value danger'>Not Created</div></div>",
    "<div class='card'><div class='label'>Official Money</div><div class='value gold'>$0.00</div><p>Until external settlement</p></div>",
    "<div class='card'><div class='label'>Execution Requires</div><div class='value'>User Signature: True</div></div>",
    "<div class='card'><div class='label'>Network</div><div class='value'>Solana Devnet / Mainnet Gate</div></div>",
    "</section>",
    "<section class='card wide'><h2>Doctrine Stack</h2><div class='doctrine'><span>Proof ≠ Money</span><span>Token ≠ Profit</span><span>Testnet ≠ Settlement</span><span>Mint Address = Token Exists</span><span>Stripe Settlement = Official Fiat Money</span></div></section>",
    "<section class='grid-3'>",
    "<div class='card'><h3>1. Value State Machine</h3><ol><li>Human Idea</li><li>Proof</li><li>Product</li><li>Signal</li><li>Settlement</li><li>Money</li></ol></div>",
    "<div class='card'><h3>2. QR Gateway State Machine</h3><ol><li>QR Scan</li><li>Terms</li><li>Wallet Signature</li><li>Support Payment</li><li>Receipt</li><li>Proof Event</li></ol></div>",
    "<div class='card'><h3>3. Token Launch State Machine</h3><ol><li>Manifest</li><li>Metadata</li><li>Legal Review</li><li>Testnet</li><li>Mainnet Mint</li><li>Support Economy</li></ol></div>",
    "</section>",
    "<section class='card wide'><h2>Chat → Terminal → Chain Deploy</h2><p class='mono'>chat = conversation + terminal + repo + wallet identity + proof engine + policy engine + chain deployer</p><div class='pipeline'><span>Chat</span><span>LLM Plan</span><span>Terminal</span><span>Repo</span><span>Hash</span><span>GitHub/IPFS</span><span>Solana Receipt</span><span>QR Pool</span><span>Human Signature</span></div></section>",
    "<section class='grid'>",
    "<div class='card'><div class='label'>Corpus Appraisal Value</div><div class='big accent'>$9,251,500</div><p>File-level complexity-adjusted pricing. Knowledge seed, not liquid.</p><div class='progress-bar'><div class='progress-fill' style='width:100%'></div></div></div>",
    "<div class='card'><div class='label'>Indexed Knowledge Value</div><div class='big' id='indexedValue'>Loading...</div><p>Active / searchable / monetizable corpus chunks.</p><div class='progress-bar'><div class='progress-fill' style='width:0%' id='indexedBar'></div></div></div>",
    "<div class='card'><div class='label'>Treasury Balance</div><div class='big gold' id='treasuryBal'>0.00 SOL</div><p>Real SOL/USDC received. Only this is liquid.</p><div class='progress-bar'><div class='progress-fill' style='width:0%' id='treasuryBar'></div></div></div>",
    "<div class='card'><div class='label'>Liquid Market Value</div><div class='big danger' id='liquidValue'>$0.00</div><p>Pool TVL + actual swap depth. Requires treasury > 0.</p><div class='progress-bar'><div class='progress-fill' style='width:0%' id='liquidBar'></div></div></div>",
    "</section>",
    "<section class='card wide'><h2>Self-Funding Chat Liquidity</h2><p>The first chat may bootstrap liquidity only if real SOL/USDC is deposited. Appraisal alone cannot create withdrawable cash.</p><div class='terminal'><div>&gt; llm.appraise_machine()</div><div>&gt; proof.hash_files()</div><div>&gt; wallet.require_signature()</div><div>&gt; pool.await_real_funding()</div><div>&gt; settlement.unlock_only_after_payment()</div></div></section>",
    "<footer>Conversation is proof. Proof is not money. Funding source is money. Human signature is law.</footer>",
    "</main></body></html>",
]

write("landing.html", L)
write("dashboard.html", D)
print("Done.")
