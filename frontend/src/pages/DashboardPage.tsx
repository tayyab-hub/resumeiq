import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { BarChart3, FilePlus2, FileText, Target, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  ErrorMessage,
  Skeleton,
} from '@/components/ui/Primitives';
import { analysesApi } from '@/api/analyses';
import { toApiError } from '@/api/client';
import { useAuth } from '@/hooks/authContext';
import { formatDate, formatRelative, humanise } from '@/utilities/format';
import { scoreBand } from '@/utilities/score';

function StatCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  icon: typeof FileText;
}) {
  return (
    <Card>
      <CardBody className="flex items-start gap-4">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-brand-50">
          <Icon className="h-5 w-5 text-brand-600" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="text-sm text-ink-500">{label}</p>
          <p className="text-2xl font-semibold tabular-nums text-ink-900">{value}</p>
          {hint && <p className="text-xs text-ink-400">{hint}</p>}
        </div>
      </CardBody>
    </Card>
  );
}

function StatsSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" role="status" aria-live="polite">
      <span className="sr-only">Loading your dashboard</span>
      {[0, 1, 2, 3].map((index) => (
        <Card key={index}>
          <CardBody className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-7 w-16" />
          </CardBody>
        </Card>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();

  const statsQuery = useQuery({ queryKey: ['dashboard-stats'], queryFn: analysesApi.stats });
  const recentQuery = useQuery({
    queryKey: ['analyses', 1, 5],
    queryFn: () => analysesApi.list(1, 5),
  });

  const stats = statsQuery.data;
  const firstName = user?.full_name.split(' ')[0] ?? 'there';

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1>Welcome back, {firstName}</h1>
          <p className="mt-1 text-ink-600">
            Every analysis you run is saved here, privately to your account.
          </p>
        </div>
        <Link to="/analyses/new">
          <Button size="lg">
            <FilePlus2 className="h-4 w-4" aria-hidden="true" />
            New analysis
          </Button>
        </Link>
      </div>

      {statsQuery.isLoading ? (
        <StatsSkeleton />
      ) : statsQuery.error ? (
        <ErrorMessage
          error={toApiError(statsQuery.error)}
          onRetry={() => void statsQuery.refetch()}
        />
      ) : stats ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Analyses run" value={String(stats.total_analyses)} icon={FileText} />
          <StatCard
            label="Average score"
            value={stats.average_score === null ? '—' : String(stats.average_score)}
            hint={stats.average_score === null ? 'Run your first analysis' : 'out of 100'}
            icon={BarChart3}
          />
          <StatCard
            label="Best score"
            value={stats.best_score === null ? '—' : String(stats.best_score)}
            hint={stats.best_score === null ? undefined : scoreBand(stats.best_score).label}
            icon={Target}
          />
          <StatCard
            label="Last 30 days"
            value={String(stats.analyses_this_month)}
            hint="analyses run"
            icon={TrendingUp}
          />
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Score trend"
            description="Your overall match score across saved analyses, oldest first."
          />
          <CardBody>
            {statsQuery.isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : !stats || stats.score_trend.length < 2 ? (
              // A one-point line chart is meaningless; say so rather than
              // rendering a broken axis.
              <EmptyState
                icon={TrendingUp}
                title="Not enough data yet"
                description="Run at least two analyses and your score trend will appear here."
              />
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={stats.score_trend}
                    margin={{ top: 8, right: 8, bottom: 0, left: -20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value: string) => formatDate(value)}
                      stroke="#94a3b8"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      domain={[0, 100]}
                      stroke="#94a3b8"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      formatter={(value: number) => [`${value} / 100`, 'Score']}
                      labelFormatter={(value: string) => formatDate(value)}
                      contentStyle={{
                        borderRadius: 8,
                        border: '1px solid #e2e8f0',
                        fontSize: 13,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#2049e0"
                      strokeWidth={2}
                      dot={{ r: 3, fill: '#2049e0' }}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="Most common gaps"
            description="Required skills missing across your analyses."
          />
          <CardBody>
            {statsQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-3/5" />
              </div>
            ) : !stats || stats.common_missing_skills.length === 0 ? (
              <EmptyState
                title="Nothing to show yet"
                description="Missing required skills will be summarised here once you have run an analysis."
              />
            ) : (
              <ul className="space-y-2">
                {stats.common_missing_skills.map((entry) => (
                  <li
                    key={entry.skill}
                    className="flex items-center justify-between rounded border border-ink-200 px-3 py-2 text-sm"
                  >
                    <span className="truncate font-medium text-ink-800">
                      {humanise(entry.skill)}
                    </span>
                    <span className="shrink-0 tabular-nums text-ink-500">{entry.occurrences}×</span>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Recent analyses"
          action={
            <Link to="/history" className="text-sm font-medium text-brand-700 underline">
              View all
            </Link>
          }
        />
        <CardBody className="p-0">
          {recentQuery.isLoading ? (
            <div className="space-y-3 p-5">
              <Skeleton className="h-5 w-full" />
              <Skeleton className="h-5 w-full" />
              <Skeleton className="h-5 w-2/3" />
            </div>
          ) : recentQuery.error ? (
            <div className="p-5">
              <ErrorMessage
                error={toApiError(recentQuery.error)}
                onRetry={() => void recentQuery.refetch()}
              />
            </div>
          ) : !recentQuery.data || recentQuery.data.items.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No analyses yet"
              description="Upload a resume and paste a job description to see how well they match, and exactly why."
              action={
                <Link to="/analyses/new">
                  <Button>Run your first analysis</Button>
                </Link>
              }
            />
          ) : (
            <ul className="divide-y divide-ink-200">
              {recentQuery.data.items.map((item) => {
                const band = scoreBand(item.overall_score);
                return (
                  <li key={item.id}>
                    <Link
                      to={`/analyses/${item.id}`}
                      className="flex items-center gap-4 px-5 py-3.5 hover:bg-ink-50"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium text-ink-900">{item.title}</p>
                        <p className="text-xs text-ink-500">
                          <time dateTime={item.created_at} title={formatDate(item.created_at)}>
                            {formatRelative(item.created_at)}
                          </time>
                        </p>
                      </div>
                      <span className={`shrink-0 text-lg font-semibold tabular-nums ${band.text}`}>
                        {item.overall_score}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
