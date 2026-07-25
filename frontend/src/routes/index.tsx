import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AppLayout } from '@/layouts/AppLayout';
import { PublicLayout } from '@/layouts/PublicLayout';
import { ProtectedRoute, PublicOnlyRoute } from '@/routes/ProtectedRoute';
import { LoadingBlock } from '@/components/ui/Primitives';
import { ErrorPage } from '@/pages/ErrorPage';
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { PrivacyPage } from '@/pages/PrivacyPage';
import { RegisterPage } from '@/pages/RegisterPage';

// The authenticated area is code-split: a first-time visitor should not
// download the dashboard and charting library to read the landing page.
const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })),
);
const NewAnalysisPage = lazy(() =>
  import('@/pages/NewAnalysisPage').then((m) => ({ default: m.NewAnalysisPage })),
);
const ResultsPage = lazy(() =>
  import('@/pages/ResultsPage').then((m) => ({ default: m.ResultsPage })),
);
const HistoryPage = lazy(() =>
  import('@/pages/HistoryPage').then((m) => ({ default: m.HistoryPage })),
);
const ProfilePage = lazy(() =>
  import('@/pages/ProfilePage').then((m) => ({ default: m.ProfilePage })),
);

function Lazy({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-4xl py-10">
          <LoadingBlock />
        </div>
      }
    >
      {children}
    </Suspense>
  );
}

const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    errorElement: <ErrorPage />,
    children: [
      { path: '/', element: <LandingPage /> },
      { path: '/privacy', element: <PrivacyPage /> },
      {
        path: '/login',
        element: (
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        ),
      },
      {
        path: '/register',
        element: (
          <PublicOnlyRoute>
            <RegisterPage />
          </PublicOnlyRoute>
        ),
      },
    ],
  },
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    errorElement: <ErrorPage />,
    children: [
      {
        path: '/dashboard',
        element: (
          <Lazy>
            <DashboardPage />
          </Lazy>
        ),
      },
      {
        path: '/analyses/new',
        element: (
          <Lazy>
            <NewAnalysisPage />
          </Lazy>
        ),
      },
      {
        path: '/analyses/:id',
        element: (
          <Lazy>
            <ResultsPage />
          </Lazy>
        ),
      },
      {
        path: '/history',
        element: (
          <Lazy>
            <HistoryPage />
          </Lazy>
        ),
      },
      {
        path: '/profile',
        element: (
          <Lazy>
            <ProfilePage />
          </Lazy>
        ),
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
]);

export function AppRoutes() {
  return <RouterProvider router={router} />;
}
