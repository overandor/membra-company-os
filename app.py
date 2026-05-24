import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from aiohttp import web

# Ensure repo root + llm-os on path for imports
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
_LLM_OS = os.path.join(_HERE, "llm-os")
if _LLM_OS not in sys.path:
    sys.path.insert(0, _LLM_OS)

from llm_signal_hunter import (
    get_latest_cycle,
    run_scan_cycle,
    start_background_scanner,
)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("SPACE_PORT", "7860")))

START_TS = time.time()


def now_ts():
    return time.time()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


VALUE_STATE_MACHINE = {
    "id": "value_state_machine",
    "name": "Value State Machine",
    "description": "Human idea → proof → product → signal → settlement → money",
    "stages": [
        {"id": "idea", "label": "Human Idea", "status": "completed", "detail": "MCHAT thesis conceived"},
        {"id": "proof", "label": "Proof", "status": "completed", "detail": "Public proof capsule generated"},
        {"id": "product", "label": "Product", "status": "active", "detail": "QR Gateway + Wallet Signature live"},
        {"id": "signal", "label": "Signal", "status": "pending", "detail": "Market signal awaiting external validation"},
        {"id": "settlement", "label": "Settlement", "status": "pending", "detail": "Stripe settlement not yet triggered"},
        {"id": "money", "label": "Money", "status": "pending", "detail": "$0.00 until external settlement clears"},
    ],
}

QR_GATEWAY_STATE_MACHINE = {
    "id": "qr_gateway_state_machine",
    "name": "QR Gateway State Machine",
    "description": "QR scan → terms → wallet signature → support payment → rebate/credit → receipt → proof event",
    "stages": [
        {"id": "qr_scan", "label": "QR Scan", "status": "completed", "detail": "Gateway endpoint live"},
        {"id": "terms", "label": "Terms", "status": "completed", "detail": "Terms of support displayed"},
        {"id": "wallet_sig", "label": "Wallet Signature", "status": "active", "detail": "Awaiting Solana wallet signature"},
        {"id": "support_payment", "label": "Support Payment", "status": "pending", "detail": "External payment not yet received"},
        {"id": "rebate_credit", "label": "Rebate / Credit", "status": "pending", "detail": "Rebate logic defined, not executed"},
        {"id": "receipt", "label": "Receipt", "status": "pending", "detail": "Receipt generated on settlement"},
        {"id": "proof_event", "label": "Proof Event", "status": "pending", "detail": "Immutable proof event recorded"},
    ],
}

TOKEN_LAUNCH_STATE_MACHINE = {
    "id": "token_launch_state_machine",
    "name": "Token Launch State Machine",
    "description": "Manifest → metadata → legal review → testnet → mainnet mint → proof capsule → support economy",
    "stages": [
        {"id": "manifest", "label": "Manifest", "status": "completed", "detail": "MCHAT launch manifest published"},
        {"id": "metadata", "label": "Metadata", "status": "completed", "detail": "Token metadata defined"},
        {"id": "legal_review", "label": "Legal Review", "status": "pending", "detail": "Legal review not yet completed"},
        {"id": "testnet", "label": "Testnet", "status": "pending", "detail": "Testnet deployment pending"},
        {"id": "mainnet_mint", "label": "Mainnet Mint", "status": "pending", "detail": "Mint address not created"},
        {"id": "proof_capsule", "label": "Proof Capsule", "status": "pending", "detail": "Awaiting mint for capsule generation"},
        {"id": "support_economy", "label": "Support Economy", "status": "pending", "detail": "Economy activates post-mint"},
    ],
}

CHAT_PIPELINE = {
    "id": "chat_pipeline",
    "name": "CHAT → TERMINAL → CHAIN DEPLOY Protocol",
    "repo": "overandor/chat-pipeline",
    "spec": "docs/CHAT_TERMINAL_CHAIN_DEPLOY_PROTOCOL_V0.md",
    "commit": "5dad707d50a867ab317b4f43cb40c5aec67af6c8",
    "definition": "chat = conversation + terminal + repo + wallet identity + proof engine + policy engine + chain deployer",
    "stages": [
        {"id": "transcript", "label": "Chat Transcript", "status": "completed", "detail": "Conversation captured"},
        {"id": "llm_plan", "label": "LLM Plan", "status": "completed", "detail": "Build plan generated"},
        {"id": "terminal", "label": "Terminal Workspace", "status": "active", "detail": "Sandbox ready for file ops"},
        {"id": "files", "label": "Files Created", "status": "active", "detail": "Source artifacts written"},
        {"id": "test_build", "label": "Tests / Build", "status": "pending", "detail": "Test runner pending"},
        {"id": "hashes", "label": "Artifact Hashes", "status": "pending", "detail": "Content-addressed hashes pending"},
        {"id": "github", "label": "GitHub Anchor", "status": "pending", "detail": "Commit anchor pending"},
        {"id": "devnet", "label": "Solana Devnet Deploy", "status": "pending", "detail": "Devnet deploy pending"},
        {"id": "qr_campaign", "label": "QR Allocation Campaign", "status": "pending", "detail": "Campaign pending"},
        {"id": "chain_receipt", "label": "Chain Receipt", "status": "pending", "detail": "Receipt pending"},
        {"id": "mainnet_tx", "label": "Mainnet TX Prepared", "status": "pending", "detail": "Awaiting approval"},
        {"id": "sign", "label": "User/Multisig Signs", "status": "pending", "detail": "Explicit approval required"},
    ],
    "boundary": "LLM can build, test, hash, commit, deploy to devnet. LLM must not hold raw private keys or auto-sign mainnet without explicit policy approval.",
}

