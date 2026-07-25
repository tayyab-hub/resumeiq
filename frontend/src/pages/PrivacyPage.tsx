import { Link } from 'react-router-dom';
import { Card, CardBody } from '@/components/ui/Primitives';

function Heading({ children }: { children: React.ReactNode }) {
  return <h2 className="mt-10 text-xl first:mt-0">{children}</h2>;
}

export function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1>Privacy and data handling</h1>
      <p className="mt-3 text-ink-600">
        A resume contains your full name, contact details, and employment history. This page states
        exactly what ResumeIQ does and does not keep. It describes the behaviour of the software,
        not a legal policy.
      </p>

      <Card className="mt-8">
        <CardBody className="prose-sm max-w-none space-y-3 text-sm leading-relaxed text-ink-700">
          <p className="font-semibold text-ink-900">The short version</p>
          <ul className="list-disc space-y-1.5 pl-5">
            <li>Your PDF is never written to disk or stored in a database.</li>
            <li>
              The text extracted from it is not stored either, unless you opt in per analysis.
            </li>
            <li>The AI provider receives derived findings, never your resume or your identity.</li>
            <li>You can delete any analysis, or your whole account, at any time.</li>
          </ul>
        </CardBody>
      </Card>

      <div className="mt-4 space-y-1 text-ink-700">
        <Heading>What happens to your resume file</Heading>
        <p className="leading-relaxed">
          When you upload a PDF, it is held in the server&apos;s memory just long enough to validate
          it and extract its text. It is then discarded. There is no upload directory, no object
          storage bucket, and no database column anywhere in the application capable of holding a
          file. That is a property of the schema, not a policy decision that could be quietly
          reversed.
        </p>

        <Heading>What is stored</Heading>
        <p className="leading-relaxed">
          When you run an analysis, the following is saved to your account:
        </p>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 leading-relaxed">
          <li>The overall score and the eight category scores, with their explanations.</li>
          <li>Which required and preferred skills matched, partially matched, or were missing.</li>
          <li>
            A short excerpt (up to 240 characters) showing where each matched skill was found. This
            exists so a claimed match is verifiable rather than asserted.
          </li>
          <li>Which resume sections were detected.</li>
          <li>
            The specific statements flagged as weak — up to 30 of them — because the results page
            has to show them back to you for the feedback to be usable.
          </li>
          <li>The job description you pasted. This is employer content, not your personal data.</li>
          <li>
            The recommendations produced, labelled by whether they came from rules or from AI.
          </li>
          <li>Your name, email address, and a bcrypt hash of your password.</li>
        </ul>

        <Heading>What is not stored</Heading>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 leading-relaxed">
          <li>The PDF file itself.</li>
          <li>
            The full extracted text — unless you tick the opt-in box when running an analysis. That
            box is off by default. The database enforces the rule with a constraint, so text cannot
            exist for an analysis where you did not opt in.
          </li>
          <li>Your password in any readable form.</li>
          <li>Resume content, job description content, or email addresses in application logs.</li>
        </ul>

        <Heading>What the AI service receives</Heading>
        <p className="leading-relaxed">
          When an AI provider is configured, it receives a bounded summary assembled from the
          analysis results: matched and missing skill names, the text of statements already flagged
          by the rule engine, which sections are absent, and the job title.
        </p>
        <p className="mt-2 leading-relaxed">
          It does <strong>not</strong> receive the PDF, the full resume text, your name, your email
          address, your phone number, or your address. The prompt is built from the analysis output,
          not from the document.
        </p>
        <p className="mt-2 leading-relaxed">
          The AI is instructed never to invent an employer, qualification, certification,
          achievement, or figure. Its output is validated against a strict schema before it is
          stored, and discarded if it does not conform. If no provider is configured, the analysis
          runs exactly as normal without it.
        </p>

        <Heading>How your data is protected</Heading>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 leading-relaxed">
          <li>Passwords are hashed with bcrypt. They are never stored, logged, or returned.</li>
          <li>
            Session refresh tokens are stored as SHA-256 hashes, so a database leak would not yield
            usable sessions.
          </li>
          <li>
            Every analysis query filters on the owner. Requesting an analysis belonging to another
            account returns &ldquo;not found&rdquo;, which does not even confirm that the record
            exists.
          </li>
          <li>All traffic is served over HTTPS.</li>
        </ul>

        <Heading>Deleting your data</Heading>
        <p className="leading-relaxed">
          Deleting an analysis removes it and every associated record immediately — scores, skill
          matches, sections, statements, recommendations, and the job description. Deleting your
          account removes your user record and cascades to every analysis you have ever run. Neither
          is a soft delete or a flag; the rows are gone.
        </p>

        <Heading>Known limitations</Heading>
        <p className="leading-relaxed">
          This is a portfolio project, and it is worth being direct about what that means:
        </p>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 leading-relaxed">
          <li>No third-party penetration test or security audit has been performed.</li>
          <li>There is no compliance certification of any kind.</li>
          <li>
            Email addresses are not verified, so someone could register with an address they do not
            control.
          </li>
          <li>There is no multi-factor authentication.</li>
          <li>Backups are whatever the hosting provider&apos;s free tier offers.</li>
          <li>
            Please do not upload another person&apos;s resume without their knowledge and consent.
          </li>
        </ul>
      </div>

      <p className="mt-10 text-sm text-ink-600">
        <Link to="/" className="font-medium text-brand-700 underline underline-offset-2">
          Back to the home page
        </Link>
      </p>
    </div>
  );
}
