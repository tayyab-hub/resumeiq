import { createContext, useContext } from 'react';
import type { User } from '@/types';

/**
 * The auth context and its consumer hook.
 *
 * Kept separate from `useAuth.tsx` so that file exports only the provider
 * component. A module that mixes component and non-component exports breaks
 * React Fast Refresh, which is what `react-refresh/only-export-components`
 * warns about.
 */
export interface AuthContextValue {
  user: User | null;
  /** True until the initial session restore finishes. */
  isRestoring: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider');
  }
  return context;
}
