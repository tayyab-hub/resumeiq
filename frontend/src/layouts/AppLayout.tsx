import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  ChevronDown,
  FilePlus2,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  X,
} from 'lucide-react';
import { Logo } from '@/layouts/PublicLayout';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/authContext';
import { cn } from '@/utilities/format';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyses/new', label: 'New analysis', icon: FilePlus2 },
  { to: '/history', label: 'History', icon: History },
  { to: '/profile', label: 'Profile & settings', icon: Settings },
];

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <ul className="space-y-1">
      {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
        <li key={to}>
          <NavLink
            to={to}
            end={to === '/dashboard'}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-ink-600 hover:bg-ink-100 hover:text-ink-900',
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={cn('h-4.5 w-4.5', isActive ? 'text-brand-600' : 'text-ink-400')}
                  aria-hidden="true"
                />
                {label}
              </>
            )}
          </NavLink>
        </li>
      ))}
    </ul>
  );
}

function ProfileMenu() {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isOpen) return;

    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setIsOpen(false);
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsOpen(false);
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  if (!user) return null;

  const initials = user.full_name
    .split(' ')
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-ink-100"
      >
        <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">
          {initials || '?'}
        </span>
        <span className="hidden max-w-[10rem] truncate font-medium text-ink-700 sm:block">
          {user.full_name}
        </span>
        <ChevronDown className="h-4 w-4 text-ink-400" aria-hidden="true" />
      </button>

      {isOpen && (
        <div
          role="menu"
          className="absolute right-0 z-40 mt-2 w-60 overflow-hidden rounded-lg border border-ink-200 bg-white shadow-md"
        >
          <div className="border-b border-ink-200 px-4 py-3">
            <p className="truncate text-sm font-medium text-ink-900">{user.full_name}</p>
            <p className="truncate text-xs text-ink-500">{user.email}</p>
          </div>
          <Link
            to="/profile"
            role="menuitem"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-2 px-4 py-2.5 text-sm text-ink-700 hover:bg-ink-50"
          >
            <Settings className="h-4 w-4 text-ink-400" aria-hidden="true" />
            Profile &amp; settings
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={async () => {
              setIsOpen(false);
              await logout();
              navigate('/');
            }}
            className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-ink-700 hover:bg-ink-50"
          >
            <LogOut className="h-4 w-4 text-ink-400" aria-hidden="true" />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}

export function AppLayout() {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const location = useLocation();

  // Close the mobile drawer on navigation, or it stays open over the new page.
  useEffect(() => setIsDrawerOpen(false), [location.pathname]);

  useEffect(() => {
    if (!isDrawerOpen) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsDrawerOpen(false);
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isDrawerOpen]);

  return (
    <div className="min-h-screen bg-ink-50">
      <a href="#main" className="skip-link">
        Skip to main content
      </a>

      {/* Sidebar on desktop */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-ink-200 bg-white lg:block">
        <div className="flex h-16 items-center border-b border-ink-200 px-5">
          <Logo />
        </div>
        <nav aria-label="Sections" className="p-3">
          <NavItems />
        </nav>
      </aside>

      {/* Slide-over drawer below lg */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-ink-900/40"
            onClick={() => setIsDrawerOpen(false)}
            aria-hidden="true"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
            className="relative h-full w-72 max-w-[85vw] animate-fade-in bg-white shadow-lg"
          >
            <div className="flex h-16 items-center justify-between border-b border-ink-200 px-5">
              <Logo />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsDrawerOpen(false)}
                aria-label="Close navigation"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
            <nav aria-label="Sections" className="p-3">
              <NavItems onNavigate={() => setIsDrawerOpen(false)} />
            </nav>
          </div>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 border-b border-ink-200 bg-white/90 backdrop-blur no-print">
          <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                className="lg:hidden"
                onClick={() => setIsDrawerOpen(true)}
                aria-label="Open navigation"
                aria-expanded={isDrawerOpen}
              >
                <Menu className="h-5 w-5" aria-hidden="true" />
              </Button>
              <div className="lg:hidden">
                <Logo />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to="/analyses/new"
                className="hidden rounded bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 sm:inline-flex"
              >
                New analysis
              </Link>
              <ProfileMenu />
            </div>
          </div>
        </header>

        <main id="main" className="px-4 py-6 sm:px-6 lg:px-8 print-full-width">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
