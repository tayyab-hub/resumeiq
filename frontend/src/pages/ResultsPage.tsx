import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Download, Printer, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, ErrorMessage, LoadingBlock } from '@/components/ui/Primitives';
import { ScoreGauge } from '@/features/analysis/ScoreGauge';
import { ScoreBreakdown } from '@/features/analysis/ScoreBreakdown';
import { SkillLists } from '@/features/analysis/SkillLists';
import {
  AiStatusNotice,
  JobRequirements,
  LimitationsNotice,
  RecommendationList,
  ScoreDisclaimer,
  SectionAnalysis,
  StatementAnalysis,
} from '@/features/analysis/AnalysisPanels';
import { analysesApi } from '@/api/analyses';
import { toApiError } from '@/api/client';
import { downloadAnalysisJson } from '@/services/exportReport';
import { formatDateTime } from '@/utilities/format';

export function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [regenerateError, setRegenerateError] = useState<string | null>(null);

  const {
    data: analysis,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => analysesApi.get(id!),
    enabled: Boolean(id),
  });

  const regenerate = useMutation({
    mutationFn: () => analysesApi.regenerateRecommendations(id!),
    onSuccess: (updated) => {
      queryClient.setQueryData(['analysis', id], updated);
      setRegenerateError(null);
    },
    onError: (mutationError) => setRegenerateError(toApiError(mutationError).what),
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl">
        <LoadingBlock label="Loading your analysis" />
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <ErrorMessage error={toApiError(error)} onRetry={() => void refetch()} />
        <Link to="/history" className="text-sm font-medium text-brand-700 underline">
          Back to your history
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Navigation and controls are excluded from print by `no-print`. */}
      <div className="no-print">
        <Link
          to="/history"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-600 hover:text-ink-900"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to history
        </Link>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate">{analysis.title}</h1>
          <p className="mt-1 text-sm text-ink-500">
            {analysis.resume_filename} · analysed {formatDateTime(analysis.created_at)}
          </p>
        </div>

        <div className="flex gap-2 no-print">
          <Button variant="secondary" size="sm" onClick={() => window.print()}>
            <Printer className="h-4 w-4" aria-hidden="true" />
            Print
          </Button>
          <Button variant="secondary" size="sm" onClick={() => downloadAnalysisJson(analysis)}>
            <Download className="h-4 w-4" aria-hidden="true" />
            Download
          </Button>
        </div>
      </div>

      <Card>
        <CardBody className="flex flex-col items-center gap-8 py-8 sm:flex-row sm:items-center sm:justify-around">
          <ScoreGauge score={analysis.overall_score} />
          <dl className="grid w-full max-w-sm gap-3 text-sm">
            <div className="flex justify-between border-b border-ink-200 pb-2">
              <dt className="text-ink-500">Role</dt>
              <dd className="font-medium text-ink-900">
                {analysis.job_analysis.job_title ?? 'Not stated'}
              </dd>
            </div>
            <div className="flex justify-between border-b border-ink-200 pb-2">
              <dt className="text-ink-500">Required skills matched</dt>
              <dd className="font-medium tabular-nums text-ink-900">
                {analysis.skills.matched.filter((s) => s.requirement_level === 'required').length}{' '}
                of {analysis.job_analysis.required_skills.length}
              </dd>
            </div>
            <div className="flex justify-between border-b border-ink-200 pb-2">
              <dt className="text-ink-500">Sections detected</dt>
              <dd className="font-medium tabular-nums text-ink-900">
                {analysis.sections.filter((s) => s.detected).length} of {analysis.sections.length}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-500">Measurable achievements</dt>
              <dd className="font-medium tabular-nums text-ink-900">
                {analysis.statements.with_measurable_result}
              </dd>
            </div>
          </dl>
        </CardBody>
      </Card>

      <ScoreDisclaimer text={analysis.disclaimer} />

      <div className="space-y-2">
        <AiStatusNotice
          status={analysis.ai_status}
          reasonCode={analysis.ai_reason_code}
          message={analysis.ai_message}
        />
        {analysis.ai_status === 'unavailable' &&
          analysis.ai_reason_code !== 'resume_text_not_stored' && (
            <div className="no-print">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => regenerate.mutate()}
                isLoading={regenerate.isPending}
                loadingLabel="Requesting…"
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Try AI suggestions again
              </Button>
              {regenerateError && (
                <p role="alert" className="mt-2 text-sm text-danger-600">
                  {regenerateError}
                </p>
              )}
            </div>
          )}
      </div>

      <RecommendationList recommendations={analysis.recommendations} />
      <ScoreBreakdown categories={analysis.score_breakdown} />
      <SkillLists skills={analysis.skills} />
      <JobRequirements job={analysis.job_analysis} />
      <SectionAnalysis sections={analysis.sections} />
      <StatementAnalysis statements={analysis.statements} />
      <LimitationsNotice />
    </div>
  );
}