QR_ALLOCATION_RULES = {
    "core_sentence": "Every verified QR read of a MEMBRA chat can trigger an immediate token allocation event tied to that chat's pool, proof capsule, and public rules.",
    "hard_boundary": "A QR read can immediately allocate protocol units, points, credits, claim receipts, or testnet tokens. A QR read should not automatically transfer valuable mainnet tokens or fiat.",
    "conditions": [
        "1. the reader accepts terms",
        "2. the wallet is connected",
        "3. the pool is funded",
        "4. anti-sybil checks pass",
        "5. token supply exists",
        "6. the smart contract/program authorizes the allocation",
        "7. compliance/risk rules allow it",
        "8. the user signs if required",
    ],
}

SPRINTS = [
    {"name": "Sprint 1 — Terminal + Repo", "items": "chat workspace, file writer, terminal sandbox, test runner, artifact hasher, GitHub anchor", "status": "active"},
    {"name": "Sprint 2 — Solana Devnet", "items": "devnet wallet adapter, devnet memo anchor, devnet SPL token mint, QR allocation campaign, chain receipt recorder", "status": "pending"},
    {"name": "Sprint 3 — Policy Engine", "items": "allowlist/blocklist, mainnet transaction preview, manual approval UI, spending caps, receipt hash", "status": "pending"},
    {"name": "Sprint 4 — Mainnet-Ready Release", "items": "multisig/KMS/HSM/MPC, audit log, pause controls, notary/KYC bridge, Stripe pool bridge, public proof capsule deploy", "status": "pending"},
]

PRODUCT_ARCHITECTURE = [
    {"layer": "MEMBRA Idea Monetization Layer v0", "status": "active"},
    {"layer": "QR Gateway", "status": "active"},
    {"layer": "Solana Wallet Signature", "status": "active"},
    {"layer": "MCHAT Launch Discipline", "status": "active"},
    {"layer": "Public Proof Capsule", "status": "active"},
    {"layer": "External Settlement", "status": "pending"},
]

STATUS_CARDS = {
    "mchat_status": "MANIFESTED, NOT MINTED",
    "mint_address": "Not Created",
    "official_money": "$0.00 Until External Settlement",
    "execution_requires_signature": True,
}

DOCTRINE = {
    "proof_is_not_money": True,
    "token_is_not_profit": True,
    "testnet_is_not_settlement": True,
    "mint_address_means_token_exists": True,
    "stripe_settlement_is_official_money": True,
}

KEY_LINE = (
    "MEMBRA does not pretend a chat is money. "
    "MEMBRA turns a chat into a proof capsule, a token thesis, "
    "a public launch manifest, and a disciplined path to settlement."
)

ONE_SENTENCE_TRUTH = (
    "MEMBRA turns each chat into an executable terminal-backed protocol workspace "
    "where the LLM can build, test, hash, commit, and deploy to chain under policy, "
    "while mainnet signing and real payouts remain gated by explicit approval and funded settlement."
)

FOOTER = (
    "A chat can birth a token thesis, manifest, proof economy, and public narrative. "
    "The token exists only after a signed Solana mainnet mint transaction creates a real mint address. "
    "Official money exists only after external settlement clears."
)


def build_state():
    return {
        "app": "MEMBRA Idea Monetization Layer v0",
        "uptime_seconds": round(now_ts() - START_TS, 2),
        "ts": now_ts(),
        "iso": now_iso(),
        "doctrine": DOCTRINE,
        "status_cards": STATUS_CARDS,
        "key_line": KEY_LINE,
        "one_sentence_truth": ONE_SENTENCE_TRUTH,
        "footer": FOOTER,
        "product_architecture": PRODUCT_ARCHITECTURE,
        "value_state_machine": VALUE_STATE_MACHINE,
        "qr_gateway_state_machine": QR_GATEWAY_STATE_MACHINE,
        "token_launch_state_machine": TOKEN_LAUNCH_STATE_MACHINE,
        "chat_pipeline": CHAT_PIPELINE,
        "qr_allocation_rules": QR_ALLOCATION_RULES,
        "sprints": SPRINTS,
    }


async def api_state(request):
    return web.json_response(build_state(), dumps=lambda x: json.dumps(x, default=str))


async def api_signals(request):
    """Return the latest LLM signal hunter cycle."""
    cycle = get_latest_cycle()
    if not cycle:
        cycle = {"status": "initialising", "message": "First scan cycle has not completed yet"}
    return web.json_response(cycle, dumps=lambda x: json.dumps(x, default=str))


async def api_signals_now(request):
    """Run one scan cycle immediately and return the result."""
    result = run_scan_cycle()
    return web.json_response(result, dumps=lambda x: json.dumps(x, default=str))


async def api_profit(request):
    """Return profit summary from the signal ledger."""
    from llm_signal_hunter import load_ledger, compute_profit_summary
    entries = load_ledger()
    summary = compute_profit_summary(entries)
    return web.json_response(summary, dumps=lambda x: json.dumps(x, default=str))


async def index(request):
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
    with open(template_path, "r") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")


async def main():
    print(f"[boot] MEMBRA Idea Monetization Layer v0 starting on port {PORT}", flush=True)
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/state", api_state)
    app.router.add_get("/signals", api_signals)
    app.router.add_get("/signals/now", api_signals_now)
    app.router.add_get("/profit", api_profit)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    print(f"[boot] Dashboard live at http://{HOST}:{PORT}", flush=True)
    print(f"[boot] LLM Signal Hunter endpoints: /signals, /signals/now, /profit", flush=True)
    await start_background_scanner()
    print(f"[boot] Background signal scanner started (every 60s)", flush=True)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
