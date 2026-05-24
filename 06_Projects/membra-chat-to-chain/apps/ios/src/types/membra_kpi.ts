export interface HealthResponse {
  ok: boolean;
  app: string;
  version: string;
  env: string;
  product_router_mounted: boolean;
  event_outbox: boolean;
}

export interface ReadyResponse {
  ok: boolean;
  counts: DashboardCounts;
  event_outbox: EventOutboxStats;
  deep_backend: any;
  solana_devnet: any;
  warnings: string[];
}

export interface DashboardCounts {
  photos: number;
  inventory: number;
  drafts: number;
  public_listings: number;
  kpis: number;
  proofs: number;
  event_outbox_pending: number;
  event_outbox_failed: number;
  event_outbox_delivered: number;
  event_outbox_dead_letter: number;
}

export interface DashboardResponse {
  counts: DashboardCounts;
}

export interface EventOutboxStats {
  pending: number;
  delivered: number;
  failed: number;
  dead_letter: number;
}

export interface Photo {
  photo_id: string;
  owner_id: string;
  filename: string;
  file_path: string;
  content_type: string;
  width: number;
  height: number;
  room_type: string;
  monetization_goal: string;
  user_notes: string;
  location_hint: string;
  room_summary: string;
  status: string;
  created_at: string;
}

export interface InventoryItem {
  inventory_item_id: string;
  source_photo_id: string;
  owner_id: string;
  sku: string;
  detected_name: string;
  asset_type: string;
  visual_evidence: string;
  monetization_type: string;
  listing_type: string;
  description: string;
  suggested_price_low: number;
  suggested_price_high: number;
  pricing_unit: string;
  confidence: number;
  kpi_score: number;
  proof_required_json: string;
  risk_flags_json: string;
  recommended_action: string;
  status: string;
  created_at: string;
}

export interface ListingDraft {
  listing_id: string;
  inventory_item_id: string;
  sku: string;
  title: string;
  description: string;
  listing_type: string;
  suggested_price_low: number;
  suggested_price_high: number;
  pricing_unit: string;
  status: string;
  owner_visibility_requested_at: string | null;
  owner_confirmed_at: string | null;
  created_at: string;
}

export interface PublicListing {
  public_listing_id: string;
  listing_id: string;
  sku: string;
  title: string;
  description: string;
  price_low: number;
  price_high: number;
  pricing_unit: string;
  visibility_status: string;
  created_at: string;
}

export interface KPICard {
  kpi_id: string;
  source_photo_id: string | null;
  inventory_item_id: string | null;
  title: string;
  value: string;
  score: number;
  category: string;
  explanation: string;
  created_at: string;
}

export interface KPIUpload {
  upload_id: string;
  filename: string;
  row_count: number;
  column_count: number;
  summary_json: string;
  suggested_kpis_json: string;
  created_at: string;
}

export interface ProofbookEntry {
  proof_id: string;
  subject_type: string;
  subject_id: string;
  event_type: string;
  proof_hash: string;
  metadata_json: string;
  created_at: string;
}

export interface WalletEvent {
  ledger_event_id: string;
  user_id: string;
  subject_type: string;
  subject_id: string;
  amount_usd: number;
  event_type: string;
  status: string;
  metadata_json: string;
  created_at: string;
}

export interface PayoutEligibility {
  payout_event_id: string;
  user_id: string;
  subject_type: string;
  subject_id: string;
  eligible_amount_usd: number;
  eligibility_reason: string;
  status: string;
  created_at: string;
}

export interface OutboxEvent {
  event_id: string;
  event_type: string;
  subject_type: string;
  subject_id: string;
  owner_id: string;
  payload_json: string;
  status: string;
  created_at: string;
}
