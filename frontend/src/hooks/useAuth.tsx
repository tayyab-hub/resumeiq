import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { authApi } from '@/api/auth';
import { restoreSession, setSessionLostHandler } from '@/api/client';
import { AuthContext, type AuthContextValue } from '@/hooks/authContext';
import { clearAccessToken, setAccessToken } from '@/services/tokenStore';
import type { User } from '@/types';

// This module exports only the provider component. `useAuth` lives in
// `@/hooks/authContext` — re-exporting it here would re-introduce the mixed
// component/non-component export that breaks Fast Refresh.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  /**
   * Restore the session on load.
   *
   * The access token lives only in memory, so a page refresh always starts
   * with none. The httpOnly refresh cookie is what proves the session is still
   * valid — the trade for not putting a token in localStorage.
   */
  useEffect(() => {
    let cancelled = false;

    restoreSession()
      .then((response) => {
        if (cancelled || !response) return;
        setAccessToken(response.access_token);
        setUserState(response.user);
      })
      .catch(() => {
        // No valid session. Not an error condition — this is the common case
        // for a first-time visitor.
        if (!cancelled) clearAccessToken();
      })
      .finally(() => {
        if (!cancelled) setIsRestoring(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // A failed silent refresh mid-session must clear the UI, not leave a stale
  // "logged in" shell behind.
  useEffect(() => {
    setSessionLostHandler(() => {
      clearAccessToken();
      setUserState(null);
    });
    return () => setSessionLostHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login({ email, password });
    setAccessToken(response.access_token);
    setUserState(response.user);
  }, []);

  const register = useCallback(async (fullName: string, email: string, password: string) => {
    const response = await authApi.register({ full_name: fullName, email, password });
    setAccessToken(response.access_token);
    setUserState(response.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      // Local state clears regardless: a network failure must not leave the
      // user apparently signed in.
      clearAccessToken();
      setUserState(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isRestoring,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
      setUser: setUserState,
    }),
    [user, isRestoring, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
