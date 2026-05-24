import { useCallback } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/services/apiClient';
import type { Owner } from '@/types';

export function useAuth() {
  const { owner, token, isAuthenticated, isLoading, setOwner, setToken, setLoading, logout } = useAuthStore();

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await apiClient.owners.create({ email, password });
      const data = response as { token: string; owner: Owner };
      setToken(data.token);
      setOwner(data.owner);
      return { success: true };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Login failed' };
    } finally {
      setLoading(false);
    }
  }, [setOwner, setToken, setLoading]);

  const checkAuth = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const profile = await apiClient.owners.profile() as { owner: Owner };
      setOwner(profile.owner);
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  }, [token, setOwner, setLoading, logout]);

  return {
    owner,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuth,
  };
}
