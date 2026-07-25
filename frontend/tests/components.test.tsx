/**
 * Component tests.
 *
 * Queries use accessible roles and labels rather than test IDs, so a passing
 * test is also evidence that the element is reachable by assistive technology.
 */

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Button } from '@/components/ui/Button';
import { Alert, EmptyState, ErrorMessage, ProgressBar } from '@/components/ui/Primitives';
import { CheckboxField, TextAreaField, TextField } from '@/components/ui/Field';
import { Modal } from '@/components/ui/Modal';
import { FileUpload } from '@/features/analysis/FileUpload';
import { ScoreGauge } from '@/features/analysis/ScoreGauge';
import { ScoreBreakdown } from '@/features/analysis/ScoreBreakdown';
import { SkillLists } from '@/features/analysis/SkillLists';
import { AiStatusNotice, StatementAnalysis } from '@/features/analysis/AnalysisPanels';
import { validateResumeFile } from '@/schemas/forms';
import { scoreBand } from '@/utilities/score';
import { formatBytes, humanise } from '@/utilities/format';
import type { ScoreCategory, SkillMatch, StatementSummary } from '@/types';

function pdfFile(name = 'resume.pdf', size = 1024): File {
  const file = new File(['%PDF-1.7 fake content'], name, { type: 'application/pdf' });
  Object.defineProperty(file, 'size', { value: size });
  return file;
}

describe('Button', () => {
  it('renders its label', () => {
    render(<Button>Run analysis</Button>);
    expect(screen.getByRole('button', { name: 'Run analysis' })).toBeInTheDocument();
  });

  it('shows a loading label and blocks interaction while busy', async () => {
    const onClick = vi.fn();
    render(
      <Button isLoading loadingLabel="Analysing…" onClick={onClick}>
        Run analysis
      </Button>,
    );
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
    expect(button).toHaveTextContent('Analysing…');
  });

  it('calls its handler when pressed', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Save</Button>);
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});

describe('Form fields', () => {
  it('associates the label with the input', () => {
    render(<TextField label="Email address" />);
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
  });

  it('announces the error and marks the field invalid', () => {
    render(<TextField label="Password" error="Password must be at least 10 characters long" />);
    const message = screen.getByRole('alert');
    expect(message).toHaveTextContent('at least 10 characters');
    expect(screen.getByLabelText(/password/i)).toHaveAttribute('aria-invalid', 'true');
  });

  it('links the hint to the control for screen readers', () => {
    render(<TextField label="Job title" hint="Optional. Detected automatically." />);
    const input = screen.getByLabelText(/job title/i);
    const describedBy = input.getAttribute('aria-describedby');
    expect(describedBy).toBeTruthy();
    expect(document.getElementById(describedBy!.split(' ')[0]!)).toHaveTextContent('Optional');
  });

  it('marks a required field for both sighted and screen-reader users', () => {
    render(<TextField label="Email address" required />);
    expect(screen.getByText('(required)')).toBeInTheDocument();
  });

  it('supports textarea and checkbox variants', () => {
    render(
      <>
        <TextAreaField label="Job description" />
        <CheckboxField label="Store the extracted resume text" />
      </>,
    );
    expect(screen.getByLabelText(/job description/i).tagName).toBe('TEXTAREA');
    expect(screen.getByLabelText(/store the extracted/i)).toHaveAttribute('type', 'checkbox');
  });
});

