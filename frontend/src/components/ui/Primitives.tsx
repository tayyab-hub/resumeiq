import type { HTMLAttributes, ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, TriangleAlert } from 'lucide-react';
import { cn } from '@/utilities/format';

// --- Card ------------------------------------------------------------------

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('card', className)} {...rest} />;
}

export function CardHeader({
  title,
  description,
  action,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-start justify-between gap-3 border-b border-ink-200 px-5 py-4',
        className,
      )}
    >
      <div className="min-w-0 space-y-1">
        <h3 className="text-base font-semibold text-ink-900">{title}</h3>
        {description && <p className="text-sm text-ink-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function CardBody({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-5 py-4', className)} {...rest} />;
}

// --- Badge -----------------------------------------------------------------

type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'brand';

const BADGE_TONES: Record<BadgeTone, string> = {
  neutral: 'bg-ink-100 text-ink-700 ring-ink-200',
  success: 'bg-success-50 text-success-700 ring-success-500/20',
  warning: 'bg-warning-50 text-warning-700 ring-warning-500/20',
  danger: 'bg-danger-50 text-danger-700 ring-danger-500/20',
  info: 'bg-info-50 text-info-700 ring-info-500/20',
  brand: 'bg-brand-50 text-brand-700 ring-brand-500/20',
};

export function Badge({
  tone = 'neutral',
  className,
  children,
}: {
  tone?: BadgeTone;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        BADGE_TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

// --- Alert -----------------------------------------------------------------

type AlertTone = 'info' | 'success' | 'warning' | 'danger';

const ALERT_TONES: Record<AlertTone, { wrapper: string; icon: typeof Info }> = {
  info: { wrapper: 'bg-info-50 border-info-500/30 text-info-700', icon: Info },
  success: { wrapper: 'bg-success-50 border-success-500/30 text-success-700', icon: CheckCircle2 },
  warning: { wrapper: 'bg-warning-50 border-warning-500/30 text-warning-700', icon: TriangleAlert },
  danger: { wrapper: 'bg-danger-50 border-danger-500/30 text-danger-700', icon: AlertCircle },
};

export function Alert({
  tone = 'info',
  title,
  children,
  action,
  className,
}: {
  tone?: AlertTone;
  title?: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  const { wrapper, icon: Icon } = ALERT_TONES[tone];
  return (
    <div
      // Errors are announced; informational alerts are not, so a page full of
      // notices does not talk over the user.
      role={tone === 'danger' ? 'alert' : 'status'}
      className={cn('flex gap-3 rounded-lg border px-4 py-3', wrapper, className)}
    >
      <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div className="min-w-0 flex-1 space-y-1 text-sm">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className="leading-relaxed">{children}</div>}
        {action && <div className="pt-1">{action}</div>}
      </div>
    </div>
  );
}

/**
 * The standard renderer for an ApiError.
 *
 * Every error the user sees answers the same three questions, because the
 * backend guarantees the three-part shape.
 */
export function ErrorMessage({
  error,
  onRetry,
  className,
}: {
  error: { what: string; why: string; nextStep: string; requestId?: string | undefined };
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <Alert tone="danger" title={error.what} className={className}>
      <p>{error.why}</p>
      <p className="font-medium">{error.nextStep}</p>
      {error.requestId && (
        <p className="pt-1 font-mono text-xs opacity-70">Reference: {error.requestId}</p>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 font-semibold underline underline-offset-2"
        >
          Try again
        </button>
      )}
    </Alert>
  );
}

// --- Skeleton and empty state ---------------------------------------------

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('skeleton h-4 w-full', className)} aria-hidden="true" />;
}

export function LoadingBlock({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="space-y-3" role="status" aria-live="polite">
      <span className="sr-only">{label}</span>
      <Skeleton className="h-5 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon?: typeof Info;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      {Icon && (
        <div className="mb-4 rounded-full bg-ink-100 p-3">
          <Icon className="h-6 w-6 text-ink-500" aria-hidden="true" />
        </div>
      )}
      <h3 className="text-base font-semibold text-ink-900">{title}</h3>
      <p className="mt-1 max-w-prose text-sm text-ink-500">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

// --- Progress --------------------------------------------------------------

export function ProgressBar({
  value,
  max = 100,
  tone = 'brand',
  label,
}: {
  value: number;
  max?: number;
  tone?: 'brand' | 'success' | 'warning' | 'danger';
  label?: string;
}) {
  const ratio = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0;
  const tones = {
    brand: 'bg-brand-500',
    success: 'bg-success-500',
    warning: 'bg-warning-500',
    danger: 'bg-danger-500',
  };
  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(value * 100) / 100}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-label={label}
      className="h-2 w-full overflow-hidden rounded-full bg-ink-200"
    >
      <div
        className={cn('h-full rounded-full transition-[width] duration-500', tones[tone])}
        style={{ width: `${ratio * 100}%` }}
      />
    </div>
  );
}
