import { AlertTriangle, Check, Info, Sparkles, X } from 'lucide-react';
import { Alert, Badge, Card, CardBody, CardHeader } from '@/components/ui/Primitives';
import { AI_REASON_LABELS, ISSUE_LABELS, SECTION_LABELS } from '@/utilities/score';
import { formatPercent, humanise } from '@/utilities/format';
import type {
  AiStatus,
  JobAnalysis,
  Recommendation,
  ResumeSectionResult,
  StatementSummary,
} from '@/types';

// --- Sections --------------------------------------------------------------

export function SectionAnalysis({ sections }: { sections: ResumeSectionResult[] }) {
  const detected = sections.filter((section) => section.detected);

  return (
    <Card>
      <CardHeader
        title="Resume sections"
        description={`${detected.length} of ${sections.length} standard sections detected. Detection is based on headings and content patterns.`}
      />
      <CardBody>
        <ul className="grid gap-2 sm:grid-cols-2">
          {sections.map((section) => (
            <li
              key={section.section_key}
              className="flex items-start gap-3 rounded border border-ink-200 px-3 py-2.5"
            >
              {section.detected ? (
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-success-600" aria-hidden="true" />
              ) : (
                <X className="mt-0.5 h-4 w-4 shrink-0 text-ink-400" aria-hidden="true" />
              )}
              <div className="min-w-0 space-y-0.5">
                <p className="text-sm font-medium text-ink-900">
                  {SECTION_LABELS[section.section_key] ?? humanise(section.section_key)}
                  <span className="sr-only">{section.detected ? ': detected' : ': missing'}</span>
                </p>
                <p className="text-xs leading-relaxed text-ink-500">{section.note}</p>
                {/* Showing the trigger makes the detection auditable. */}
                {section.matched_heading && (
                  <p className="text-xs text-ink-400">
                    Matched heading: “{section.matched_heading}”
                  </p>
                )}
              </div>
            </li>
          ))}
        </ul>
      </CardBody>
    </Card>
  );
}

// --- Statements ------------------------------------------------------------