describe('Modal', () => {
  const openModal = (onClose = vi.fn()) => {
    render(
      <Modal isOpen onClose={onClose} title="Delete this analysis?" description="Cannot be undone.">
        <button type="button">Inner control</button>
      </Modal>,
    );
    return onClose;
  };

  it('is exposed as a labelled dialog', () => {
    openModal();
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(within(dialog).getByText('Delete this analysis?')).toBeInTheDocument();
  });

  it('closes on Escape', async () => {
    const onClose = openModal();
    await userEvent.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalled();
  });

  it('closes via the close button', async () => {
    const onClose = openModal();
    await userEvent.click(screen.getByRole('button', { name: /close dialog/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it('moves focus into the dialog when it opens', async () => {
    openModal();
    await waitFor(() => {
      expect(screen.getByRole('dialog').contains(document.activeElement)).toBe(true);
    });
  });

  it('renders nothing when closed', () => {
    render(<Modal isOpen={false} onClose={vi.fn()} title="Hidden" />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});

describe('FileUpload', () => {
  it('accepts a PDF and reports it back', async () => {
    const onChange = vi.fn();
    const { container } = render(<FileUpload file={null} onChange={onChange} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    await userEvent.upload(input, pdfFile());
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ name: 'resume.pdf' }));
  });

  it('rejects a non-PDF dropped onto the drop zone', async () => {
    // Dropped rather than picked: the input's accept attribute is only a hint
    // to the file picker, and drag-and-drop bypasses it completely. This is
    // the path where a non-PDF can actually reach the component, so it is the
    // path worth testing.
    const onChange = vi.fn();
    render(<FileUpload file={null} onChange={onChange} />);

    const dropZone = screen.getByText(/drag your pdf here/i).closest('div')!;
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [new File(['x'], 'resume.docx', { type: 'application/vnd.openxmlformats' })],
      },
    });

    expect(await screen.findByRole('alert')).toHaveTextContent(/only pdf files/i);
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it('shows the selected file with its size and a way to remove it', () => {
    render(<FileUpload file={pdfFile('cv.pdf', 2048)} onChange={vi.fn()} />);
    expect(screen.getByText('cv.pdf')).toBeInTheDocument();
    expect(screen.getByText('2 KB')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /remove cv\.pdf/i })).toBeInTheDocument();
  });

  it('clears the selection when removed', async () => {
    const onChange = vi.fn();
    render(<FileUpload file={pdfFile()} onChange={onChange} />);
    await userEvent.click(screen.getByRole('button', { name: /remove/i }));
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it('tells the user their file is not stored', () => {
    render(<FileUpload file={null} onChange={vi.fn()} />);
    expect(screen.getByText(/never saved/i)).toBeInTheDocument();
  });
});

describe('validateResumeFile', () => {
  it('accepts a reasonable PDF', () => {
    expect(validateResumeFile(pdfFile())).toBeNull();
  });

  it.each([
    [null, /select your resume/i],
    [pdfFile('resume.docx'), /only pdf/i],
    [pdfFile('resume.pdf', 0), /empty/i],
    [pdfFile('resume.pdf', 6 * 1024 * 1024), /larger than 5 mb/i],
  ])('rejects invalid input', (file, expected) => {
    expect(validateResumeFile(file as File | null)).toMatch(expected);
  });
});

describe('ScoreGauge', () => {
  it('exposes the score and its band to screen readers', () => {
    render(<ScoreGauge score={69} />);
    const gauge = screen.getByRole('img');
    expect(gauge).toHaveAccessibleName(/69 out of 100/i);
    expect(gauge).toHaveAccessibleName(/moderate alignment/i);
  });

  it('shows the number visually, so colour is never the only signal', () => {
    render(<ScoreGauge score={42} />);
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText(/partial alignment/i)).toBeInTheDocument();
  });
});

describe('scoreBand', () => {
  it.each([
    [95, 'Very strong alignment'],
    [80, 'Strong alignment'],
    [65, 'Moderate alignment'],
    [45, 'Partial alignment'],
    [10, 'Weak alignment'],
  ])('labels %i as %s', (score, label) => {
    expect(scoreBand(score).label).toBe(label);
  });
});

describe('ScoreBreakdown', () => {
  const category = (overrides: Partial<ScoreCategory> = {}): ScoreCategory => ({
    category_key: 'required_skills',
    category_name: 'Required skill coverage',
    weight: 30,
    points_earned: 21.67,
    points_possible: 30,
    explanation: 'Your resume matched 6 of 9 required skills.',
    evidence: [{ skill: 'python', status: 'matched' }],
    recommendation: 'Add Docker if you have used it.',
    limitation: 'Skills are matched against a curated list of roughly 300 terms.',
    ...overrides,
  });

  it('shows the weight and the points for each category', () => {
    render(<ScoreBreakdown categories={[category()]} />);
    expect(screen.getByText('Weight 30')).toBeInTheDocument();

    // Scoped to the category row: the same figure also appears in the total
    // footer, which is correct behaviour rather than a duplicate.
    const row = screen.getByRole('button', { name: /required skill coverage/i });
    expect(within(row).getByText(/21\.67/)).toBeInTheDocument();
  });

  it('reveals the evidence, recommendation and limitation when expanded', async () => {
    render(<ScoreBreakdown categories={[category()]} />);
    const toggle = screen.getByRole('button', { name: /required skill coverage/i });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');

    await userEvent.click(toggle);

    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/add docker if you have used it/i)).toBeInTheDocument();
    expect(screen.getByText(/curated list of roughly 300 terms/i)).toBeInTheDocument();
  });

  it('marks an unscored category rather than showing it as a zero', () => {
    render(
      <ScoreBreakdown
        categories={[
          category({
            category_key: 'preferred_skills',
            category_name: 'Preferred skill coverage',
            points_earned: 0,
            points_possible: 0,
            explanation: 'No preferred skills could be extracted, so this was not scored.',
          }),
        ]}
      />,
    );
    expect(screen.getByText('Not scored')).toBeInTheDocument();
  });

  it('shows a total the user can check against the headline score', () => {
    render(<ScoreBreakdown categories={[category(), category({ category_key: 'x' })]} />);
    expect(screen.getByText(/43\.34 \/ 60/)).toBeInTheDocument();
  });
});

describe('SkillLists', () => {
  const skill = (overrides: Partial<SkillMatch> = {}): SkillMatch => ({
    skill_name: 'python',
    match_status: 'matched',
    requirement_level: 'required',
    matched_via: 'exact',
    evidence_snippet: 'Built data pipelines in Python',
    ...overrides,
  });

  it('groups skills and shows a count for each group', () => {
    render(
      <SkillLists
        skills={{
          matched: [skill()],
          partial: [skill({ skill_name: 'postgresql', match_status: 'partial' })],
          missing: [
            skill({ skill_name: 'docker', match_status: 'missing', evidence_snippet: null }),
          ],
        }}
      />,
    );
    expect(screen.getByText(/^Matched/)).toBeInTheDocument();
    expect(screen.getByText('Docker')).toBeInTheDocument();
  });

  it('shows the evidence for a matched skill', () => {
    render(<SkillLists skills={{ matched: [skill()], partial: [], missing: [] }} />);
    expect(screen.getByText(/built data pipelines in python/i)).toBeInTheDocument();
  });

  it('handles an empty group without breaking', () => {
    render(<SkillLists skills={{ matched: [], partial: [], missing: [] }} />);
    expect(screen.getAllByText(/none in this group/i)).toHaveLength(3);
  });
});

describe('StatementAnalysis', () => {
  const summary = (overrides: Partial<StatementSummary> = {}): StatementSummary => ({
    total_bullets: 10,
    with_measurable_result: 2,
    action_verb_rate: 0.6,
    findings: [
      {
        statement_text: 'Responsible for maintaining the company website',
        issue_codes: ['GENERIC_PHRASING', 'NO_ACTION_VERB'],
        word_count: 7,
        has_measurable_result: false,
        suggestion: 'Open with a specific action verb describing what you did.',
      },
    ],
    ...overrides,
  });

  it('shows the flagged statement with readable issue labels', () => {
    render(<StatementAnalysis statements={summary()} />);
    expect(screen.getByText(/responsible for maintaining/i)).toBeInTheDocument();
    expect(screen.getByText('Generic phrasing')).toBeInTheDocument();
    expect(screen.getByText('No action verb')).toBeInTheDocument();
  });

  it('states that suggestions never invent figures', () => {
    render(<StatementAnalysis statements={summary()} />);
    expect(screen.getByText(/never supply a figure/i)).toBeInTheDocument();
  });

  it('celebrates a clean result rather than showing an empty list', () => {
    render(<StatementAnalysis statements={summary({ findings: [] })} />);
    expect(screen.getByText(/no weakening patterns detected/i)).toBeInTheDocument();
  });
});

describe('AiStatusNotice', () => {
  it('presents an AI outage as information, not an error', () => {
    render(
      <AiStatusNotice
        status="unavailable"
        reasonCode="not_configured"
        message="AI suggestions are not available right now. The analysis below is complete."
      />,
    );
    // status, not alert: nothing has gone wrong from the user's point of view.
    expect(screen.getByRole('status')).toHaveTextContent(/analysis below is complete/i);
    expect(screen.getByText(/no ai provider is configured/i)).toBeInTheDocument();
  });

  it('confirms when AI suggestions are present', () => {
    render(
      <AiStatusNotice
        status="available"
        reasonCode={null}
        message="AI suggestions were generated."
      />,
    );
    expect(screen.getByText(/ai suggestions included/i)).toBeInTheDocument();
  });
});

describe('Feedback primitives', () => {
  it('announces a danger alert', () => {
    render(
      <Alert tone="danger" title="Upload failed">
        Try a different file.
      </Alert>,
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Upload failed');
  });

  it('renders all three parts of an API error', () => {
    render(
      <ErrorMessage
        error={{
          what: 'We could not read any text from this PDF.',
          why: 'It looks like a scan.',
          nextStep: 'Export a text-based PDF and try again.',
          requestId: 'abc123',
        }}
      />,
    );
    expect(screen.getByText(/could not read any text/i)).toBeInTheDocument();
    expect(screen.getByText(/looks like a scan/i)).toBeInTheDocument();
    expect(screen.getByText(/export a text-based pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/abc123/)).toBeInTheDocument();
  });

  it('offers a retry when one is available', async () => {
    const onRetry = vi.fn();
    render(
      <ErrorMessage
        error={{ what: 'Failed', why: 'Network', nextStep: 'Retry', requestId: undefined }}
        onRetry={onRetry}
      />,
    );
    await userEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('exposes progress to assistive technology', () => {
    render(<ProgressBar value={65} label="Required skill coverage" />);
    const bar = screen.getByRole('progressbar', { name: 'Required skill coverage' });
    expect(bar).toHaveAttribute('aria-valuenow', '65');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('renders an empty state with a call to action', () => {
    render(
      <EmptyState
        title="No analyses yet"
        description="Upload a resume to get started."
        action={<Button>Run your first analysis</Button>}
      />,
    );
    expect(screen.getByRole('heading', { name: /no analyses yet/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run your first analysis/i })).toBeInTheDocument();
  });
});

describe('Formatting helpers', () => {
  it('formats byte sizes', () => {
    expect(formatBytes(512)).toBe('512 B');
    expect(formatBytes(2048)).toBe('2 KB');
    expect(formatBytes(3 * 1024 * 1024)).toBe('3.0 MB');
  });

  it('humanises snake_case keys', () => {
    expect(humanise('rest_api')).toBe('Rest Api');
    expect(humanise('measurable_achievements')).toBe('Measurable Achievements');
  });
});
