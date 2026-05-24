export interface ArtifactSchema {
  artifact_id: string;
  creator_wallet: string;
  creator_handle?: string;
  session_id: string;
  artifact_type: ArtifactType;
  title: string;
  summary: string;
  raw_content_hash_sha256: string;
  redacted_content_hash_sha256: string;
  proof_hash: string;
  license_scope: LicenseScope;
  privacy_status: PrivacyStatus;
  llm_appraisal_usd: number;
  appraisal_method: string;
  evidence_grade: number;
  github_commit?: string;
  github_path?: string;
  ipfs_cid?: string;
  solana_devnet_tx?: string;
  solana_receipt_pda?: string;
  payment_status: PaymentStatus;
  funding_source: FundingSource;
  created_at: string;
  updated_at: string;
}

export type ArtifactType =
  | "prompt_response_pair"
  | "build_epoch"
  | "fieldwork"
  | "ui_asset"
  | "code"
  | "invention_disclosure"
  | "memory"
  | "support_receipt";

export type LicenseScope =
  | "private"
  | "public"
  | "commercial"
  | "research"
  | "revocable";

export type PrivacyStatus =
  | "private"
  | "redacted"
  | "approved_public";

export type PaymentStatus =
  | "unfunded"
  | "funded"
  | "payable"
  | "paid"
  | "failed";

export type FundingSource =
  | "none"
  | "buyer"
  | "sponsor"
  | "donor"
  | "grant"
  | "bounty"
  | "license"
  | "escrow"
  | "treasury";

export interface AppraisalScores {
  originality_score_0_100: number;
  usefulness_score_0_100: number;
  implementation_score_0_100: number;
  provenance_strength_0_100: number;
  commercial_proximity_0_100: number;
  privacy_risk_0_100: number;
  duplicate_penalty_0_100: number;
}

export interface AppraisalResult extends AppraisalScores {
  base_score: number;
  total_score: number;
  llm_appraisal_usd: number;
  time_capital_band: TimeCapitalBand;
  disclaimer: string;
}

export type TimeCapitalBand =
  | "protected_floor"
  | "builder_operator"
  | "ip_creation"
  | "commercialization";

export interface SessionData {
  session_id: string;
  creator_wallet: string;
  started_at: string;
  status: "active" | "completed" | "abandoned";
}

export interface QRPayload {
  protocol: "MEMBRA-QR-0.1";
  cluster: "devnet" | "mainnet";
  action: "OPEN_ARTIFACT_SUPPORT_PAGE";
  artifact_id: string;
  program_id: string;
  artifact_pda: string;
  creator_public_wallet: string;
  terms_uri: string;
  terms_hash: string;
  proof_hash: string;
  execution_requires_user_signature: true;
  not_profit_guarantee: true;
  not_investment: true;
}

export interface PolicyResult {
  allowed: boolean;
  reason?: string;
  risk_flags: string[];
  requires_manual_approval: boolean;
  requires_legal_review: boolean;
  block_reasons: string[];
}

export interface MainnetPaymentPayload {
  artifact_id: string;
  payer_wallet: string;
  recipient_wallet: string;
  amount: number;
  token: "SOL" | "USDC";
  funding_source: FundingSource;
  approval_context: string;
}

export interface MainnetPaymentPreparation {
  serialized_transaction?: string;
  transaction_description: string;
  policy_result: PolicyResult;
  risk_flags: string[];
  requires_manual_signature: true;
}

export interface ChatPipelineStage {
  id: string;
  label: string;
  status: "completed" | "active" | "pending";
  detail: string;
}

export interface MEMBRATokenState {
  stage: string;
  status: "completed" | "active" | "pending";
  detail: string;
}
