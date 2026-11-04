import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { onSessionExpired, refreshAccessToken } from '@/services/api';
import * as authService from '@/services/authService';
import { tokenStore } from '@/services/tokenStore';
import type { CurrentUser } from '@/types/auth';

import { AuthContext, type AuthStatus } from './authContextValue';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<CurrentUser | null>(null);
  const queryClient = useQueryClient();

  const clearSession = useCallback(() => {
    tokenStore.set(null);
    setUser(null);
    setStatus('anonymous');
    queryClient.clear(); // não deixa dados do usuário anterior em cache
  }, [queryClient]);

  // Ao abrir a página, tenta recuperar a sessão pelo cookie de refresh.
  useEffect(() => {
    let cancelled = false;
    refreshAccessToken()
      .then(() => authService.getMe())
      .then((me) => {
        if (!cancelled) {
          setUser(me);
          setStatus('authenticated');
        }
      })
      .catch(() => {
        if (!cancelled) clearSession();
      });
    return () => {
      cancelled = true;
    };
  }, [clearSession]);

  useEffect(() => onSessionExpired(clearSession), [clearSession]);

  const login = useCallback(async (email: string, password: string) => {
    await authService.login(email, password);
    const me = await authService.getMe();
    setUser(me);
    setStatus('authenticated');
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const value = useMemo(() => ({ status, user, login, logout }), [status, user, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
