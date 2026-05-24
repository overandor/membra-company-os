export const TIME_CAPITAL_BANDS = {
  protected_floor: { rate_per_sec: 0.07, label: "Protected Floor" },
  builder_operator: { rate_per_sec: 0.14, label: "Builder / Operator" },
  ip_creation: { rate_per_sec: 0.28, label: "IP Creation" },
  commercialization: { rate_per_sec: 0.42, label: "Commercialization-Facing Work" },
} as const;

export const APPRAISAL_DISCLAIMER =
  "Model opinion only; not payment. Appraisal is a directional signal, not a cash valuation.";

export const DOCTRINE = {
  proof_is_not_money: true,
  token_is_not_profit: true,
  testnet_is_not_settlement: true,
  mint_address_means_token_exists: true,
  stripe_settlement_is_official_money: true,
} as const;

export const HARD_BOUNDARIES = [
  "LLM appraisal is not money.",
  "Proof is not payment.",
  "Manifest is not token.",
  "Token is not guaranteed profit.",
  "Support payment is not investment.",
  "Rebate is not yield.",
  "Receipt is not equity.",
  "QR is not blind execution.",
  "Wallet is not a funding source.",
  "Mainnet mint is not legal clearance.",
] as const;

export const SECRET_PATTERNS = [
  /-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----/,
  /[0-9a-fA-F]{64}/,
  /(?:seed\s*phrase|mnemonic|secret\s*key|private\s*key)/i,
  /\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b/,
  /\b0x[a-fA-F0-9]{64}\b/,
];

export const PII_PATTERNS = [
  /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/,
  /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/,
  /\b\d{3}[-.]?\d{2}[-.]?\d{4}\b/,
];

export const BLOCKED_PHRASES = [
  "guaranteed profit",
  "guaranteed return",
  "risk-free",
  "risk free",
  "guaranteed yield",
  "automatic payout",
  "official certification",
  "guaranteed equity",
];

export const CHAT_PIPELINE_STAGES = [
  { id: "chat_captured", label: "CHAT CAPTURED" },
  { id: "plan_generated", label: "PLAN GENERATED" },
  { id: "terminal_opened", label: "TERMINAL WORKSPACE OPENED" },
  { id: "files_written", label: "FILES WRITTEN" },
  { id: "tests_run", label: "TESTS RUN" },
  { id: "artifacts_hashed", label: "ARTIFACTS HASHED" },
  { id: "github_anchored", label: "GITHUB ANCHORED" },
  { id: "devnet_deployed", label: "DEVNET DEPLOYED" },
  { id: "qr_campaign", label: "QR CAMPAIGN CREATED" },
  { id: "chain_receipt", label: "CHAIN RECEIPT RECORDED" },
  { id: "mainnet_prepared", label: "MAINNET PAYLOAD PREPARED" },
  { id: "approval_required", label: "APPROVAL REQUIRED" },
  { id: "signed", label: "SIGNED BY USER OR MULTISIG" },
  { id: "mainnet_executed", label: "MAINNET EXECUTED" },
] as const;

export const MEMBRA_STAGES = [
  { id: "draft_manifest", label: "Draft Manifest" },
  { id: "metadata_prepared", label: "Metadata Prepared" },
  { id: "legal_review", label: "Legal Review" },
  { id: "testnet_dry_run", label: "Testnet Dry Run" },
  { id: "mainnet_mint", label: "Mainnet Mint Created" },
  { id: "authority_policy", label: "Authority Policy Set" },
  { id: "proof_capsule", label: "Public Proof Capsule" },
  { id: "liquidity_decision", label: "Liquidity Decision" },
  { id: "support_economy", label: "Support Economy Active" },
  { id: "external_settlement", label: "External Settlement Recorded" },
] as const;

export const COLORS = {
  bg: "#050505",
  panel: "#0B0D10",
  panel2: "#111318",
  orange: "#FF8A1F",
  gold: "#D6A64F",
  bronze: "#9A6A35",
  text: "#F7F2E8",
  muted: "#9B9489",
  success: "#49D17D",
  danger: "#D84A32",
} as const;
