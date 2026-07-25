import type { AnalysisDetail } from '@/types';

/**
 * Download a structured summary of an analysis.
 *
 * JSON rather than a generated PDF: the browser's own print-to-PDF already
 * produces a better-looking document from the print stylesheet, and a
 * machine-readable export is more useful than a second rendering of the same
 * page.
 */
export function downloadAnalysisJson(analysis: AnalysisDetail): void {
  const report = {
    generated_at: new Date().toISOString(),
    generated_by: 'ResumeIQ',
    disclaimer: analysis.disclaimer,
    analysis: {
      title: analysis.title,
      created_at: analysis.created_at,
      resume_filename: analysis.resume_filename,
      overall_score: analysis.overall_score,
      job: analysis.job_analysis,
      score_breakdown: analysis.score_breakdown.map((category) => ({
        category: category.category_name,
        weight: category.weight,
        points_earned: category.points_earned,
        points_possible: category.points_possible,
        explanation: category.explanation,
        recommendation: category.recommendation,
        limitation: category.limitation,
      })),
      skills: {
        matched: analysis.skills.matched.map((skill) => skill.skill_name),
        partially_matched: analysis.skills.partial.map((skill) => skill.skill_name),
        missing: analysis.skills.missing.map((skill) => skill.skill_name),
      },
      sections: analysis.sections.map((section) => ({
        section: section.section_key,
        detected: section.detected,
      })),
      statements: {
        reviewed: analysis.statements.total_bullets,
        with_measurable_result: analysis.statements.with_measurable_result,
        action_verb_rate: analysis.statements.action_verb_rate,
        findings: analysis.statements.findings,
      },
      recommendations: analysis.recommendations,
      ai_status: analysis.ai_status,
    },
  };

  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `resumeiq-${slugify(analysis.title)}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function slugify(value: string): string {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'analysis'
  );
}
