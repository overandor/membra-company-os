import {
  HealthResponse,
  ReadyResponse,
  DashboardResponse,
  Photo,
  InventoryItem,
  ListingDraft,
  PublicListing,
  KPICard,
  KPIUpload,
  ProofbookEntry,
  WalletEvent,
  PayoutEligibility,
  OutboxEvent,
} from '../types/membra_kpi';

const BASE_URL = 'http://localhost:8000';

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

export const membraApi = {
  // Health & Status
  health: () => fetchJSON<HealthResponse>('/api/health'),
  ready: () => fetchJSON<ReadyResponse>('/api/ready'),
  dashboard: () => fetchJSON<DashboardResponse>('/api/dashboard'),

  // Photos & Inventory
  photos: () => fetchJSON<{ photos: Photo[] }>('/api/photos'),
  inventory: () => fetchJSON<{ inventory: InventoryItem[] }>('/api/inventory'),
  skuMap: () => fetchJSON<{ sku_map: any[] }>('/api/sku-map'),

  // Listings
  publicListings: () => fetchJSON<{ public_listings: PublicListing[] }>('/api/listings/public'),
  listingDrafts: () => fetchJSON<{ drafts: ListingDraft[] }>('/api/listings/drafts'),
  requestVisibility: (listingId: string) =>
    fetchJSON<any>(`/api/listings/${listingId}/request-visibility`, { method: 'POST' }),
  confirmVisibility: (listingId: string) =>
    fetchJSON<any>(`/api/listings/${listingId}/confirm-visibility`, { method: 'POST' }),

  // KPIs
  kpis: () => fetchJSON<{ kpis: KPICard[]; uploads: KPIUpload[] }>('/api/kpis'),

  // Wallet & Payouts
  walletEvents: () => fetchJSON<{ wallet_events: WalletEvent[] }>('/api/wallet-events'),
  createWalletEvent: (payload: { user_id: string; subject_type: string; subject_id: string; amount_usd: number; event_type: string; status?: string; metadata?: any }) =>
    fetchJSON<{ success: boolean; wallet_event: WalletEvent }>('/api/wallet-events', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  payoutEligibility: () => fetchJSON<{ payout_eligibility: PayoutEligibility[] }>('/api/payout-eligibility'),
  createPayoutEligibility: (payload: { user_id: string; subject_type: string; subject_id: string; eligible_amount_usd: number; eligibility_reason?: string }) =>
    fetchJSON<{ success: boolean; payout_eligibility: PayoutEligibility }>('/api/payout-eligibility', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Proofbook
  proofbook: () => fetchJSON<{ proofbook: ProofbookEntry[]; chain: any }>('/api/proofbook'),

  // Events Outbox
  outboxEvents: (status?: string, limit?: number) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (limit) params.append('limit', String(limit));
    return fetchJSON<{ events: OutboxEvent[] }>(`/api/events/outbox?${params.toString()}`);
  },
  outboxStats: () => fetchJSON<{ event_outbox: any }>('/api/events/outbox/stats'),

  // Uploads
  analyzePhoto: async (formData: FormData) => {
    const res = await fetch(`${BASE_URL}/api/photo/analyze`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    return res.json();
  },
  uploadKPI: async (formData: FormData) => {
    const res = await fetch(`${BASE_URL}/api/kpi/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    return res.json();
  },
};
