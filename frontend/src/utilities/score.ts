/**
 * Score presentation.
 *
 * These bands affect colour and wording only. They change nothing in the
 * calculation, which lives entirely on the server.
 */

export interface ScoreBand {
  label: string;
  text: string;
  bg: string;
  ring: string;
  stroke: string;
}

export function scoreBand(score: number): ScoreBand {
  if (score >= 90)
    return {
      label: 'Very strong alignment',
      text: 'text-success-700',
      bg: 'bg-success-50',
      ring: 'ring-success-500/30',
      stroke: '#059669',
    };
  if (score >= 75)
    return {
      label: 'Strong alignment',
      text: 'text-success-700',
      bg: 'bg-success-50',
      ring: 'ring-success-500/30',
      stroke: '#10b981',
    };
  if (score >= 60)
    return {
      label: 'Moderate alignment',
      text: 'text-info-700',
      bg: 'bg-info-50',
      ring: 'ring-info-500/30',
      stroke: '#3b82f6',
    };
  if (score >= 40)
    return {
      label: 'Partial alignment',
      text: 'text-warning-700',
      bg: 'bg-warning-50',
      ring: 'ring-warning-500/30',
      stroke: '#f59e0b',
    };
  return {
    label: 'Weak alignment',
    text: 'text-danger-700',
    bg: 'bg-danger-50',
    ring: 'ring-danger-500/30',
    stroke: '#ef4444',
  };
}

export const ISSUE_LABELS: Record<string, string> = {
  NO_ACTION_VERB: 'No action verb',
  NO_METRIC: 'No measurable result',
  GENERIC_PHRASING: 'Generic phrasing',
  PASSIVE_VOICE: 'Passive voice',
  TOO_LONG: 'Too long',
  REPETITION: 'Repeated phrasing',
};

export const SECTION_LABELS: Record<string, string> = {
  contact: 'Contact information',
  summary: 'Professional summary',
  skills: 'Skills',
  experience: 'Work experience',
  education: 'Education',
  projects: 'Projects',
  certifications: 'Certifications',
  achievements: 'Achievements',
  languages: 'Languages',
};

export const AI_REASON_LABELS: Record<string, string> = {
  not_configured: 'No AI provider is configured for this deployment.',
  timeout: 'The AI provider did not respond in time.',
  rate_limited: 'The AI provider is rate limiting requests.',
  provider_error: 'The AI provider returned an error.',
  invalid_output: 'The AI response did not match the expected format and was discarded.',
  quota_exceeded: "You have used today's AI suggestion allowance.",
  provider_refused: 'The AI provider declined to process this request.',
  resume_text_not_stored:
    'Regenerating suggestions needs the resume text, which was not stored for this analysis.',
};
