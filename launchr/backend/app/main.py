"""LaunchR FastAPI backend — Phase 3: Proof Token + Wallet + LLM."""
import os
import uuid
import hashlib
import httpx
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy import select, desc

from app.models import (
    ScanRequest, LaunchRequest, DeveloperAssetMap, EvidencePacket,
    AppraisalResult, Asset, EvidencePacketV2, OwnershipStatus, EpochRecord,
    OwnershipVerifyRequest, EpochCreateRequest, Portfolio, PortfolioWithHF,
    TokenMint, WalletConnect, LLMUseCase, DeveloperCapitalization,
    MintProofRequest, WalletRegisterRequest, LLMGenerateRequest,
    PackageInfo, RegistryScanResult, DeploymentInfo, DeploymentScanResult,
    QualityScoreResult, MultiSourceAsset, MultiSourceProfile, EvidenceExport,
)
from app.github_scanner import GitHubScanner, GitHubRateLimitError
from app.hf_scanner import HuggingFaceScanner
from app.registry_scanner import RegistryScanner
from app.deployment_scanner import DeploymentScanner
from app.quality_scorer import QualityScorer
from app.appraisal_engine import AppraisalEngine
from app.evidence_builder import EvidenceBuilder
from app.evidence_v2 import EvidenceBuilderV2
from app.portfolio_engine import PortfolioEngine
from app.ecosystem_engine import EcosystemEngine
from app.report_generator import generate_appraisal_pdf
from app.canonical_hash import compute_packet_hash, verify_packet_hash
from app.database import init_db, AsyncSessionLocal

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="LaunchR API",
    description="GitHub-native software asset launchpad. Phase 3: Proof Token + Wallet + LLM.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

appraisal_engine = AppraisalEngine()
evidence_builder = EvidenceBuilder()
evidence_builder_v2 = EvidenceBuilderV2()
portfolio_engine = PortfolioEngine()
ecosystem_engine = EcosystemEngine()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "phase": "Phase 3 — Proof Token + Wallet + LLM",
        "github_token_configured": bool(GITHUB_TOKEN),
        "openai_key_configured": bool(OPENAI_API_KEY),
    }


# =============================================================================
# PHASE 1 ENDPOINTS (preserved)
# =============================================================================

