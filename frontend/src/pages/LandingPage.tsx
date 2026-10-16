import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  FileSearch,
  Gauge,
  ListChecks,
  Lock,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge, Card, CardBody } from '@/components/ui/Primitives';
import sampleAnalysis from '@/data/sample-analysis.json';

const FEATURES = [
  {
    icon: ScanSearch,
    title: 'Requirement extraction',
    body: 'The job description is parsed into required and preferred skills, an experience requirement, and an education level. Where a posting gives no "nice to have" section, the result says so rather than guessing.',
  },
  {
    icon: ListChecks,
    title: 'Evidence for every match',
    body: 'Each matched skill shows the fragment of your resume it was found in, and whether it matched exactly, through a known alias, or only through a related technology.',
  },
  {
    icon: Gauge,
    title: 'A score you can audit',
    body: 'Eight categories, published weights, and a stated limitation on each one. You can reconstruct the total by hand from what is on screen.',
  },
  {
    icon: FileSearch,
    title: 'Statement-level feedback',
    body: 'Bullets are flagged for generic phrasing, passive voice, missing action verbs, and absent results — with structural suggestions that never invent a figure.',
  },
  {
    icon: Sparkles,
    title: 'Optional AI suggestions',
    body: 'AI is disabled on this free demo. An explicitly enabled provider can offer advisory suggestions. Every suggestion is labelled as AI, and the analysis is complete without it.',
  },
  {
    icon: Lock,
    title: 'No permanent PDF storage',
    body: 'Uploads may use temporary storage and are removed after processing. Results retain short evidence excerpts; full text is saved only with your opt-in.',
  },
];

const SCORING = [
  ['Required skill coverage', 30],
  ['Relevant experience indicators', 15],
  ['Preferred skill coverage', 10],
  ['Education alignment', 10],
  ['Keyword coverage', 10],
  ['Resume section completeness', 10],
  ['Measurable achievements', 10],
  ['Statement quality', 5],
] as const;

const FAQ = [
  {
    q: 'Will a high score get me an interview?',
    a: 'No, and nothing that claims otherwise is being honest with you. The score measures how well your resume evidences what one particular posting asks for. Hiring decisions involve the competition, timing, referrals, and human judgement — none of which this tool can see.',
  },
  {
    q: 'Is this the same algorithm as a real applicant tracking system?',
    a: 'No. Commercial ATS platforms do not publish their matching logic, so any tool claiming to replicate them is guessing. ResumeIQ uses its own published rubric, and tells you exactly what that rubric measures.',
  },
  {
    q: 'What happens to my resume?',
    a: 'Uploads may be buffered in temporary storage, then removed after processing. Saved results include evidence snippets and flagged statements. Full extracted text is saved only if you opt in.',
  },
  {
    q: 'What does the AI service receive?',
    a: 'AI is disabled on the free demo. If explicitly enabled in another deployment, it receives curated skill names, section identifiers, numeric counts and issue codes. Free-form statements and titles are excluded. Generated suggestions can still be inaccurate.',
  },
  {
    q: 'Why did it miss a skill I definitely have?',
    a: 'Matching is lexical against a curated list of around 300 terms and their common aliases. An unusual phrasing, or a technology outside that list, will be missed. This understates a score rather than inflating it, and it is why every category publishes its limitation.',
  },
  {
    q: 'Can I delete my data?',
    a: 'Yes. Delete any single analysis, or your whole account, at any time. Deletion is immediate and cascades to every stored record.',
  },
];

