import { API_ENDPOINTS } from '@/constants/Api';
import { useAuthStore } from '@/stores/authStore';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: Record<string, unknown> | FormData;
  headers?: Record<string, string>;
}

async function request<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const { token } = useAuthStore.getState();
  const isFormData = options.body instanceof FormData;

  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(url, {
    method: options.method || 'GET',
    headers,
    body: isFormData ? (options.body as FormData) : options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: `HTTP ${response.status}` }));
    throw new Error(error.message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  health: () => request<{ ok: boolean; app: string }>(API_ENDPOINTS.health),

  owners: {
    create: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.owners, { method: 'POST', body: data }),
    profile: () => request(API_ENDPOINTS.profile),
  },

  assets: {
    create: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.assets, { method: 'POST', body: data }),
    createWindow: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.windows, { method: 'POST', body: data }),
    createVehicle: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.vehicles, { method: 'POST', body: data }),
    createWearable: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.wearables, { method: 'POST', body: data }),
  },

  campaigns: {
    available: () => request<{ campaigns: unknown[] }>(API_ENDPOINTS.campaigns.available),
    accept: (id: string) => request(API_ENDPOINTS.campaigns.accept(id), { method: 'POST' }),
    decline: (id: string) => request(API_ENDPOINTS.campaigns.decline(id), { method: 'POST' }),
  },

  mediaKits: {
    confirmReceipt: (id: string) =>
      request(API_ENDPOINTS.mediaKits.confirmReceipt(id), { method: 'POST' }),
  },

  proof: {
    submitPhoto: (formData: FormData) =>
      request(API_ENDPOINTS.proof.photo, { method: 'POST', body: formData }),
    submitLocation: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.proof.location, { method: 'POST', body: data }),
    qrScan: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.proof.qrScan, { method: 'POST', body: data }),
    nfcTap: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.proof.nfcTap, { method: 'POST', body: data }),
  },

  wallet: {
    rewardStatus: () => request(API_ENDPOINTS.wallet.rewardStatus),
    payoutHistory: () => request(API_ENDPOINTS.wallet.payoutHistory),
  },

  claims: {
    create: (data: Record<string, unknown>) =>
      request(API_ENDPOINTS.claims.create, { method: 'POST', body: data }),
    get: (id: string) => request(API_ENDPOINTS.claims.get(id)),
  },
};
