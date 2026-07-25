import { Link, NavLink, Outlet } from 'react-router-dom';
import { FileSearch } from 'lucide-react';
import { useAuth } from '@/hooks/authContext';
import { cn } from '@/utilities/format';

export function Logo({ className }: { className?: string }) {
  return (
    <Link
      to="/"
      className={cn('inline-flex items-center gap-2 font-semibold text-ink-900', className)}
    >
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">
        <FileSearch className="h-4.5 w-4.5" aria-hidden="true" />
      </span>
      <span className="text-lg tracking-tight">
        Resume<span className="text-brand-600">IQ</span>
      </span>
    </Link>
  );
}

export function PublicLayout() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <a href="#main" className="skip-link">
        Skip to main content
      </a>

      <header className="sticky top-0 z-30 border-b border-ink-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Logo />
          <nav aria-label="Main" className="flex items-center gap-1 sm:gap-2">
            <NavLink
              to="/privacy"
              className={({ isActive }) =>
                cn(
                  'rounded px-3 py-2 text-sm font-medium transition-colors',
                  isActive ? 'text-brand-700' : 'text-ink-600 hover:text-ink-900',
                )
              }
            >
              Privacy
            </NavLink>
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="rounded bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="rounded px-3 py-2 text-sm font-medium text-ink-600 hover:text-ink-900"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="rounded bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Create account
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main id="main" className="flex-1">
        <Outlet />
      </main>

      <SiteFooter />
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-ink-200 bg-ink-50">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-8 sm:flex-row sm:justify-between">
          <div className="max-w-sm space-y-3">
            <Logo />
            <p className="text-sm leading-relaxed text-ink-500">
              A transparent resume-to-job matching tool. Every point in the score is published,
              explained, and traceable to evidence in your document.
            </p>
          </div>

          <div className="flex gap-12">
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-500">
                Product
              </h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <a href="/#how-it-works" className="text-ink-600 hover:text-brand-700">
                    How it works
                  </a>
                </li>
                <li>
                  <a href="/#scoring" className="text-ink-600 hover:text-brand-700">
                    Scoring method
                  </a>
                </li>
                <li>
                  <a href="/#limitations" className="text-ink-600 hover:text-brand-700">
                    Limitations
                  </a>
                </li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-500">
                Your data
              </h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/privacy" className="text-ink-600 hover:text-brand-700">
                    Privacy
                  </Link>
                </li>
                <li>
                  <a href="/#faq" className="text-ink-600 hover:text-brand-700">
                    FAQ
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-8 border-t border-ink-200 pt-6 text-xs leading-relaxed text-ink-500">
          <p>
            ResumeIQ scores are internal estimates produced by a published rubric. They are not a
            simulation of any employer&apos;s applicant tracking system and do not predict hiring
            outcomes.
          </p>
          <p className="mt-2">Built as a portfolio project. Open source under the MIT licence.</p>
        </div>
      </div>
    </footer>
  );
}
