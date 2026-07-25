import { useState } from 'react';
import { CheckCircle2, CircleDashed, XCircle } from 'lucide-react';
import { Badge, Card, CardBody, CardHeader } from '@/components/ui/Primitives';
import { humanise } from '@/utilities/format';
import type { SkillMatch } from '@/types';

const VISIBLE_BY_DEFAULT = 8;

function SkillGroup({
  title,
  description,
  skills,
  icon: Icon,
  tone,
}: {
  title: string;
  description: string;
  skills: SkillMatch[];
  icon: typeof CheckCircle2;
  tone: 'success' | 'warning' | 'danger';
}) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? skills : skills.slice(0, VISIBLE_BY_DEFAULT);

  const iconColour = {
    success: 'text-success-600',
    warning: 'text-warning-600',
    danger: 'text-danger-600',
  }[tone];

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Icon className={`h-4.5 w-4.5 ${iconColour}`} aria-hidden="true" />
        <h4 className="font-medium text-ink-900">
          {title} <span className="tabular-nums text-ink-400">({skills.length})</span>
        </h4>
      </div>
      <p className="text-sm text-ink-500">{description}</p>

      {skills.length === 0 ? (
        <p className="rounded bg-ink-50 px-3 py-2 text-sm text-ink-500">None in this group.</p>
      ) : (
        <>
          <ul className="space-y-2">
            {visible.map((skill) => (
              <li key={skill.skill_name} className="rounded border border-ink-200 px-3 py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-ink-900">
                    {humanise(skill.skill_name)}
                  </span>
                  <Badge tone={skill.requirement_level === 'required' ? 'brand' : 'neutral'}>
                    {skill.requirement_level}
                  </Badge>
                  {skill.matched_via && <Badge tone="info">matched via {skill.matched_via}</Badge>}
                </div>
                {/* Evidence, so a claimed match is verifiable rather than asserted. */}
                {skill.evidence_snippet && (
                  <p className="mt-1.5 truncate text-xs italic text-ink-500">
                    “{skill.evidence_snippet}”
                  </p>
                )}
              </li>
            ))}
          </ul>

          {skills.length > VISIBLE_BY_DEFAULT && (
            <button
              type="button"
              onClick={() => setShowAll((open) => !open)}
              className="text-sm font-medium text-brand-700 underline underline-offset-2"
            >
              {showAll ? 'Show fewer' : `Show all ${skills.length}`}
            </button>
          )}
        </>
      )}
    </div>
  );
}

export function SkillLists({
  skills,
}: {
  skills: { matched: SkillMatch[]; partial: SkillMatch[]; missing: SkillMatch[] };
}) {
  return (
    <Card>
      <CardHeader
        title="Skill comparison"
        description="Each requirement extracted from the job description, and whether your resume evidences it."
      />
      <CardBody className="grid gap-8 lg:grid-cols-3">
        <SkillGroup
          title="Matched"
          description="Found in your resume, either exactly or under a known alias."
          skills={skills.matched}
          icon={CheckCircle2}
          tone="success"
        />
        <SkillGroup
          title="Partially matched"
          description="A related technology was found. This earns half credit, because it is evidence rather than proof."
          skills={skills.partial}
          icon={CircleDashed}
          tone="warning"
        />
        <SkillGroup
          title="Missing"
          description="Not found anywhere in your resume. Add only those you genuinely have."
          skills={skills.missing}
          icon={XCircle}
          tone="danger"
        />
      </CardBody>
    </Card>
  );
}