@app.post("/scan", response_model=DeveloperAssetMap)
async def scan_user(request: ScanRequest):
    scanner = GitHubScanner()
    try:
        repos = await scanner.scan_user(request.github_username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GitHub user not found or API error: {e}")
    finally:
        await scanner.close()

    if not repos:
        raise HTTPException(status_code=404, detail="No public repos found for this user.")

    asset_map = appraisal_engine.build_asset_map(request.github_username, repos)

    if scanner.rate_limited:
        asset_map.metadata["rate_limited"] = True
        asset_map.metadata["warning"] = (
            "GitHub API rate limit exceeded. Showing cached/demo data. "
            "Set GITHUB_TOKEN on the backend for full access."
        )

    async with AsyncSessionLocal() as db:
        from app.database import DBGitHubAccount
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        stmt = sqlite_insert(DBGitHubAccount).values(
            id=str(uuid.uuid4()),
            username=request.github_username,
            scanned_at=datetime.utcnow(),
            raw_data=asset_map.model_dump(mode="json"),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["username"],
            set_={"scanned_at": datetime.utcnow(), "raw_data": asset_map.model_dump(mode="json")}
        )
        await db.execute(stmt)
        await db.commit()

    return asset_map


@app.get("/appraise/{username}/{repo_full_name:path}", response_model=AppraisalResult)
async def appraise_repo(username: str, repo_full_name: str):
    scanner = GitHubScanner()
    try:
        repos = await scanner.scan_user(username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GitHub user not found: {e}")
    finally:
        await scanner.close()

    target = next((r for r in repos if r.full_name == repo_full_name), None)
    if not target:
        raise HTTPException(status_code=404, detail="Repository not found in user's public repos.")

    appraisal = appraisal_engine.appraise_repo(username, target, repos)

    async with AsyncSessionLocal() as db:
        from app.database import DBAppraisal
        db_appraisal = DBAppraisal(
            id=appraisal.appraisal_id,
            github_username=username,
            repo_full_name=repo_full_name,
            raw_score=appraisal.raw_score,
            risk_adjusted_score=appraisal.risk_adjusted_score,
            risk_level=appraisal.risk_level.value,
            suggested_market_cap=appraisal.suggested_initial_market_cap_usd,
            created_at=appraisal.created_at,
            raw_data=appraisal.model_dump(mode="json"),
        )
        db.add(db_appraisal)
        await db.commit()

    return appraisal


@app.get("/evidence/{username}/{repo_full_name:path}", response_model=EvidencePacket)
async def build_evidence(username: str, repo_full_name: str):
    scanner = GitHubScanner()
    try:
        repos = await scanner.scan_user(username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GitHub user not found: {e}")
    finally:
        await scanner.close()

    target = next((r for r in repos if r.full_name == repo_full_name), None)
    if not target:
        raise HTTPException(status_code=404, detail="Repository not found.")

    appraisal = appraisal_engine.appraise_repo(username, target, repos)
    packet = evidence_builder.build_packet(username, target, appraisal)

    async with AsyncSessionLocal() as db:
        from app.database import DBEvidencePacket
        db_pkt = DBEvidencePacket(
            id=packet.packet_id,
            github_username=username,
            repo_full_name=repo_full_name,
            repo_snapshot_hash=packet.repo_snapshot_hash,
            launch_readiness_score=packet.launch_readiness_score,
            do_not_mint_flags=packet.do_not_mint_flags,
            created_at=packet.created_at,
            raw_data=packet.model_dump(mode="json"),
        )
        db.add(db_pkt)
        await db.commit()

    return packet


@app.get("/report/pdf/{username}/{repo_full_name:path}")
async def download_report(username: str, repo_full_name: str):
    scanner = GitHubScanner()
    try:
        repos = await scanner.scan_user(username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GitHub user not found: {e}")
    finally:
        await scanner.close()

    target = next((r for r in repos if r.full_name == repo_full_name), None)
    if not target:
        raise HTTPException(status_code=404, detail="Repository not found.")

    asset_map = appraisal_engine.build_asset_map(username, repos)
    appraisal = appraisal_engine.appraise_repo(username, target, repos)
    packet = evidence_builder.build_packet(username, target, appraisal)

    pdf_bytes = generate_appraisal_pdf(asset_map, packet)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=launchr_report_{username}.pdf"},
    )


@app.get("/repos/{username}")
async def list_repos(username: str):
    scanner = GitHubScanner()
    try:
        repos = await scanner.scan_user(username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GitHub user not found: {e}")
    finally:
        await scanner.close()
    return {"username": username, "repos": [r.model_dump(mode="json") for r in repos]}


# =============================================================================
# PHASE 2: ASSET MANAGEMENT
# =============================================================================

@app.post("/assets", response_model=Asset)
async def create_asset(request: ScanRequest):
    """Scan a GitHub user and create a persistent Asset for a selected repo."""
    scanner = GitHubScanner()
    try:
        repos = await scanner.scan_user(request.github_username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GitHub user not found or API error: {e}")
    finally:
        await scanner.close()

    if not repos:
        raise HTTPException(status_code=404, detail="No public repos found for this user.")

    # Use the top repo as the default asset
    top_repo = max(repos, key=lambda r: r.stars)
    asset_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as db:
        from app.database import DBAsset
        asset = DBAsset(
            id=asset_id,
            github_username=request.github_username,
            repo_full_name=top_repo.full_name,
            source_type="github_repo",
            source_uri=f"https://github.com/{top_repo.full_name}",
            name=top_repo.name,
            description=top_repo.description,
            stars=top_repo.stars,
            language=top_repo.language,
            license=top_repo.license,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            raw_repo_data=top_repo.model_dump(mode="json"),
        )
        db.add(asset)
        await db.commit()
        await db.refresh(asset)

    return Asset(
        asset_id=asset.id,
        github_username=asset.github_username,
        repo_full_name=asset.repo_full_name,
        source_type=asset.source_type,
        source_uri=asset.source_uri,
        name=asset.name,
        description=asset.description,
        stars=asset.stars,
        language=asset.language,
        license=asset.license,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        raw_repo_data=asset.raw_repo_data,
    )


@app.get("/assets")
async def list_assets():
    async with AsyncSessionLocal() as db:
        from app.database import DBAsset
        result = await db.execute(select(DBAsset).order_by(desc(DBAsset.created_at)))
        rows = result.scalars().all()
    return {
        "assets": [
            {
                "asset_id": r.id,
                "github_username": r.github_username,
                "repo_full_name": r.repo_full_name,
                "name": r.name,
                "stars": r.stars,
                "language": r.language,
                "license": r.license,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@app.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBAsset
        result = await db.execute(select(DBAsset).where(DBAsset.id == asset_id))
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found.")
        return {
            "asset_id": row.id,
            "github_username": row.github_username,
            "repo_full_name": row.repo_full_name,
            "source_type": row.source_type,
            "source_uri": row.source_uri,
            "name": row.name,
            "description": row.description,
            "stars": row.stars,
            "language": row.language,
            "license": row.license,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "raw_repo_data": row.raw_repo_data,
        }


# =============================================================================
# PHASE 2: OWNERSHIP VERIFICATION
# =============================================================================

@app.post("/verify/github-owner")
async def verify_github_owner(request: OwnershipVerifyRequest):
    """Verify that the caller owns the GitHub repo via token or OAuth."""
    token = request.github_token or GITHUB_TOKEN
    if not token:
        raise HTTPException(status_code=401, detail="No GitHub token provided. Set GITHUB_TOKEN env var or pass github_token.")

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        # Check who the token belongs to
        me_resp = await client.get("https://api.github.com/user", headers=headers)
        if me_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid GitHub token.")
        me = me_resp.json()
        token_user = me.get("login", "").lower()

        # Check repo info
        repo_resp = await client.get(f"https://api.github.com/repos/{request.repo_full_name}", headers=headers)
        if repo_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Repository not found or no access.")
        repo = repo_resp.json()
        owner = repo.get("owner", {}).get("login", "").lower()
        repo_name = repo.get("name", "")

        verified = token_user == owner

    # Upsert ownership record
    async with AsyncSessionLocal() as db:
        from app.database import DBAsset, DBOwnership
        # Find or create asset
        asset_result = await db.execute(
            select(DBAsset).where(DBAsset.repo_full_name == request.repo_full_name)
        )
        asset = asset_result.scalar_one_or_none()
        if not asset:
            asset = DBAsset(
                id=str(uuid.uuid4()),
                github_username=request.github_username,
                repo_full_name=request.repo_full_name,
                source_type="github_repo",
                source_uri=f"https://github.com/{request.repo_full_name}",
                name=repo_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                raw_repo_data=repo,
            )
            db.add(asset)
            await db.flush()

        # Upsert ownership
        own_result = await db.execute(
            select(DBOwnership).where(DBOwnership.asset_id == asset.id)
        )
        ownership = own_result.scalar_one_or_none()
        if not ownership:
            ownership = DBOwnership(
                id=str(uuid.uuid4()),
                asset_id=asset.id,
                github_username=request.github_username,
                repo_full_name=request.repo_full_name,
            )
            db.add(ownership)

        ownership.verified = verified
        ownership.verification_method = request.verification_method
        ownership.verified_at = datetime.utcnow() if verified else None
        ownership.github_token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
        await db.commit()
        await db.refresh(ownership)

    return OwnershipStatus(
        asset_id=asset.id,
        github_username=request.github_username,
        repo_full_name=request.repo_full_name,
        verified=verified,
        verification_method=request.verification_method,
        verified_at=ownership.verified_at,
        can_launch=verified and not any(
            f.auto_block for f in appraisal_engine.risk_engine.scan_repo(request.github_username, {
                "name": repo_name, "full_name": request.repo_full_name, "description": "", "stars": 0, "forks": 0,
                "open_issues": 0, "language": None, "languages": {}, "created_at": "", "updated_at": "",
                "pushed_at": None, "size_kb": 0, "license": None, "has_readme": False, "has_tests": False,
                "has_actions": False, "has_security": False, "topics": [], "default_branch": "main",
                "commits_90d": 0, "contributors": 0, "releases": 0,
            })
        ),
    )


@app.get("/assets/{asset_id}/ownership")
async def get_ownership(asset_id: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBOwnership
        result = await db.execute(select(DBOwnership).where(DBOwnership.asset_id == asset_id))
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Ownership record not found.")
        return {
            "asset_id": row.asset_id,
            "github_username": row.github_username,
            "repo_full_name": row.repo_full_name,
            "verified": row.verified,
            "verification_method": row.verification_method,
            "verified_at": row.verified_at.isoformat() if row.verified_at else None,
        }


# =============================================================================
# PHASE 2: EVIDENCE PACKET V2
# =============================================================================

async def _get_or_create_asset(username: str, repo_full_name: str, db) -> str:
    from app.database import DBAsset
    result = await db.execute(select(DBAsset).where(DBAsset.repo_full_name == repo_full_name))
    asset = result.scalar_one_or_none()
    if asset:
        return asset.id
    asset = DBAsset(
        id=str(uuid.uuid4()),
        github_username=username,
        repo_full_name=repo_full_name,
        source_type="github_repo",
        source_uri=f"https://github.com/{repo_full_name}",
        name=repo_full_name.split("/")[-1],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(asset)
    await db.flush()
    return asset.id


@app.get("/evidence/{asset_id}")
async def get_evidence_by_asset(asset_id: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBEvidencePacket
        result = await db.execute(
            select(DBEvidencePacket).where(DBEvidencePacket.asset_id == asset_id).order_by(desc(DBEvidencePacket.epoch))
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="No evidence packet found for this asset.")
        return row.raw_data


@app.get("/evidence/{asset_id}/packet.json")
async def download_packet_json(asset_id: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBEvidencePacket
        result = await db.execute(
            select(DBEvidencePacket).where(DBEvidencePacket.asset_id == asset_id).order_by(desc(DBEvidencePacket.epoch))
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="No evidence packet found.")
        return JSONResponse(
            content=row.raw_data,
            headers={"Content-Disposition": f"attachment; filename=launchr_packet_{asset_id}.json"},
        )


@app.post("/evidence/{asset_id}")
async def build_evidence_v2(asset_id: str):
    """Generate a canonical Evidence Packet V2 for an asset."""
    async with AsyncSessionLocal() as db:
        from app.database import DBAsset, DBOwnership, DBEvidencePacket
        asset_result = await db.execute(select(DBAsset).where(DBAsset.id == asset_id))
        asset = asset_result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found.")

        ownership_result = await db.execute(
            select(DBOwnership).where(DBOwnership.asset_id == asset_id)
        )
        ownership = ownership_result.scalar_one_or_none()
        ownership_verified = ownership.verified if ownership else False

    scanner = GitHubScanner()
    try:
        repos = await scanner.scan_user(asset.github_username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GitHub user not found or API error: {e}")
    finally:
        await scanner.close()

    target = next((r for r in repos if r.full_name == asset.repo_full_name), None)
    if not target:
        raise HTTPException(status_code=404, detail="Repository not found.")

    appraisal = appraisal_engine.appraise_repo(asset.github_username, target, repos)

    # Determine next epoch
    async with AsyncSessionLocal() as db:
        epoch_result = await db.execute(
            select(DBEvidencePacket).where(DBEvidencePacket.asset_id == asset_id).order_by(desc(DBEvidencePacket.epoch))
        )
        latest = epoch_result.scalar_one_or_none()
        next_epoch = (latest.epoch + 1) if latest else 1

    packet = evidence_builder_v2.build_packet(
        asset_id=asset_id,
        epoch=next_epoch,
        username=asset.github_username,
        repo=target,
        appraisal=appraisal,
        ownership_verified=ownership_verified,
    )

    async with AsyncSessionLocal() as db:
        db_pkt = DBEvidencePacket(
            id=packet.packet_id,
            asset_id=asset_id,
            epoch=packet.epoch,
            github_username=asset.github_username,
            repo_full_name=asset.repo_full_name,
            source_type=packet.source_type,
            source_uri=packet.source_uri,
            github_owner_verified=ownership_verified,
            repo_snapshot_hash=packet.repo_snapshot_hash,
            manifest_hash=packet.manifest_hash,
            appraisal_hash=packet.appraisal_hash,
            risk_report_hash=packet.risk_report_hash,
            packet_hash=packet.packet_hash,
            merkle_root=packet.merkle_root,
            launch_readiness_score=packet.launch_readiness_score,
            recommended_token_mode=packet.recommended_token_mode,
            do_not_mint_flags=packet.do_not_mint_flags,
            created_at=packet.created_at,
            disclaimer=packet.disclaimer,
            raw_data=packet.model_dump(mode="json"),
        )
        db.add(db_pkt)
        await db.commit()

    return packet.model_dump(mode="json")


@app.post("/evidence/{asset_id}/verify")
async def verify_evidence_packet(asset_id: str):
    """Recompute and verify the packet_hash of the latest evidence packet."""
    async with AsyncSessionLocal() as db:
        from app.database import DBEvidencePacket
        result = await db.execute(
            select(DBEvidencePacket).where(DBEvidencePacket.asset_id == asset_id).order_by(desc(DBEvidencePacket.epoch))
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="No evidence packet found.")

    raw = row.raw_data
    valid = verify_packet_hash(raw)
    return {
        "asset_id": asset_id,
        "packet_id": row.id,
        "packet_hash": raw.get("packet_hash"),
        "verified": valid,
        "message": "Packet hash matches canonical computation." if valid else "WARNING: Packet hash mismatch!",
    }


# =============================================================================
# PHASE 2: EPOCH TRACKING
# =============================================================================

@app.post("/evidence/{asset_id}/epoch")
async def create_epoch(asset_id: str, request: EpochCreateRequest):
    """Create a new evidence epoch for an asset (e.g., after repo improvements)."""
    if request.asset_id != asset_id:
        raise HTTPException(status_code=400, detail="asset_id mismatch.")

    async with AsyncSessionLocal() as db:
        from app.database import DBAsset, DBEvidencePacket, DBEpoch
        asset_result = await db.execute(select(DBAsset).where(DBAsset.id == asset_id))
        asset = asset_result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found.")

        # Find latest packet for score_before
        latest_result = await db.execute(
            select(DBEvidencePacket).where(DBEvidencePacket.asset_id == asset_id).order_by(desc(DBEvidencePacket.epoch))
        )
        latest = latest_result.scalar_one_or_none()
        score_before = latest.launch_readiness_score if latest else None

        # Build new evidence
        scanner = GitHubScanner()
        try:
            repos = await scanner.scan_user(asset.github_username)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"GitHub API error: {e}")
        finally:
            await scanner.close()

        target = next((r for r in repos if r.full_name == asset.repo_full_name), None)
        if not target:
            raise HTTPException(status_code=404, detail="Repository not found.")

        appraisal = appraisal_engine.appraise_repo(asset.github_username, target, repos)

        ownership_result = await db.execute(
            select(DBOwnership).where(DBOwnership.asset_id == asset_id)
        )
        ownership = ownership_result.scalar_one_or_none()
        ownership_verified = ownership.verified if ownership else False

        next_epoch = (latest.epoch + 1) if latest else 1
        packet = evidence_builder_v2.build_packet(
            asset_id=asset_id,
            epoch=next_epoch,
            username=asset.github_username,
            repo=target,
            appraisal=appraisal,
            ownership_verified=ownership_verified,
        )

        db_pkt = DBEvidencePacket(
            id=packet.packet_id,
            asset_id=asset_id,
            epoch=packet.epoch,
            github_username=asset.github_username,
            repo_full_name=asset.repo_full_name,
            source_type=packet.source_type,
            source_uri=packet.source_uri,
            github_owner_verified=ownership_verified,
            repo_snapshot_hash=packet.repo_snapshot_hash,
            manifest_hash=packet.manifest_hash,
            appraisal_hash=packet.appraisal_hash,
            risk_report_hash=packet.risk_report_hash,
            packet_hash=packet.packet_hash,
            merkle_root=packet.merkle_root,
            launch_readiness_score=packet.launch_readiness_score,
            recommended_token_mode=packet.recommended_token_mode,
            do_not_mint_flags=packet.do_not_mint_flags,
            created_at=packet.created_at,
            disclaimer=packet.disclaimer,
            raw_data=packet.model_dump(mode="json"),
        )
        db.add(db_pkt)
        await db.flush()

        epoch = DBEpoch(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            epoch=next_epoch,
            packet_id=packet.packet_id,
            trigger=request.trigger,
            score_before=score_before,
            score_after=packet.launch_readiness_score,
            notes=request.notes,
        )
        db.add(epoch)
        await db.commit()

        return {
            "epoch_id": epoch.id,
            "asset_id": asset_id,
            "epoch": next_epoch,
            "packet_id": packet.packet_id,
            "trigger": request.trigger,
            "score_before": score_before,
            "score_after": packet.launch_readiness_score,
            "notes": request.notes,
            "created_at": epoch.created_at.isoformat() if epoch.created_at else None,
        }


@app.get("/assets/{asset_id}/epochs")
async def list_epochs(asset_id: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBEpoch
        result = await db.execute(
            select(DBEpoch).where(DBEpoch.asset_id == asset_id).order_by(desc(DBEpoch.epoch))
        )
        rows = result.scalars().all()
    return {
        "epochs": [
            {
                "epoch_id": r.id,
                "epoch": r.epoch,
                "packet_id": r.packet_id,
                "trigger": r.trigger,
                "score_before": r.score_before,
                "score_after": r.score_after,
                "notes": r.notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


# =============================================================================
# PORTFOLIO LAYER
# =============================================================================

@app.get("/profile/{username}")
async def get_profile(username: str, sources: str = "github"):
    """Return Developer Capitalization with ecosystem families."""
    source_list = [s.strip().lower() for s in sources.split(",")]

    # GitHub scan
    repos = []
    if "github" in source_list:
        scanner = GitHubScanner()
        try:
            repos = await scanner.scan_user(username)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"GitHub user not found or API error: {e}")
        finally:
            await scanner.close()

    portfolio = await portfolio_engine.build_portfolio(username, repos)
    await portfolio_engine.persist_portfolio(portfolio)

    # Ecosystem detection
    dev_cap = ecosystem_engine.detect_ecosystems(username, repos, portfolio)

    result = dev_cap.model_dump(mode="json")

    # Hugging Face scan
    if "hf" in source_list or "huggingface" in source_list:
        hf_scanner = HuggingFaceScanner()
        try:
            hf_data = await hf_scanner.scan_user(username)
        except Exception:
            hf_data = None
        finally:
            await hf_scanner.close()

        if hf_data:
            result["hf_assets"] = hf_data
            result["combined_total_assets"] = portfolio.total_assets + hf_data["total_assets"]
            hf_value = hf_data["total_downloads"] * 0.01 + hf_data["total_likes"] * 1.0
            result["combined_estimated_value_low"] = round(
                portfolio.risk_adjusted_value_low_usd + hf_value * 0.5, 0
            )
            result["combined_estimated_value_high"] = round(
                portfolio.risk_adjusted_value_high_usd + hf_value * 2.0, 0
            )

    return result


@app.get("/portfolios")
async def list_portfolios():
    async with AsyncSessionLocal() as db:
        from app.database import DBPortfolio
        result = await db.execute(select(DBPortfolio).order_by(desc(DBPortfolio.created_at)))
        rows = result.scalars().all()
    return {
        "portfolios": [
            {
                "portfolio_id": r.id,
                "github_username": r.github_username,
                "total_assets": r.total_assets,
                "launchable_assets": r.launchable_assets,
                "gross_value": f"${int(r.gross_portfolio_value_low):,}–${int(r.gross_portfolio_value_high):,}",
                "risk_adjusted_value": f"${int(r.risk_adjusted_value_low):,}–${int(r.risk_adjusted_value_high):,}",
                "portfolio_confidence": r.portfolio_confidence,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@app.get("/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBPortfolio
        result = await db.execute(select(DBPortfolio).where(DBPortfolio.id == portfolio_id))
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Portfolio not found.")
        return row.raw_data


# =============================================================================
# PHASE 3: WALLET + TOKEN MINT + LLM
# =============================================================================

@app.post("/wallets")
async def register_wallet(request: WalletRegisterRequest):
    """Register a wallet address for a GitHub user."""
    wallet_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as db:
        from app.database import DBWallet
        wallet = DBWallet(
            id=wallet_id,
            github_username=request.github_username,
            wallet_address=request.wallet_address,
            chain=request.chain,
            verified=True,
            created_at=datetime.utcnow(),
        )
        db.add(wallet)
        await db.commit()
    return {
        "wallet_id": wallet_id,
        "github_username": request.github_username,
        "wallet_address": request.wallet_address,
        "chain": request.chain,
        "verified": True,
    }


@app.get("/wallets/{username}")
async def list_wallets(username: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBWallet
        result = await db.execute(
            select(DBWallet).where(DBWallet.github_username == username).order_by(desc(DBWallet.created_at))
        )
        rows = result.scalars().all()
    return {
        "wallets": [
            {
                "wallet_id": r.id,
                "wallet_address": r.wallet_address,
                "chain": r.chain,
                "verified": r.verified,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@app.post("/tokens/mint")
async def mint_proof_token(request: MintProofRequest):
    """Mint a non-transferable proof token for an asset (simulated for MVP)."""
    async with AsyncSessionLocal() as db:
        from app.database import DBAsset, DBEvidencePacket, DBTokenMint
        asset_result = await db.execute(select(DBAsset).where(DBAsset.id == request.asset_id))
        asset = asset_result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found.")

        evidence_result = await db.execute(
            select(DBEvidencePacket).where(DBEvidencePacket.asset_id == request.asset_id).order_by(desc(DBEvidencePacket.epoch))
        )
        evidence = evidence_result.scalar_one_or_none()
        if not evidence:
            raise HTTPException(status_code=400, detail="No evidence packet found. Build evidence first.")

        if evidence.do_not_mint_flags and len(evidence.do_not_mint_flags) > 0:
            raise HTTPException(status_code=403, detail="Asset has Do Not Mint flags. Cannot mint token.")

        mint_id = str(uuid.uuid4())
        simulated_mint_address = f"simulated_mint_{hashlib.sha256(mint_id.encode()).hexdigest()[:16]}"
        simulated_tx = f"simulated_tx_{hashlib.sha256((mint_id + 'tx').encode()).hexdigest()[:16]}"

        token_mint = DBTokenMint(
            id=mint_id,
            asset_id=request.asset_id,
            github_username=asset.github_username,
            wallet_address=request.wallet_address,
            token_type=request.token_type,
            token_mint_address=simulated_mint_address,
            evidence_packet_id=evidence.id,
            transfer_restricted=True,
            minted_at=datetime.utcnow(),
            tx_signature=simulated_tx,
            status="simulated",
            raw_data={
                "disclaimer": "This is a simulated mint for MVP. No real blockchain transaction occurred.",
                "evidence_packet_hash": evidence.packet_hash,
                "merkle_root": evidence.merkle_root,
            },
        )
        db.add(token_mint)
        await db.commit()

    return {
        "mint_id": mint_id,
        "asset_id": request.asset_id,
        "token_type": request.token_type,
        "token_mint_address": simulated_mint_address,
        "transfer_restricted": True,
        "status": "simulated",
        "tx_signature": simulated_tx,
        "message": "SIMULATED MINT: This is an MVP proof-of-concept. No real token was minted on-chain.",
        "disclaimer": "Appraisal is not market cap. Market cap is not cash. Liquidity is not guaranteed exit value.",
    }


@app.get("/tokens/{asset_id}")
async def list_token_mints(asset_id: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBTokenMint
        result = await db.execute(
            select(DBTokenMint).where(DBTokenMint.asset_id == asset_id).order_by(desc(DBTokenMint.minted_at))
        )
        rows = result.scalars().all()
    return {
        "mints": [
            {
                "mint_id": r.id,
                "token_type": r.token_type,
                "token_mint_address": r.token_mint_address,
                "transfer_restricted": r.transfer_restricted,
                "status": r.status,
                "tx_signature": r.tx_signature,
                "wallet_address": r.wallet_address,
                "minted_at": r.minted_at.isoformat() if r.minted_at else None,
            }
            for r in rows
        ]
    }


@app.post("/llm/generate")
async def generate_llm_usecase(request: LLMGenerateRequest):
    """Generate an LLM-powered use case for an asset."""
    async with AsyncSessionLocal() as db:
        from app.database import DBAsset, DBLLMUseCase
        asset_result = await db.execute(select(DBAsset).where(DBAsset.id == request.asset_id))
        asset = asset_result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found.")

        # Generate deterministic simulated output based on asset data
        use_case_id = str(uuid.uuid4())
        name = asset.name or "unnamed"
        stars = asset.stars or 0
        lang = asset.language or "unknown"

        if request.use_case_type == "readme_summary":
            output = (
                f"## {name}\n\n"
                f"This repository appears to be a {lang} project with {stars} stars. "
                f"It demonstrates moderate community interest. "
                f"The codebase likely contains core functionality suitable for package distribution. "
                f"Recommended next step: improve README clarity and add usage examples."
            )
            confidence = min(0.95, 0.5 + (stars / 10000))
        elif request.use_case_type == "code_quality":
            score = min(100, 50 + (stars / 100))
            output = (
                f"## Code Quality Assessment: {name}\n\n"
                f"- **Estimated Quality Score**: {score:.0f}/100\n"
                f"- **Community Signal**: {stars} stars indicates { 'strong' if stars > 1000 else 'moderate' if stars > 50 else 'early-stage' } engagement\n"
                f"- **Language**: {lang}\n"
                f"- **Recommendation**: Add comprehensive test coverage and CI/CD before launch."
            )
            confidence = min(0.9, 0.4 + (stars / 5000))
        elif request.use_case_type == "market_demand":
            demand = "high" if stars > 1000 else "moderate" if stars > 100 else "niche"
            output = (
                f"## Market Demand Analysis: {name}\n\n"
                f"- **Demand Level**: {demand}\n"
                f"- **Star Velocity Indicator**: {stars} total stars\n"
                f"- **Market Category**: Developer tooling / Open-source infrastructure\n"
                f"- **Launch Recommendation**: {'Strong candidate for restricted token launch' if stars > 500 else 'Build proof token first, gather more traction'}"
            )
            confidence = min(0.85, 0.45 + (stars / 8000))
        else:
            output = f"Unknown use case type: {request.use_case_type}"
            confidence = 0.0

        db_usecase = DBLLMUseCase(
            id=use_case_id,
            asset_id=request.asset_id,
            use_case_type=request.use_case_type,
            input_hash=hashlib.sha256(f"{request.asset_id}:{request.use_case_type}".encode()).hexdigest()[:16],
            output_text=output,
            model_used="simulated-llm" if not OPENAI_API_KEY else "gpt-4o-mini",
            confidence=round(confidence, 2),
            created_at=datetime.utcnow(),
        )
        db.add(db_usecase)
        await db.commit()

    return {
        "use_case_id": use_case_id,
        "asset_id": request.asset_id,
        "use_case_type": request.use_case_type,
        "output": output,
        "model_used": db_usecase.model_used,
        "confidence": round(confidence, 2),
        "disclaimer": "LLM output is simulated for MVP. Connect OPENAI_API_KEY for real inference.",
    }


@app.get("/llm/{asset_id}")
async def list_llm_usecases(asset_id: str):
    async with AsyncSessionLocal() as db:
        from app.database import DBLLMUseCase
        result = await db.execute(
            select(DBLLMUseCase).where(DBLLMUseCase.asset_id == asset_id).order_by(desc(DBLLMUseCase.created_at))
        )
        rows = result.scalars().all()
    return {
        "use_cases": [
            {
                "use_case_id": r.id,
                "use_case_type": r.use_case_type,
                "output_text": r.output_text,
                "model_used": r.model_used,
                "confidence": r.confidence,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


# =============================================================================
# PHASE 2.5 — Multi-source Software Asset Intelligence
# =============================================================================

@app.get("/registry/{username}", response_model=RegistryScanResult)
async def scan_registries(username: str):
    """Scan npm, PyPI, and Cargo registries for packages by a username."""
    scanner = RegistryScanner()
    packages = []
    registries_found = []
    try:
        npm = await scanner.scan_npm(username)
        if npm:
            packages.append(npm)
            registries_found.append("npm")
    except Exception:
        pass
    try:
        pypi = await scanner.scan_pypi(username)
        if pypi:
            packages.append(pypi)
            registries_found.append("pypi")
    except Exception:
        pass
    try:
        cargo = await scanner.scan_cargo(username)
        if cargo:
            packages.append(cargo)
            registries_found.append("cargo")
    except Exception:
        pass
    finally:
        await scanner.close()

    return RegistryScanResult(
        username=username,
        packages=[p.to_dict() for p in packages],
        total_packages=len(packages),
        total_downloads=sum(p.downloads for p in packages),
        registries_found=registries_found,
    )


@app.get("/deployments/{repo_full_name:path}", response_model=DeploymentScanResult)
async def scan_deployments(repo_full_name: str):
    """Detect public deployments for a repo (Vercel, Netlify, Fly, etc.)."""
    parts = repo_full_name.split("/")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="repo_full_name must be owner/repo")
    username, repo_name = parts
    scanner = DeploymentScanner()
    try:
        deployments = await scanner.probe_common_deployments(username, repo_name)
    except Exception:
        deployments = []
    finally:
        await scanner.close()

    return DeploymentScanResult(
        repo_full_name=repo_full_name,
        deployments=deployments,
        live_count=len(deployments),
    )


@app.get("/quality/{username}/{repo_name}", response_model=QualityScoreResult)
async def quality_score(username: str, repo_name: str):
    """Score a repo for README, license, security, docs, CI, tests."""
    full_name = f"{username}/{repo_name}"
    scanner = GitHubScanner()
    try:
        repos = await scanner.scan_user(username)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GitHub user not found: {e}")
    finally:
        await scanner.close()

    target = next((r for r in repos if r.full_name == full_name), None)
    if not target:
        raise HTTPException(status_code=404, detail="Repository not found.")

    scorer = QualityScorer()
    score = scorer.score_repo(target)
    return QualityScoreResult(
        repo_full_name=full_name,
        readme_score=score.readme_score,
        license_score=score.license_score,
        security_score=score.security_score,
        docs_score=score.docs_score,
        ci_score=score.ci_score,
        tests_score=score.tests_score,
        overall_quality=score.overall_quality,
    )


@app.get("/profile-v2/{username}", response_model=MultiSourceProfile)
async def multi_source_profile(username: str, sources: str = "github"):
    """Multi-source Software Asset Intelligence profile."""
    source_list = [s.strip().lower() for s in sources.split(",")]
    assets: List[MultiSourceAsset] = []
    total_downloads = 0
    total_stars = 0
    quality_summary = None

    # GitHub
    if "github" in source_list:
        scanner = GitHubScanner()
        try:
            repos = await scanner.scan_user(username)
        except Exception:
            repos = []
        finally:
            await scanner.close()

        scorer = QualityScorer()
        for r in repos:
            # Probe deployments
            dep_scanner = DeploymentScanner()
            try:
                deps = await dep_scanner.probe_common_deployments(username, r.name)
            except Exception:
                deps = []
            finally:
                await dep_scanner.close()

            q = scorer.score_repo(r)
            assets.append(MultiSourceAsset(
                source="github",
                name=r.name,
                full_name=r.full_name,
                url=f"https://github.com/{r.full_name}",
                stars_or_likes=r.stars,
                downloads=0,
                language=r.language,
                description=r.description,
                license=r.license,
                quality_score=q.overall_quality,
                deployments=[DeploymentInfo(url=d.url, platform=d.platform, status=d.status,
                                           detected_framework=d.detected_framework,
                                           response_time_ms=d.response_time_ms, has_ssl=d.has_ssl)
                            for d in deps],
            ))
            total_stars += r.stars

        if repos:
            top_repo = max(repos, key=lambda x: x.stars)
            quality_summary = QualityScoreResult(
                repo_full_name=top_repo.full_name,
                readme_score=scorer.score_repo(top_repo).readme_score,
                license_score=scorer.score_repo(top_repo).license_score,
                security_score=scorer.score_repo(top_repo).security_score,
                docs_score=scorer.score_repo(top_repo).docs_score,
                ci_score=scorer.score_repo(top_repo).ci_score,
                tests_score=scorer.score_repo(top_repo).tests_score,
                overall_quality=scorer.score_repo(top_repo).overall_quality,
            )

    # Hugging Face
    if "hf" in source_list or "huggingface" in source_list:
        hf_scanner = HuggingFaceScanner()
        try:
            hf = await hf_scanner.scan_user(username)
            for m in hf.models:
                assets.append(MultiSourceAsset(
                    source="hf",
                    name=m.name,
                    full_name=f"{username}/{m.name}",
                    url=f"https://huggingface.co/{username}/{m.name}",
                    stars_or_likes=m.likes,
                    downloads=m.downloads,
                    language=None,
                    description=m.description,
                    license=m.license,
                ))
                total_downloads += m.downloads
                total_stars += m.likes
            for d in hf.datasets:
                assets.append(MultiSourceAsset(
                    source="hf",
                    name=d.name,
                    full_name=f"{username}/{d.name}",
                    url=f"https://huggingface.co/datasets/{username}/{d.name}",
                    stars_or_likes=d.likes,
                    downloads=d.downloads,
                    language=None,
                    description=d.description,
                    license=d.license,
                ))
                total_downloads += d.downloads
                total_stars += d.likes
        except Exception:
            pass

    # Package registries
    if "registry" in source_list or "npm" in source_list or "pypi" in source_list or "cargo" in source_list:
        reg_scanner = RegistryScanner()
        try:
            for pkg in [await reg_scanner.scan_npm(username),
                        await reg_scanner.scan_pypi(username),
                        await reg_scanner.scan_cargo(username)]:
                if pkg:
                    assets.append(MultiSourceAsset(
                        source=pkg.registry,
                        name=pkg.name,
                        full_name=pkg.name,
                        url=pkg.homepage or pkg.repository_url or "",
                        stars_or_likes=0,
                        downloads=pkg.downloads,
                        language=None,
                        description=pkg.description,
                        license=pkg.license,
                    ))
                    total_downloads += pkg.downloads
        except Exception:
            pass
        finally:
            await reg_scanner.close()

    return MultiSourceProfile(
        username=username,
        sources_scanned=source_list,
        total_assets=len(assets),
        total_downloads=total_downloads,
        total_stars_or_likes=total_stars,
        assets=assets,
        quality_summary=quality_summary,
        token_launch_ready=False,
        gated_reason="Token launch gated. See REALITY_STATUS.md for compliance gates.",
    )


@app.get("/evidence/{asset_id}/export", response_model=EvidenceExport)
async def export_evidence(asset_id: str):
    """Export evidence packet as JSON with BitNet-compatible receipt hash."""
    async with AsyncSessionLocal() as db:
        from app.database import DBEvidencePacket, DBAsset
        result = await db.execute(
            select(DBEvidencePacket).where(DBEvidencePacket.asset_id == asset_id).order_by(desc(DBEvidencePacket.epoch))
        )
        packet = result.scalar_one_or_none()
        if not packet:
            raise HTTPException(status_code=404, detail="No evidence packet found for this asset.")

        asset_result = await db.execute(select(DBAsset).where(DBAsset.id == asset_id))
        asset = asset_result.scalar_one_or_none()

    # Compute BitNet-compatible receipt hash
    bitnet_payload = f"{asset_id}:{packet.epoch}:{packet.packet_hash}:{packet.created_at.isoformat()}"
    bitnet_receipt_hash = hashlib.sha256(bitnet_payload.encode()).hexdigest()

    export_id = str(uuid.uuid4())
    export_url = f"/evidence/{asset_id}/export/{export_id}.json"

    return EvidenceExport(
        packet_id=packet.id,
        asset_id=asset_id,
        github_username=asset.github_username if asset else "unknown",
        repo_full_name=asset.repo_full_name if asset else "unknown",
        export_format="json",
        exported_at=datetime.utcnow(),
        download_url=export_url,
        receipt_hash=packet.packet_hash,
        merkle_root=packet.merkle_root,
        bitnet_receipt_hash=bitnet_receipt_hash,
    )
