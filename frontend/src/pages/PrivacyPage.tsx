import { Link } from 'react-router-dom';
import { Card, CardBody } from '@/components/ui/Primitives';

export function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-14 sm:px-6">
      <div>
        <h1>Privacy and data handling</h1>
        <p className="mt-3 text-ink-600">
          Understand what you share before uploading. This is a student portfolio demo; you can
          explore the fictional sample without submitting personal information.
        </p>
        <Link to="/sample" className="mt-4 inline-block font-medium text-brand-700 underline">
          Explore Sample Analysis
        </Link>
      </div>
      <Card>
        <CardBody className="space-y-3 text-sm leading-relaxed">
          <h2 className="text-xl">Your PDF is temporary</h2>
          <p>
            Uploads may be buffered in memory or in a temporary file by the web framework. Temporary
            upload files are closed after processing. ResumeIQ does not save the original PDF in its
            database or object storage.
          </p>
          <p>
            Text extraction is limited to 5 MB uploads, 10 pages, 100,000 characters and a 10-second
            processing timeout. Scanned PDFs need a selectable text layer; OCR is not provided.
          </p>
        </CardBody>
      </Card>
      <section className="space-y-3 leading-relaxed">
        <h2>What your account stores</h2>
        <ul className="list-disc space-y-2 pl-5">
          <li>Your name, email and password hash; refresh tokens are stored as hashes.</li>
          <li>Analysis titles, filenames, dates, scores, explanations and recommendations.</li>
          <li>
            Skill evidence excerpts (up to 240 characters each) and up to 30 flagged statements (up
            to 600 characters each). These can contain personal information even when full-text
            storage is off.
          </li>
          <li>
            The job description you paste, including any personal or confidential information it
            contains.
          </li>
          <li>
            Full extracted resume text only when you select the per-analysis opt-in. The database
            enforces that choice.
          </li>
        </ul>
      </section>
      <section className="space-y-3 leading-relaxed">
        <h2>AI is disabled on the free demo</h2>
        <p>
          The complete score and rule-generated advice work without an AI provider. No paid AI
          requests are needed.
        </p>
        <p>
          If the operator explicitly enables AI on a separate deployment, the prompt includes
          curated skill labels, missing-section identifiers, numeric statistics and issue codes. It
          excludes free-form statements, job titles, the PDF and full resume text.
        </p>
        <p>
          AI output is checked for structure and size, not factual truth. Instructions cannot
          guarantee that suggestions will be accurate. Review every suggestion before using it.
        </p>
      </section>
      <section className="space-y-3 leading-relaxed">
        <h2>Sessions and access</h2>
        <p>
          The browser keeps the access token in memory and the refresh token in an HttpOnly cookie.
          Hosted configuration requires HTTPS, an exact website origin and a same-origin API proxy.
          Every private analysis query checks account ownership.
        </p>
        <p>
          Changing your password invalidates existing access and refresh sessions. Signing out
          revokes the current refresh session and clears its cookie; an already copied access token
          can remain valid until its 30-minute expiry.
        </p>
        <p>
          Application logs exclude document bodies, passwords and raw exception messages. Hosting
          providers may retain network and operational logs according to their own policies.
        </p>
      </section>
      <section className="space-y-3 leading-relaxed">
        <h2>Retention and deletion</h2>
        <p>
          Saved records remain until you delete an analysis or your account. Account deletion
          removes the account and associated analyses from the active database. Provider backups may
          retain earlier copies until their retention period expires.
        </p>
        <p>
          There is no email verification, password-recovery service or multi-factor authentication.
          Use a fictional resume to evaluate the demo, and only upload information you are
          authorised to share.
        </p>
      </section>
      <section className="space-y-3 leading-relaxed">
        <h2>Limits of this project</h2>
        <p>
          This project has no independent penetration-test certification. Rate limits are held in
          one server process and reset on restart. Free hosting may sleep, pause or become
          unavailable when its quotas are exhausted. A score does not predict hiring outcomes, and a
          skill not detected is not necessarily a skill you lack.
        </p>
      </section>
      <Link to="/" className="inline-block font-medium text-brand-700 underline">
        Back to home
      </Link>
    </div>
  );
}
