import { Link } from 'react-router-dom';
import { Compass } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <span className="grid h-14 w-14 place-items-center rounded-full bg-ink-100">
        <Compass className="h-7 w-7 text-ink-500" aria-hidden="true" />
      </span>

      <p className="mt-6 text-sm font-semibold uppercase tracking-wide text-brand-600">Error 404</p>
      <h1 className="mt-2">We could not find that page</h1>
      <p className="mt-3 max-w-md text-ink-600">
        The link may be out of date, or the address may have been mistyped. Nothing has been lost —
        your saved analyses are unaffected.
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link to="/">
          <Button>Go to the home page</Button>
        </Link>
        <Link to="/dashboard">
          <Button variant="secondary">Go to your dashboard</Button>
        </Link>
      </div>
    </div>
  );
}