function Section({
  id,
  children,
  className = '',
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20 ${className}`}>
      {children}
    </section>
  );
}

export function LandingPage() {
  return (
    <>
      {/* Hero */}
      <Section className="!pb-10 text-center">
        <Badge tone="brand" className="mb-5">
          Transparent by design
        </Badge>
        <h1 className="mx-auto max-w-3xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
          See exactly why your resume does or does not match a job
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-ink-600">
          Upload a PDF resume, paste a job description, and get a breakdown of which requirements
          you evidence and which you do not — with the weight, the points, and the reasoning shown
          for every category.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link
            to="/sample"
            className="rounded-lg bg-brand-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-brand-700"
          >
            Explore Sample Analysis
          </Link>
          <Link
            to="/register"
            className="rounded-lg border border-ink-200 px-6 py-3 text-base font-medium text-ink-800 hover:bg-ink-50"
          >
            Analyse your resume
          </Link>
          <a href="#scoring">
            <Button size="lg" variant="secondary">
              See how scoring works
            </Button>
          </a>
        </div>
        <p className="mt-4 text-sm text-ink-500">
          Try the fictional sample instantly. No signup, personal data or AI API needed.
        </p>
      </Section>

      {/* Demonstration */}
      <Section className="!pt-0">
        <Card className="mx-auto max-w-4xl overflow-hidden">
          <div className="border-b border-ink-200 bg-ink-50 px-5 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-ink-500">
              Example output · demonstration data for a fictional candidate
            </p>
          </div>
          <CardBody className="grid gap-6 sm:grid-cols-[auto_1fr] sm:items-center">
            <div className="text-center">
              <div className="text-5xl font-semibold tabular-nums text-info-700">
                {sampleAnalysis.overall_score}
              </div>
              <p className="text-sm font-medium text-info-700">Rubric score / 100</p>
            </div>
            <ul className="space-y-2 text-sm">
              {sampleAnalysis.score_breakdown
                .slice(0, 4)
                .map((category) => [
                  category.category_name,
                  `${category.points_earned.toFixed(2)} / ${category.points_possible.toFixed(2)}`,
                  category.explanation,
                ])
                .map(([label, points, detail]) => (
                  <li
                    key={label}
                    className="flex flex-wrap items-baseline justify-between gap-x-4 border-b border-ink-200 pb-2"
                  >
                    <span className="font-medium text-ink-800">{label}</span>
                    <span className="tabular-nums text-ink-900">{points}</span>
                    <span className="w-full text-xs text-ink-500">{detail}</span>
                  </li>
                ))}
            </ul>
          </CardBody>
        </Card>
      </Section>

      {/* Features */}
      <Section className="bg-white">
        <h2 className="text-center">What it actually does</h2>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <Card key={title}>
              <CardBody className="space-y-3">
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand-50">
                  <Icon className="h-5 w-5 text-brand-600" aria-hidden="true" />
                </span>
                <h3>{title}</h3>
                <p className="text-sm leading-relaxed text-ink-600">{body}</p>
              </CardBody>
            </Card>
          ))}
        </div>
      </Section>

      {/* Scoring */}
      <Section id="scoring">
        <div className="grid gap-10 lg:grid-cols-2 lg:items-start">
          <div>
            <h2>The scoring model, in full</h2>
            <p className="mt-4 leading-relaxed text-ink-600">
              Eight categories totalling 100 points. Nothing is hidden, and nothing is weighted by a
              model you cannot inspect. If a job description contains no preferred skills, that
              category scores zero out of zero and the rest are rescaled — an employer who lists no
              preferences should not cost you ten points.
            </p>
            <p className="mt-4 leading-relaxed text-ink-600">
              Keyword coverage awards full marks at 60% overlap rather than 100%, deliberately.
              Requiring total overlap would reward stuffing your resume with the posting&apos;s
              vocabulary, which makes it worse to read and no better to a human.
            </p>
          </div>

          <Card>
            <ul className="divide-y divide-ink-200">
              {SCORING.map(([label, weight]) => (
                <li key={label} className="flex items-center justify-between px-5 py-3">
                  <span className="text-sm text-ink-700">{label}</span>
                  <span className="tabular-nums text-sm font-semibold text-ink-900">{weight}</span>
                </li>
              ))}
              <li className="flex items-center justify-between bg-ink-50 px-5 py-3">
                <span className="text-sm font-semibold text-ink-900">Total</span>
                <span className="tabular-nums text-sm font-semibold text-ink-900">100</span>
              </li>
            </ul>
          </Card>
        </div>
      </Section>

      {/* How it works */}
      <Section id="how-it-works" className="bg-white">
        <h2 className="text-center">How it works</h2>
        <ol className="mt-10 grid gap-6 sm:grid-cols-3">
          {[
            [
              'Upload your resume',
              'A text PDF, up to 5 MB and 10 pages. Temporary upload buffers are removed after processing.',
            ],
            [
              'Paste the job description',
              'The posting is parsed into required and preferred skills, experience, and education requirements.',
            ],
            [
              'Read the breakdown',
              'Every category shows its weight, points, evidence, recommendation, and limitation.',
            ],
          ].map(([title, body], index) => (
            <li key={title} className="relative rounded-lg border border-ink-200 p-6">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-600 text-sm font-semibold text-white">
                {index + 1}
              </span>
              <h3 className="mt-4">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-600">{body}</p>
            </li>
          ))}
        </ol>
      </Section>

      {/* Privacy */}
      <Section id="privacy-summary">
        <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <h2>Control what you share and save</h2>
            <p className="mt-4 leading-relaxed text-ink-600">
              A resume contains your full name, address, phone number, and employment history. The
              safest way to protect that is not to hold it.
            </p>
            <Link to="/privacy" className="mt-5 inline-block">
              <Button variant="secondary">Read the full privacy statement</Button>
            </Link>
          </div>

          <ul className="space-y-3">
            {[
              [ShieldCheck, 'PDF uploads are temporary and are not saved in the database.'],
              [Lock, 'Resume text is not stored unless you opt in for that analysis.'],
              [ShieldCheck, 'Passwords are hashed with bcrypt. Session tokens are stored hashed.'],
              [CheckCircle2, 'Resume content never appears in application logs.'],
              [Trash2, 'Delete any analysis, or your whole account, at any time.'],
            ].map(([Icon, text]) => {
              const IconComponent = Icon as typeof ShieldCheck;
              return (
                <li
                  key={text as string}
                  className="flex gap-3 rounded-lg border border-ink-200 bg-white px-4 py-3"
                >
                  <IconComponent
                    className="mt-0.5 h-5 w-5 shrink-0 text-success-600"
                    aria-hidden="true"
                  />
                  <span className="text-sm leading-relaxed text-ink-700">{text as string}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </Section>

      {/* Limitations */}
      <Section id="limitations" className="bg-white">
        <h2>What this tool cannot do</h2>
        <p className="mt-4 max-w-prose leading-relaxed text-ink-600">
          Stated plainly, because a tool that only lists its strengths is not telling you enough to
          judge its output.
        </p>
        <ul className="mt-6 grid max-w-4xl gap-3 sm:grid-cols-2">
          {[
            'It cannot predict whether you will be shortlisted or hired.',
            'It does not replicate any specific employer’s applicant tracking system.',
            'It cannot verify that anything on your resume is true.',
            'Skill matching is lexical, so unusual wording is missed.',
            'It does not read scanned or image-only PDFs.',
            'It is not a replacement for a recruiter or a careers adviser.',
          ].map((item) => (
            <li
              key={item}
              className="rounded-lg border border-ink-200 px-4 py-3 text-sm text-ink-700"
            >
              {item}
            </li>
          ))}
        </ul>
      </Section>

      {/* FAQ */}
      <Section id="faq">
        <h2 className="text-center">Frequently asked questions</h2>
        <div className="mx-auto mt-10 max-w-3xl space-y-3">
          {FAQ.map(({ q, a }) => (
            <details key={q} className="group rounded-lg border border-ink-200 bg-white">
              <summary className="cursor-pointer list-none px-5 py-4 font-medium text-ink-900 marker:hidden">
                <span className="flex items-center justify-between gap-4">
                  {q}
                  <span
                    className="text-ink-400 transition-transform group-open:rotate-45"
                    aria-hidden="true"
                  >
                    +
                  </span>
                </span>
              </summary>
              <p className="border-t border-ink-200 px-5 py-4 text-sm leading-relaxed text-ink-600">
                {a}
              </p>
            </details>
          ))}
        </div>
      </Section>

      {/* Call to action */}
      <Section className="!py-14">
        <Card className="bg-brand-600 text-center">
          <CardBody className="py-12">
            <h2 className="text-white">Find out what a job posting is actually asking for</h2>
            <p className="mx-auto mt-3 max-w-xl leading-relaxed text-brand-100">
              Explore the fictional sample, then review the evidence behind every point.
            </p>
            <Link to="/register" className="mt-7 inline-block">
              <Button size="lg" variant="secondary">
                Create a free account
              </Button>
            </Link>
          </CardBody>
        </Card>
      </Section>
    </>
  );
}