export function StatementAnalysis({ statements }: { statements: StatementSummary }) {
  return (
    <Card>
      <CardHeader
        title="Statement quality"
        description="Bullets flagged by the rule engine, and what would make each one stronger."
      />
      <CardBody className="space-y-4">
        <dl className="grid gap-3 sm:grid-cols-3">
          <div className="rounded border border-ink-200 px-3 py-2.5">
            <dt className="text-xs text-ink-500">Statements reviewed</dt>
            <dd className="text-lg font-semibold tabular-nums text-ink-900">
              {statements.total_bullets}
            </dd>
          </div>
          <div className="rounded border border-ink-200 px-3 py-2.5">
            <dt className="text-xs text-ink-500">With a measurable result</dt>
            <dd className="text-lg font-semibold tabular-nums text-ink-900">
              {statements.with_measurable_result}
            </dd>
          </div>
          <div className="rounded border border-ink-200 px-3 py-2.5">
            <dt className="text-xs text-ink-500">Open with an action verb</dt>
            <dd className="text-lg font-semibold tabular-nums text-ink-900">
              {formatPercent(statements.action_verb_rate)}
            </dd>
          </div>
        </dl>

        {statements.findings.length === 0 ? (
          <Alert tone="success" title="No weakening patterns detected">
            Your statements open with action verbs and avoid generic phrasing.
          </Alert>
        ) : (
          <ul className="space-y-3">
            {statements.findings.map((finding, index) => (
              <li key={index} className="rounded-lg border border-ink-200 p-4">
                <p className="text-sm leading-relaxed text-ink-800">“{finding.statement_text}”</p>

                <div className="mt-2 flex flex-wrap gap-1.5">
                  {finding.issue_codes.map((code) => (
                    <Badge key={code} tone="warning">
                      {ISSUE_LABELS[code] ?? humanise(code)}
                    </Badge>
                  ))}
                  <Badge tone="neutral">{finding.word_count} words</Badge>
                </div>

                {finding.suggestion && (
                  <p className="mt-3 border-l-2 border-brand-300 pl-3 text-sm leading-relaxed text-ink-600">
                    {finding.suggestion}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}

        <p className="text-xs leading-relaxed text-ink-500">
          Suggestions describe the shape of a stronger statement. They never supply a figure, an
          employer, or an outcome — those must come from you, and must be true.
        </p>
      </CardBody>
    </Card>
  );
}

// --- Job requirements ------------------------------------------------------

export function JobRequirements({ job }: { job: JobAnalysis }) {
  return (
    <Card>
      <CardHeader
        title="What this job asks for"
        description="Extracted from the posting you pasted."
      />
      <CardBody className="space-y-4">
        <dl className="grid gap-3 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-ink-500">Experience requested</dt>
            <dd className="text-sm font-medium text-ink-900">
              {job.min_years_experience ? `${job.min_years_experience}+ years` : 'Not stated'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-ink-500">Education requested</dt>
            <dd className="text-sm font-medium capitalize text-ink-900">
              {job.required_education_level ?? 'Not stated'}
            </dd>
          </div>
        </dl>

        {/* Disclosing the fallback rather than presenting a guess as a fact. */}
        {job.requirement_split_inferred && (
          <Alert tone="warning" title="This posting did not separate required from preferred">
            No “nice to have” or “preferred” section was found, so every requirement was treated as
            required. Your score may be stricter than the employer intends — read the posting
            yourself to judge which requirements are genuinely essential.
          </Alert>
        )}
      </CardBody>
    </Card>
  );
}

// --- Recommendations -------------------------------------------------------

const PRIORITY_TONE = { high: 'danger', medium: 'warning', low: 'neutral' } as const;

export function RecommendationList({ recommendations }: { recommendations: Recommendation[] }) {
  if (recommendations.length === 0) return null;

  return (
    <Card>
      <CardHeader
        title="Improvement priorities"
        description="Ordered by impact. Each item is labelled with where it came from."
      />
      <CardBody>
        <ol className="space-y-3">
          {recommendations.map((recommendation, index) => (
            <li key={index} className="rounded-lg border border-ink-200 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={PRIORITY_TONE[recommendation.priority]}>
                  {recommendation.priority} priority
                </Badge>
                <Badge tone={recommendation.source === 'ai' ? 'brand' : 'neutral'}>
                  {recommendation.source === 'ai' ? (
                    <span className="inline-flex items-center gap-1">
                      <Sparkles className="h-3 w-3" aria-hidden="true" /> AI suggestion
                    </span>
                  ) : (
                    'Rule-based'
                  )}
                </Badge>
                <Badge tone="neutral">{humanise(recommendation.category)}</Badge>
              </div>

              <h4 className="mt-2 font-medium text-ink-900">{recommendation.title}</h4>
              <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-ink-600">
                {recommendation.detail}
              </p>
            </li>
          ))}
        </ol>
      </CardBody>
    </Card>
  );
}

// --- AI status -------------------------------------------------------------

export function AiStatusNotice({
  status,
  reasonCode,
  message,
}: {
  status: AiStatus;
  reasonCode: string | null;
  message: string;
}) {
  if (status === 'available') {
    return (
      <Alert tone="info" title="AI suggestions included">
        {message}
      </Alert>
    );
  }

  return (
    // Informational, not an error: the analysis below is complete either way.
    <Alert tone="info" title="AI suggestions are unavailable">
      <p>{message}</p>
      {reasonCode && AI_REASON_LABELS[reasonCode] && (
        <p className="mt-1 text-xs opacity-80">Reason: {AI_REASON_LABELS[reasonCode]}</p>
      )}
    </Alert>
  );
}

// --- Disclaimer ------------------------------------------------------------

export function ScoreDisclaimer({ text }: { text: string }) {
  return (
    <div className="flex gap-3 rounded-lg border border-ink-200 bg-ink-50 px-4 py-3">
      <Info className="mt-0.5 h-4.5 w-4.5 shrink-0 text-ink-400" aria-hidden="true" />
      <p className="text-xs leading-relaxed text-ink-600">{text}</p>
    </div>
  );
}

export function LimitationsNotice() {
  return (
    <div className="flex gap-3 rounded-lg border border-warning-500/30 bg-warning-50 px-4 py-3">
      <AlertTriangle className="mt-0.5 h-4.5 w-4.5 shrink-0 text-warning-600" aria-hidden="true" />
      <div className="space-y-1 text-xs leading-relaxed text-warning-700">
        <p className="font-semibold">What this analysis cannot do</p>
        <ul className="list-disc space-y-0.5 pl-4">
          <li>
            Skills are matched lexically against a curated list, so unusual wording is missed.
          </li>
          <li>It cannot verify that anything on your resume is true.</li>
          <li>It does not predict whether you will be shortlisted or hired.</li>
          <li>It is not a replacement for a recruiter or a careers adviser.</li>
        </ul>
      </div>
    </div>
  );
}
