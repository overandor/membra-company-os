import {
  User,
  Asset,
  Reservation,
  Payment,
  InsuranceCoverage,
  AdCampaign,
  AdAnalytics,
  WearAnalytics,
  HealthStatus,
  KPIData,
} from '../types';

const BASE_URL = 'http://localhost:8000/v1';

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

export const api = {
  health: () => fetchJSON<HealthStatus>('/health'),

  users: (type?: 'host' | 'guest') => fetchJSON<User[]>(`/users${type ? `?user_type=${type}` : ''}`),

  assets: (category?: string) => fetchJSON<Asset[]>(`/assets${category ? `?category=${category}` : ''}`),

  reservations: () => fetchJSON<Reservation[]>('/reservations'),
  reservation: (id: string) => fetchJSON<Reservation>(`/reservations/${id}`),

  payments: () => fetchJSON<Payment[]>('/payments'),

  campaigns: () => fetchJSON<AdCampaign[]>('/ad-campaigns'),
  campaignAnalytics: (id: string) => fetchJSON<AdAnalytics>(`/ad-analytics/campaign/${id}`),

  wearAnalytics: (campaignId: string) => fetchJSON<WearAnalytics>(`/wear-analytics/campaign/${campaignId}`),

  async aggregateKPIs(): Promise<KPIData> {
    const [users, assets, reservations, campaigns] = await Promise.all([
      this.users(),
      this.assets(),
      this.reservations(),
      this.campaigns(),
    ]);

    const hosts = users.filter((u: User) => u.user_type === 'host');
    const guests = users.filter((u: User) => u.user_type === 'guest');

    // Note: The demo backend doesn't have a direct /payments endpoint;
    // we estimate revenue from reservation price via assets.
    const totalRevenueCents = reservations.reduce((sum: number, r: Reservation) => {
      const asset = assets.find((a: Asset) => a.asset_id === r.asset_id);
      return sum + (asset ? asset.price_cents : 0);
    }, 0);

    const activeCampaigns = campaigns.filter(
      (c: AdCampaign) => c.status === 'launched' || c.status === 'funded'
    ).length;

    // Scan count would come from ad-analytics; default to 0 if unavailable
    let totalScans = 0;
    try {
      for (const c of campaigns.slice(0, 3)) {
        const a = await this.campaignAnalytics(c.campaign_id);
        totalScans += a.scans || 0;
      }
    } catch {
      // ignore
    }

    const avgRiskScore =
      reservations.length > 0
        ? reservations.reduce((sum: number, r: Reservation) => sum + (r.risk_score || 0), 0) / reservations.length
        : 0;

    return {
      totalUsers: users.length,
      totalHosts: hosts.length,
      totalGuests: guests.length,
      totalAssets: assets.length,
      totalReservations: reservations.length,
      totalRevenueCents,
      activeCampaigns,
      totalScans,
      avgRiskScore: Math.round(avgRiskScore * 100) / 100,
      pendingClaims: 0,
    };
  },
};
