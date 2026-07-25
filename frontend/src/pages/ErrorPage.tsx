import { isRouteErrorResponse, Link, useRouteError } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';

/**
 * The route-level error boundary.
 *
 * A rendering failure shows this rather than a blank page. Nothing about the
 * underlying error is displayed: an exception message can carry internal
 * detail, and it would mean nothing to the user in any case.
 */
export function ErrorPage() {
  const error = useRouteError();
  const status = isRouteErrorResponse(error) ? error.status : null;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <span className="grid h-14 w-14 place-items-center rounded-full bg-danger-50">
        <AlertTriangle className="h-7 w-7 text-danger-600" aria-hidden="true" />
      </span>

      {status && (
        <p className="mt-6 text-sm font-semibold uppercase tracking-wide text-danger-600">
          Error {status}
        </p>
      )}
      <h1 className="mt-2">Something went wrong</h1>
      <p className="mt-3 max-w-md text-ink-600">
        This page failed to load. It is a fault on our side, not in anything you did, and your saved
        analyses are unaffected.
      </p>
      <p className="mt-2 max-w-md text-sm text-ink-500">
        Reloading usually fixes it. If it keeps happening, sign out and back in again.
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Button onClick={() => window.location.reload()}>Reload the page</Button>
        <Link to="/">
          <Button variant="secondary">Go to the home page</Button>
        </Link>
      </div>
    </div>
  );
}
