import os
import uuid
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

app = FastAPI(
    title="MEMBRA API",
    description="Chat-to-Chain Human Value Infrastructure",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TS = time.time()

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
PINATA_JWT = os.getenv("PINATA_JWT", "")
PROGRAM_ID = os.getenv("SOLANA_PROGRAM_ID", "membraQRGateway11111111111111111111111111111")

ARTIFACTS_DB: dict[str, dict] = {}
SESSIONS_DB: dict[str, dict] = {}
LEDGER: list[dict] = []


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def generate_artifact_id() -> str:
    return f"MEMBRA-ART-{uuid.uuid4().hex[:12].upper()}"


class StartSessionRequest(BaseModel):
    creator_wallet: str = Field(..., description="Public Solana wallet address")


class ChatArtifactRequest(BaseModel):
    session_id: str
    creator_wallet: str
    prompt: str
    response: str
    title: str = ""
    license_scope: str = "private"


class BuildEpochRequest(BaseModel):
    session_id: str
    creator_wallet: str
    files_created: list[str] = []
    build_output: str = ""
    test_results: str = ""
    title: str = ""


class ImageArtifactRequest(BaseModel):
    session_id: str
    creator_wallet: str
    image_hash: str
    visible_text: str = ""
    style_tokens: str = ""
    title: str = ""


class ApproveArtifactRequest(BaseModel):
    privacy_status: str = "approved_public"


class MainnetPaymentRequest(BaseModel):
    artifact_id: str
    payer_wallet: str
    recipient_wallet: str
    amount: float
    token: str = "SOL"
    funding_source: str = "none"
    approval_context: str = ""


class PolicyEvaluateRequest(BaseModel):
    content: str
    artifact_type: str = "prompt_response_pair"


class QRCreateRequest(BaseModel):
    artifact_id: str
    terms_uri: str = ""
    terms_hash: str = ""


def detect_secrets(content: str) -> list[str]:
    flags = []
    import re
    if re.search(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", content):
        flags.append("private_key_detected")
    if re.search(r"\b[0-9a-fA-F]{64}\b", content):
        flags.append("potential_seed_or_key")
    if re.search(r"(?:seed\s*phrase|mnemonic|secret\s*key|private\s*key)", content, re.I):
        flags.append("secret_language_detected")
    return flags


def detect_pii(content: str) -> list[str]:
    flags = []
    import re
    if re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", content):
        flags.append("email_detected")
    if re.search(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", content):
        flags.append("phone_detected")
    return flags


def detect_blocked_phrases(content: str) -> list[str]:
    blocked = [
        "guaranteed profit", "guaranteed return", "risk-free", "risk free",
        "guaranteed yield", "automatic payout", "official certification",
        "guaranteed equity",
    ]
    return [p for p in blocked if p.lower() in content.lower()]


def compute_appraisal(artifact_type: str, content: str) -> dict:
    scores = {
        "originality_score_0_100": 50,
        "usefulness_score_0_100": 50,
        "implementation_score_0_100": 50,
        "provenance_strength_0_100": 50,
        "commercial_proximity_0_100": 30,
        "privacy_risk_0_100": 20,
        "duplicate_penalty_0_100": 0,
    }
    base = 10
    total = (
        base
        + scores["originality_score_0_100"] * 1.5
        + scores["usefulness_score_0_100"] * 1.25
        + scores["implementation_score_0_100"] * 1.5
        + scores["provenance_strength_0_100"] * 1.0
        + scores["commercial_proximity_0_100"] * 2.0
        - scores["privacy_risk_0_100"] * 1.5
        - scores["duplicate_penalty_0_100"] * 2.0
    )
    total = max(0, total)
    return {
        **scores,
        "base_score": base,
        "total_score": round(total, 1),
        "llm_appraisal_usd": 0,
        "time_capital_band": "protected_floor",
        "disclaimer": "Model opinion only; not payment. Appraisal is a directional signal, not a cash valuation.",
    }


@app.get("/")
async def root():
    return {
        "app": "MEMBRA API",
        "version": "0.1.0",
        "doctrine": "Chat-to-Chain Human Value Infrastructure",
        "uptime_seconds": round(time.time() - START_TS, 2),
    }


@app.post("/api/sessions/start")
async def start_session(req: StartSessionRequest):
    session_id = f"SESSION-{uuid.uuid4().hex[:8].upper()}"
    session = {
        "session_id": session_id,
        "creator_wallet": req.creator_wallet,
        "started_at": now_iso(),
        "status": "active",
    }
    SESSIONS_DB[session_id] = session
    return session


@app.post("/api/artifacts/from-chat")
async def create_chat_artifact(req: ChatArtifactRequest):
    artifact_id = generate_artifact_id()
    raw_content = json.dumps({"prompt": req.prompt, "response": req.response})
    redacted_content = json.dumps({"prompt": "[REDACTED]", "response": req.response})
    proof_hash = sha256(raw_content)

    artifact = {
        "artifact_id": artifact_id,
        "creator_wallet": req.creator_wallet,
        "session_id": req.session_id,
        "artifact_type": "prompt_response_pair",
        "title": req.title or f"Chat Artifact {artifact_id[-8:]}",
        "summary": req.prompt[:200],
        "raw_content_hash_sha256": sha256(raw_content),
        "redacted_content_hash_sha256": sha256(redacted_content),
        "proof_hash": proof_hash,
        "license_scope": req.license_scope,
        "privacy_status": "private",
        "llm_appraisal_usd": 0,
        "appraisal_method": "deterministic_placeholder",
        "evidence_grade": 0,
        "payment_status": "unfunded",
        "funding_source": "none",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    ARTIFACTS_DB[artifact_id] = artifact
    LEDGER.append({"action": "artifact_created", "artifact_id": artifact_id, "ts": now_iso()})
    return artifact


@app.post("/api/artifacts/from-build-epoch")
async def create_build_artifact(req: BuildEpochRequest):
    artifact_id = generate_artifact_id()
    raw_content = json.dumps({"files": req.files_created, "build": req.build_output, "tests": req.test_results})
    proof_hash = sha256(raw_content)

    artifact = {
        "artifact_id": artifact_id,
        "creator_wallet": req.creator_wallet,
        "session_id": req.session_id,
        "artifact_type": "build_epoch",
        "title": req.title or f"Build Epoch {artifact_id[-8:]}",
        "summary": f"Build with {len(req.files_created)} files",
        "raw_content_hash_sha256": sha256(raw_content),
        "redacted_content_hash_sha256": sha256(raw_content),
        "proof_hash": proof_hash,
        "license_scope": "private",
        "privacy_status": "private",
        "llm_appraisal_usd": 0,
        "appraisal_method": "deterministic_placeholder",
        "evidence_grade": 0,
        "payment_status": "unfunded",
        "funding_source": "none",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    ARTIFACTS_DB[artifact_id] = artifact
    LEDGER.append({"action": "artifact_created", "artifact_id": artifact_id, "ts": now_iso()})
    return artifact


@app.post("/api/artifacts/from-image")
async def create_image_artifact(req: ImageArtifactRequest):
    artifact_id = generate_artifact_id()
    raw_content = json.dumps({"image_hash": req.image_hash, "text": req.visible_text, "style": req.style_tokens})
    proof_hash = sha256(raw_content)

    artifact = {
        "artifact_id": artifact_id,
        "creator_wallet": req.creator_wallet,
        "session_id": req.session_id,
        "artifact_type": "ui_asset",
        "title": req.title or f"Visual Artifact {artifact_id[-8:]}",
        "summary": f"Image hash: {req.image_hash[:16]}...",
        "raw_content_hash_sha256": sha256(raw_content),
        "redacted_content_hash_sha256": sha256(raw_content),
        "proof_hash": proof_hash,
        "license_scope": "private",
        "privacy_status": "private",
        "llm_appraisal_usd": 0,
        "appraisal_method": "deterministic_placeholder",
        "evidence_grade": 0,
        "payment_status": "unfunded",
        "funding_source": "none",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    ARTIFACTS_DB[artifact_id] = artifact
    LEDGER.append({"action": "artifact_created", "artifact_id": artifact_id, "ts": now_iso()})
    return artifact


@app.get("/api/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    if artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return ARTIFACTS_DB[artifact_id]


@app.post("/api/artifacts/{artifact_id}/approve")
async def approve_artifact(artifact_id: str, req: ApproveArtifactRequest):
    if artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    ARTIFACTS_DB[artifact_id]["privacy_status"] = req.privacy_status
    ARTIFACTS_DB[artifact_id]["updated_at"] = now_iso()
    LEDGER.append({"action": "artifact_approved", "artifact_id": artifact_id, "status": req.privacy_status, "ts": now_iso()})
    return ARTIFACTS_DB[artifact_id]


@app.post("/api/artifacts/{artifact_id}/hash")
async def hash_artifact(artifact_id: str):
    if artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    artifact = ARTIFACTS_DB[artifact_id]
    content = json.dumps(artifact, sort_keys=True)
    proof_hash = sha256(content)
    artifact["proof_hash"] = proof_hash
    artifact["updated_at"] = now_iso()
    return {"artifact_id": artifact_id, "proof_hash": proof_hash}


@app.post("/api/artifacts/{artifact_id}/github-anchor")
async def github_anchor(artifact_id: str):
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=503, detail="GITHUB_TOKEN not configured. Set GITHUB_TOKEN in .env")
    if artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "artifact_id": artifact_id,
        "status": "github_anchor_prepared",
        "note": "GitHub anchoring requires GITHUB_TOKEN and repo access. This endpoint validates the token exists.",
    }


@app.post("/api/artifacts/{artifact_id}/ipfs-pin")
async def ipfs_pin(artifact_id: str):
    if not PINATA_JWT:
        raise HTTPException(status_code=503, detail="PINATA_JWT not configured. Set PINATA_JWT in .env")
    if artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "artifact_id": artifact_id,
        "status": "ipfs_pin_prepared",
        "note": "IPFS pinning requires PINATA_JWT. This endpoint validates the token exists.",
    }


@app.post("/api/solana/devnet/initialize-artifact")
async def solana_devnet_initialize(artifact_id: str = Query(...)):
    if artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    artifact = ARTIFACTS_DB[artifact_id]
    return {
        "artifact_id": artifact_id,
        "program_id": PROGRAM_ID,
        "cluster": "devnet",
        "status": "ready_for_initialization",
        "proof_hash": artifact["proof_hash"],
        "note": "Initialize this artifact on devnet using the Anchor program. Requires wallet signature.",
    }


@app.post("/api/solana/devnet/support-artifact")
async def solana_devnet_support(artifact_id: str = Query(...), amount_lamports: int = Query(...)):
    if artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "artifact_id": artifact_id,
        "amount_lamports": amount_lamports,
        "cluster": "devnet",
        "status": "ready_for_support",
        "note": "Support this artifact on devnet. Requires wallet signature and terms acceptance.",
    }


@app.post("/api/solana/mainnet/prepare-payment")
async def mainnet_prepare_payment(req: MainnetPaymentRequest):
    if req.artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact = ARTIFACTS_DB[req.artifact_id]

    if artifact["funding_source"] == "none" and req.funding_source == "none":
        raise HTTPException(
            status_code=400,
            detail="Cannot prepare mainnet payment: funding_source is 'none'. A funded source (buyer, sponsor, donor, grant, bounty, license, escrow, treasury) is required.",
        )

    policy = evaluate_policy_internal(
        f"Mainnet payment: {req.amount} {req.token} from {req.payer_wallet} to {req.recipient_wallet} for artifact {req.artifact_id}"
    )

    if not policy["allowed"]:
        raise HTTPException(status_code=403, detail=f"Policy blocked: {policy['block_reasons']}")

    return {
        "artifact_id": req.artifact_id,
        "transaction_description": f"Payment of {req.amount} {req.token} from {req.payer_wallet} to {req.recipient_wallet}",
        "policy_result": policy,
        "risk_flags": policy["risk_flags"],
        "requires_manual_signature": True,
        "note": "Mainnet transaction prepared but NOT sent. Requires explicit user/multisig approval. No auto-signing.",
    }


def evaluate_policy_internal(content: str) -> dict:
    secrets = detect_secrets(content)
    pii = detect_pii(content)
    blocked = detect_blocked_phrases(content)
    risk_flags = secrets + pii

    allowed = True
    block_reasons = []

    if secrets:
        allowed = False
        block_reasons.append("Secret or private key material detected")
    if blocked:
        allowed = False
        block_reasons.append(f"Blocked phrases detected: {blocked}")

    requires_manual = True
    requires_legal = bool(blocked)

    return {
        "allowed": allowed,
        "risk_flags": risk_flags,
        "requires_manual_approval": requires_manual,
        "requires_legal_review": requires_legal,
        "block_reasons": block_reasons,
    }


@app.post("/api/policy/evaluate")
async def evaluate_policy(req: PolicyEvaluateRequest):
    return evaluate_policy_internal(req.content)


@app.get("/api/ledger")
async def get_ledger():
    return {"ledger": LEDGER, "count": len(LEDGER)}


@app.get("/api/proof/{artifact_id}")
async def get_proof(artifact_id: str):
    if artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    artifact = ARTIFACTS_DB[artifact_id]
    return {
        "artifact_id": artifact_id,
        "title": artifact["title"],
        "summary": artifact["summary"],
        "creator_wallet": artifact["creator_wallet"],
        "proof_hash": artifact["proof_hash"],
        "raw_content_hash": artifact["raw_content_hash_sha256"],
        "redacted_content_hash": artifact["redacted_content_hash_sha256"],
        "evidence_grade": artifact["evidence_grade"],
        "appraisal": artifact["llm_appraisal_usd"],
        "github_commit": artifact.get("github_commit"),
        "ipfs_cid": artifact.get("ipfs_cid"),
        "solana_devnet_tx": artifact.get("solana_devnet_tx"),
        "solana_receipt_pda": artifact.get("solana_receipt_pda"),
        "payment_status": artifact["payment_status"],
        "funding_source": artifact["funding_source"],
        "privacy_status": artifact["privacy_status"],
        "disclaimers": [
            "This is a proof of artifact existence, not a payment guarantee.",
            "No private keys or seed phrases are stored.",
            "Mainnet execution requires explicit human/multisig approval.",
        ],
    }


@app.post("/api/qr/create")
async def create_qr(req: QRCreateRequest):
    if req.artifact_id not in ARTIFACTS_DB:
        raise HTTPException(status_code=404, detail="Artifact not found")
    artifact = ARTIFACTS_DB[req.artifact_id]
    qr_payload = {
        "protocol": "MEMBRA-QR-0.1",
        "cluster": "devnet",
        "action": "OPEN_ARTIFACT_SUPPORT_PAGE",
        "artifact_id": req.artifact_id,
        "program_id": PROGRAM_ID,
        "artifact_pda": "",
        "creator_public_wallet": artifact["creator_wallet"],
        "terms_uri": req.terms_uri or f"ipfs://{artifact['proof_hash']}",
        "terms_hash": req.terms_hash or f"sha256:{artifact['proof_hash']}",
        "proof_hash": f"sha256:{artifact['proof_hash']}",
        "execution_requires_user_signature": True,
        "not_profit_guarantee": True,
        "not_investment": True,
    }
    campaign_id = f"CAMPAIGN-{uuid.uuid4().hex[:8].upper()}"
    return {"campaign_id": campaign_id, "qr_payload": qr_payload}


@app.get("/api/qr/{campaign_id}")
async def get_qr_campaign(campaign_id: str):
    return {
        "campaign_id": campaign_id,
        "status": "active",
        "note": "QR campaign data. In production, this would fetch from database.",
    }


@app.get("/api/state")
async def get_state():
    return {
        "app": "MEMBRA Idea Monetization Layer v0",
        "uptime_seconds": round(time.time() - START_TS, 2),
        "artifact_count": len(ARTIFACTS_DB),
        "session_count": len(SESSIONS_DB),
        "ledger_entries": len(LEDGER),
        "config": {
            "solana_rpc": SOLANA_RPC_URL,
            "has_github_token": bool(GITHUB_TOKEN),
            "has_pinata_jwt": bool(PINATA_JWT),
            "program_id": PROGRAM_ID,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", "8000")))
