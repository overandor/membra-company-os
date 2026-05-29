from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TokenMode(str, Enum):
    RESTRICTED = "restricted"
    OPEN = "open"


class RepoSummary(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    stars: int
    forks: int
    open_issues: int
    language: Optional[str] = None
    languages: Dict[str, int] = {}
    created_at: str
    updated_at: str
    pushed_at: Optional[str] = None
    size_kb: int
    license: Optional[str] = None
    has_readme: bool = False
    has_tests: bool = False
    has_actions: bool = False
    has_security: bool = False
    topics: List[str] = []
    default_branch: str = "main"
    commits_90d: int = 0
    contributors: int = 0
    releases: int = 0


class DeveloperAssetMap(BaseModel):
    github_username: str
    scanned_at: datetime
    total_repos: int
    active_repos_90d: int
    core_projects_detected: int
    launchable_assets: int
    repo_quality_score: float = Field(ge=0, le=100)
    novelty_score: float = Field(ge=0, le=100)
    buildability_score: float = Field(ge=0, le=100)
    market_demand_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    token_launch_readiness: float = Field(ge=0, le=100)
    estimated_market_cap_range_usd: str
    recommended_launch_asset: Optional[str] = None
    repos: List[RepoSummary] = []
    metadata: Dict[str, Any] = {}


class RiskFlag(BaseModel):
    flag_type: str
    severity: RiskLevel
    description: str
    auto_block: bool = False


class EvidencePacket(BaseModel):
    packet_id: str
    github_username: str
    repo_full_name: str
    created_at: datetime
    username_proof: str
    repo_snapshot_hash: str
    commit_range: str
    license_scan: Dict[str, Any]
    dependency_scan: Dict[str, Any]
    readme_summary: str
    architecture_summary: str
    risk_flags: List[RiskFlag]
    appraisal_report: Dict[str, Any]
    launch_readiness_score: float
    do_not_mint_flags: List[str] = []
    signature: Optional[str] = None


class AppraisalResult(BaseModel):
    appraisal_id: str
    github_username: str
    repo_full_name: Optional[str] = None
    created_at: datetime
    raw_score: float
    risk_adjusted_score: float
    repo_activity: float
    code_quality: float
    documentation: float
    originality: float
    market_demand: float
    deployability: float
    traction: float
    risk_penalty: float
    suggested_initial_market_cap_usd: str
    recommended_token_mode: TokenMode
    risk_level: RiskLevel
    risk_flags: List[RiskFlag]


class Asset(BaseModel):
    asset_id: str
    github_username: str
    repo_full_name: str
    source_type: str = "github_repo"
    source_uri: str
    name: str
    description: Optional[str] = None
    stars: int = 0
    language: Optional[str] = None
    license: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    raw_repo_data: Optional[Dict[str, Any]] = None


class OwnershipStatus(BaseModel):
    asset_id: str
    github_username: str
    repo_full_name: str
    verified: bool = False
    verification_method: str = "none"
    verified_at: Optional[datetime] = None
    can_launch: bool = False


class EvidencePacketV2(BaseModel):
    packet_id: str
    asset_id: str
    epoch: int = 1
    github_username: str
    repo_full_name: str
    source_type: str = "github_repo"
    source_uri: str
    github_owner_verified: bool = False
    repo_snapshot_hash: str
    manifest_hash: str
    appraisal_hash: str
    risk_report_hash: str
    packet_hash: str
    merkle_root: str
    launch_readiness_score: float
    recommended_token_mode: str = "none"
    do_not_mint_flags: List[str] = []
    created_at: datetime
    disclaimer: str = "Appraisal is an estimate. Market cap is a signal, not guaranteed value."


class EpochRecord(BaseModel):
    epoch_id: str
    asset_id: str
    epoch: int
    packet_id: str
    trigger: str = "manual"
    score_before: Optional[float] = None
    score_after: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime


class LaunchConfig(BaseModel):
    github_username: str
    repo_full_name: str
    creator_allocation_pct: float = Field(default=20.0, ge=0, le=100)
    liquidity_pool_allocation_pct: float = Field(default=60.0, ge=0, le=100)
    treasury_allocation_pct: float = Field(default=10.0, ge=0, le=100)
    community_allocation_pct: float = Field(default=5.0, ge=0, le=100)
    reviewer_allocation_pct: float = Field(default=5.0, ge=0, le=100)
    locked_liquidity_pct: float = Field(default=80.0, ge=0, le=100)
    vesting_period_days: int = Field(default=365, ge=0)


class ScanRequest(BaseModel):
    github_username: str


class LaunchRequest(BaseModel):
    github_username: str
    repo_full_name: str
    wallet_address: Optional[str] = None


class OwnershipVerifyRequest(BaseModel):
    github_username: str
    repo_full_name: str
    github_token: Optional[str] = None
    verification_method: str = "token"


class EpochCreateRequest(BaseModel):
    asset_id: str
    trigger: str = "manual"
    notes: Optional[str] = None


class PortfolioAssetSummary(BaseModel):
    asset_id: str
    name: str
    repo_full_name: str
    stars: int
    launch_readiness_score: float
    recommended_token_mode: str
    do_not_mint: bool
    ownership_verified: bool
    latest_packet_id: Optional[str] = None


class PortfolioRiskSummary(BaseModel):
    total_flags: int
    auto_block_count: int
    high_severity_count: int
    medium_severity_count: int
    top_risks: List[str]


class Portfolio(BaseModel):
    portfolio_id: str
    github_username: str
    total_assets: int
    launchable_assets: int
    proof_ready_assets: int
    restricted_ready_assets: int
    do_not_mint_assets: int
    gross_portfolio_value_low_usd: float
    gross_portfolio_value_high_usd: float
    risk_adjusted_value_low_usd: float
    risk_adjusted_value_high_usd: float
    estimated_market_cap_range_usd: str
    portfolio_confidence: float
    top_5_assets: List[PortfolioAssetSummary]
    risk_summary: PortfolioRiskSummary
    created_at: datetime
    updated_at: datetime


class TokenMint(BaseModel):
    mint_id: str
    asset_id: str
    github_username: str
    wallet_address: str
    token_type: str = "proof"
    token_mint_address: Optional[str] = None
    evidence_packet_id: str
    transfer_restricted: bool = True
    minted_at: datetime
    tx_signature: Optional[str] = None
    status: str = "simulated"


class WalletConnect(BaseModel):
    wallet_id: str
    github_username: str
    wallet_address: str
    chain: str = "solana"
    verified: bool = False
    created_at: datetime


class LLMUseCase(BaseModel):
    use_case_id: str
    asset_id: str
    use_case_type: str
    output_text: str
    model_used: str = "gpt-4o-mini"
    confidence: Optional[float] = None
    created_at: datetime


class MintProofRequest(BaseModel):
    asset_id: str
    wallet_address: str
    token_type: str = "proof"


class WalletRegisterRequest(BaseModel):
    github_username: str
    wallet_address: str
    chain: str = "solana"


class LLMGenerateRequest(BaseModel):
    asset_id: str
    use_case_type: str  # readme_summary | code_quality | market_demand


class HFAssetSummary(BaseModel):
    asset_id: str
    name: str
    asset_type: str
    description: Optional[str] = None
    downloads: int = 0
    likes: int = 0
    tags: List[str] = []
    license: Optional[str] = None
    pipeline_tag: Optional[str] = None


class HFScanResult(BaseModel):
    username: str
    models: List[HFAssetSummary]
    datasets: List[HFAssetSummary]
    spaces: List[HFAssetSummary]
    total_models: int
    total_datasets: int
    total_spaces: int
    total_assets: int
    total_downloads: int
    total_likes: int


class PortfolioWithHF(BaseModel):
    github_portfolio: Portfolio
    hf_assets: Optional[HFScanResult] = None
    combined_total_assets: int = 0
    combined_estimated_value_low: float = 0.0
    combined_estimated_value_high: float = 0.0


class FamilyAsset(BaseModel):
    repo_full_name: str
    name: str
    stars: int
    language: Optional[str] = None
    launch_readiness_score: float
    recommended_token_mode: str
    do_not_mint: bool


class EcosystemFamily(BaseModel):
    family_id: str
    family_name: str
    repo_count: int
    total_stars: int
    languages: List[str]
    assets: List[FamilyAsset]
    flagship_asset: Optional[str] = None
    flagship_score: float = 0.0
    launch_candidate: bool = False
    risk_flags: List[str] = []


class CapitalBreakdown(BaseModel):
    technical_capital: float = Field(ge=0, le=100)
    innovation_capital: float = Field(ge=0, le=100)
    market_capital: float = Field(ge=0, le=100)
    evidence_capital: float = Field(ge=0, le=100)
    combined_score: float = Field(ge=0, le=100)


class DeveloperCapitalization(BaseModel):
    github_username: str
    portfolio: Portfolio
    ecosystems: List[EcosystemFamily]
    total_families: int
    core_products: int
    launch_candidates: int
    flagship_assets: int
    capital_breakdown: CapitalBreakdown
    top_opportunity: Optional[str] = None
    top_risk: Optional[str] = None
    hf_assets: Optional[HFScanResult] = None


class PackageInfo(BaseModel):
    name: str
    registry: str
    version: str
    downloads: int = 0
    dependents: int = 0
    license: Optional[str] = None
    description: str = ""
    repository_url: Optional[str] = None
    homepage: Optional[str] = None
    author: Optional[str] = None
    keywords: List[str] = []
    last_published: Optional[str] = None
    maintainers: int = 0


class RegistryScanResult(BaseModel):
    username: str
    packages: List[PackageInfo]
    total_packages: int
    total_downloads: int
    registries_found: List[str]


class DeploymentInfo(BaseModel):
    url: str
    platform: str
    status: str
    detected_framework: Optional[str] = None
    response_time_ms: Optional[float] = None
    has_ssl: bool = False


class DeploymentScanResult(BaseModel):
    repo_full_name: str
    deployments: List[DeploymentInfo]
    live_count: int


class QualityScoreResult(BaseModel):
    repo_full_name: str
    readme_score: float
    license_score: float
    security_score: float
    docs_score: float
    ci_score: float
    tests_score: float
    overall_quality: float


class MultiSourceAsset(BaseModel):
    source: str  # github, hf, npm, pypi, cargo
    name: str
    full_name: str
    url: str
    stars_or_likes: int = 0
    downloads: int = 0
    language: Optional[str] = None
    description: Optional[str] = None
    license: Optional[str] = None
    quality_score: Optional[float] = None
    deployments: List[DeploymentInfo] = []


class MultiSourceProfile(BaseModel):
    username: str
    sources_scanned: List[str]
    total_assets: int
    total_downloads: int
    total_stars_or_likes: int
    assets: List[MultiSourceAsset]
    quality_summary: Optional[QualityScoreResult] = None
    token_launch_ready: bool = False
    gated_reason: str = "Token launch gated. See REALITY_STATUS.md for compliance gates."


class EvidenceExport(BaseModel):
    packet_id: str
    asset_id: str
    github_username: str
    repo_full_name: str
    export_format: str = "json"
    exported_at: datetime
    download_url: str
    receipt_hash: str
    merkle_root: str
    bitnet_receipt_hash: str
