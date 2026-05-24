export interface User {
  user_id: string;
  email: string;
  name: string;
  phone: string;
  user_type: 'host' | 'guest';
  verified: boolean;
  created_at: string;
}

export interface Asset {
  asset_id: string;
  host_id: string;
  title: string;
  description: string;
  category: string;
  address: string;
  latitude: number;
  longitude: number;
  price_cents: number;
  deposit_cents: number;
  insurable: boolean;
  status: string;
}

export interface Reservation {
  visit_id: string;
  guest_id: string;
  asset_id: string;
  status: string;
  created_at: string;
  risk_score?: number;
  risk_approved?: boolean;
}

export interface Payment {
  payment_id: string;
  visit_id: string;
  amount_cents: number;
  status: string;
  provider: string;
  created_at: string;
}

export interface InsuranceCoverage {
  coverage_id: string;
  visit_id: string;
  status: string;
  coverage_limit_cents: number;
  premium_cents: number;
}

export interface AdCampaign {
  campaign_id: string;
  owner_id: string;
  name: string;
  budget_cents: number;
  status: string;
  target_city?: string;
}

export interface AdAnalytics {
  campaign_id: string;
  impressions: number;
  scans: number;
  ctr: number;
  total_payout_cents: number;
}

export interface WearAnalytics {
  campaign_id: string;
  impressions: number;
  verified_proofs: number;
  total_payout_cents: number;
}

export interface HealthStatus {
  status: string;
  service: string;
}

export interface KPIData {
  totalUsers: number;
  totalHosts: number;
  totalGuests: number;
  totalAssets: number;
  totalReservations: number;
  totalRevenueCents: number;
  activeCampaigns: number;
  totalScans: number;
  avgRiskScore: number;
  pendingClaims: number;
}
