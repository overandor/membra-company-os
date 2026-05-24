export interface Owner {
  id: string;
  email: string;
  wallet_address?: string;
  display_name?: string;
  phone?: string;
  created_at: string;
  is_active: boolean;
}

export type AssetType = 'vehicle' | 'window' | 'wearable' | 'bag' | 'sign' | 'surface';

export interface Asset {
  id: string;
  owner_id: string;
  type: AssetType;
  name: string;
  description?: string;
  location?: GeoLocation;
  photos: string[];
  status: 'pending' | 'active' | 'inactive' | 'rejected';
  created_at: string;
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
  address?: string;
}

export interface Campaign {
  id: string;
  title: string;
  description: string;
  brand_name: string;
  reward_amount: number;
  reward_currency: string;
  requirements: string[];
  asset_types: AssetType[];
  start_date: string;
  end_date: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
}

export interface CampaignOffer {
  campaign: Campaign;
  accepted_at?: string;
  status: 'offered' | 'accepted' | 'declined' | 'completed';
}

export interface MediaKit {
  id: string;
  campaign_id: string;
  owner_id: string;
  items: MediaKitItem[];
  shipped_at?: string;
  delivered_at?: string;
  confirmed_at?: string;
  status: 'preparing' | 'shipped' | 'delivered' | 'confirmed';
}

export interface MediaKitItem {
  name: string;
  quantity: number;
  description?: string;
}

export interface ProofSubmission {
  id: string;
  owner_id: string;
  campaign_id: string;
  asset_id: string;
  photo_url: string;
  location?: GeoLocation;
  submitted_at: string;
  status: 'pending' | 'under_review' | 'approved' | 'rejected';
  review_notes?: string;
}

export interface QRScanEvent {
  id: string;
  owner_id: string;
  scan_type: 'qr' | 'nfc';
  payload: string;
  location?: GeoLocation;
  scanned_at: string;
  verified: boolean;
}

export interface RewardStatus {
  total_earned: number;
  total_paid: number;
  pending_amount: number;
  currency: string;
  next_payout_date?: string;
  transactions: RewardTransaction[];
}

export interface RewardTransaction {
  id: string;
  amount: number;
  currency: string;
  type: 'campaign_reward' | 'bonus' | 'referral';
  status: 'pending' | 'processing' | 'completed';
  created_at: string;
  campaign_name?: string;
}

export interface Claim {
  id: string;
  owner_id: string;
  type: 'payment_missing' | 'proof_rejected' | 'campaign_issue' | 'support';
  subject_id?: string;
  description: string;
  status: 'open' | 'under_review' | 'resolved' | 'closed';
  created_at: string;
  resolved_at?: string;
}

export interface WalletReadiness {
  wallet_address: string;
  is_connected: boolean;
  is_verified: boolean;
  preferred_payout_method?: 'crypto' | 'bank_transfer' | 'paypal';
  minimum_payout_threshold: number;
  current_balance: number;
}

export interface MobileEvent {
  event_id: string;
  owner_email: string;
  action_type: string;
  subject_type: string;
  subject_id: string;
  evidence_url: string;
  notes: string;
  metadata: Record<string, unknown>;
  event_hash: string;
  status: string;
  created_at: string;
}
