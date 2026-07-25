import { useState } from 'react';
import { ChevronDown, Info } from 'lucide-react';
import { Badge, Card, CardBody, CardHeader, ProgressBar } from '@/components/ui/Primitives';
import { cn } from '@/utilities/format';
import type { ScoreCategory } from '@/types';

function toneFor(ratio: number) {
  if (ratio >= 0.75) return 'success' as const;
  if (ratio >= 0.5) return 'warning' as const;
  return 'danger' as const;
}

function EvidenceList({ evidence }: { evidence: Array<Record<string, unknown>> }) {
  if (evidence.length === 0) return null;

  return (
    <ul className="mt-3 space-y-1.5">
      {evidence.slice(0, 12).map((item, index) => (
        <li key={index} className="rounded bg-ink-50 px-3 py-2 text-xs text-ink-600">
          {Object.entries(item)
            .filter(([, value]) => value !== null && value !== undefined && value !== '')
            .map(([key, value]) => (
              <span key={key} className="mr-3 inline-block">
                <span className="font-medium text-ink-500">{key.replace(/_/g, ' ')}:</span>{' '}
                {Array.isArray(value) ? value.join(', ') : String(value)}
              </span>
            ))}
        </li>
      ))}
      {evidence.length > 12 && (
        <li className="px-3 text-xs text-ink-400">
          …and {evidence.length - 12} more items of evidence
        </li>
      )}
    </ul>
  );
}

function CategoryRow({ category }: { category: ScoreCategory }) {
  const [isOpen, setIsOpen] = useState(false);
  const isScored = category.points_possible > 0;
  const ratio = isScored ? category.points_earned / category.points_possible : 0;

  return (
    <li className="border-b border-ink-200 last:border-0">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        aria-expanded={isOpen}
        className="flex w-full items-start gap-4 px-5 py-4 text-left hover:bg-ink-50"
      >
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-ink-900">{category.category_name}</span>
            <Badge tone="neutral">Weight {category.weight}</Badge>
            {!isScored && <Badge tone="info">Not scored</Badge>}
          </div>

          <p className="text-sm leading-relaxed text-ink-600">{category.explanation}</p>

          {isScored && (
            <ProgressBar value={ratio * 100} tone={toneFor(ratio)} label={category.category_name} />
          )}
        </div>

        <div className="flex shrink-0 items-center gap-3 pt-0.5">
          <span className="tabular-nums text-sm font-semibold text-ink-900">
            {category.points_earned.toFixed(2)}
            <span className="font-normal text-ink-400">
              {' '}
              / {category.points_possible.toFixed(0)}
            </span>
          </span>
          <ChevronDown
            className={cn('h-4 w-4 text-ink-400 transition-transform', isOpen && 'rotate-180')}
            aria-hidden="true"
          />
        </div>
      </button>

      {isOpen && (
        <div className="space-y-3 bg-ink-50/60 px-5 pb-5 pt-1">
          {category.recommendation && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-500">
                What to do
              </h4>
              <p className="mt-1 text-sm leading-relaxed text-ink-700">{category.recommendation}</p>
            </div>
          )}

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-500">Evidence</h4>
            <EvidenceList evidence={category.evidence} />
            {category.evidence.length === 0 && (
              <p className="mt-1 text-sm text-ink-500">No supporting detail for this category.</p>
            )}
          </div>

          {/* Every category states what it cannot measure. */}
          <div className="flex gap-2 rounded border border-ink-200 bg-white px-3 py-2">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-ink-400" aria-hidden="true" />
            <p className="text-xs leading-relaxed text-ink-500">
              <span className="font-semibold">Limitation:</span> {category.limitation}
            </p>
          </div>
        </div>
      )}
    </li>
  );
}

export function ScoreBreakdown({ categories }: { categories: ScoreCategory[] }) {
  return (
    <Card>
      <CardHeader
        title="Score breakdown"
        description="Every category shows its weight, the points it earned, the evidence behind them, and what it cannot measure. Select a row to expand it."
      />
      <ul>
        {categories.map((category) => (
          <CategoryRow key={category.category_key} category={category} />
        ))}
      </ul>
      <CardBody className="border-t border-ink-200 bg-ink-50/60">
        <p className="text-sm text-ink-600">
          <span className="font-semibold text-ink-900">
            Total:{' '}
            {categories.reduce((sum, category) => sum + category.points_earned, 0).toFixed(2)} /{' '}
            {categories.reduce((sum, category) => sum + category.points_possible, 0).toFixed(0)}
          </span>{' '}
          — rounded to the nearest whole number for the headline score.
        </p>
      </CardBody>
    </Card>
  );
}
