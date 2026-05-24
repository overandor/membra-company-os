import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Owner, WalletReadiness } from '@/types';

interface AuthState {
  owner: Owner | null;
  wallet: WalletReadiness | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setOwner: (owner: Owner | null) => void;
  setWallet: (wallet: WalletReadiness | null) => void;
  setToken: (token: string | null) => void;
  setAuthenticated: (value: boolean) => void;
  setLoading: (value: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      owner: null,
      wallet: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      setOwner: (owner) => set({ owner }),
      setWallet: (wallet) => set({ wallet }),
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      setAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
      setLoading: (isLoading) => set({ isLoading }),
      logout: () => set({ owner: null, wallet: null, token: null, isAuthenticated: false }),
    }),
    {
      name: 'membra-auth-storage',
      storage: createJSONStorage(() => ({
        getItem: async (name) => {
          try {
            const { getItemAsync } = await import('expo-secure-store');
            return await getItemAsync(name);
          } catch {
            return null;
          }
        },
        setItem: async (name, value) => {
          try {
            const { setItemAsync } = await import('expo-secure-store');
            await setItemAsync(name, value);
          } catch {}
        },
        removeItem: async (name) => {
          try {
            const { deleteItemAsync } = await import('expo-secure-store');
            await deleteItemAsync(name);
          } catch {}
        },
      })),
    }
  )
);
