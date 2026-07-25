import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '@/hooks/authContext';
import { LoadingBlock } from '@/components/ui/Primitives';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isRestoring } = useAuth();
  const location = useLocation();

  // Waiting for the session restore to finish is what prevents the login
  // flash a signed-in user would otherwise see on every page refresh.
  if (isRestoring) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <LoadingBlock label="Restoring your session" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Remember where they were headed so login can return them there.
    return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />;
  }

  return <>{children}</>;
}

export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isRestoring } = useAuth();

  if (isRestoring) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <LoadingBlock label="Loading" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
