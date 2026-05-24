const API_BASE_URL = process.env.EXPO_PUBLIC_MEMBRA_API_URL || 'https://api.membra.labs/v1';

export const API_ENDPOINTS = {
  base: API_BASE_URL,
  health: `${API_BASE_URL}/health`,
  owners: `${API_BASE_URL}/owners`,
  profile: `${API_BASE_URL}/owners/profile`,
  assets: `${API_BASE_URL}/ad-assets`,
  windows: `${API_BASE_URL}/windows`,
  vehicles: `${API_BASE_URL}/vehicles`,
  wearables: `${API_BASE_URL}/wearables`,
  campaigns: {
    available: `${API_BASE_URL}/campaigns/available`,
    accept: (id: string) => `${API_BASE_URL}/campaigns/${id}/accept`,
    decline: (id: string) => `${API_BASE_URL}/campaigns/${id}/decline`,
  },
  mediaKits: {
    confirmReceipt: (id: string) => `${API_BASE_URL}/media-kits/${id}/confirm-receipt`,
  },
  proof: {
    photo: `${API_BASE_URL}/proof/photo`,
    location: `${API_BASE_URL}/proof/location`,
    qrScan: `${API_BASE_URL}/proof/qr-scan`,
    nfcTap: `${API_BASE_URL}/proof/nfc-tap`,
  },
  wallet: {
    rewardStatus: `${API_BASE_URL}/wallet/reward-status`,
    payoutHistory: `${API_BASE_URL}/wallet/payout-history`,
  },
  claims: {
    create: `${API_BASE_URL}/claims`,
    get: (id: string) => `${API_BASE_URL}/claims/${id}`,
  },
} as const;

export const STORAGE_KEYS = {
  authToken: 'membra_auth_token',
  refreshToken: 'membra_refresh_token',
  ownerProfile: 'membra_owner_profile',
  lastSync: 'membra_last_sync',
} as const;
