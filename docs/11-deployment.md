# RM0 deployment runbook

15 October 2026. Use the current status in [release readiness](10-release-readiness.md); configuration files alone do not prove deployment.

## Scope and cost gate

Use only ResumeIQ resources and the existing Neon `resumeiq-prod`, production branch, Singapore. Inspect existing resources first; do not duplicate them or modify SCAMGUARD/shared billing settings. Never add a card, paid disk/database/compute, purchased domain or billable AI.

Account inspection found Vercel Hobby and Render Hobby with **no card on file**, $0 current/projected charges, 3.93/750 shared free instance hours, 4 MB/5 GB bandwidth and 0/500 pipeline minutes. These quotas are shared with the existing SCAMGUARD service. After deployment, Render still showed no card and $0 current/projected charges (4.27/750 hours). Neon `resumeiq-prod` / production / Singapore / `neondb` was verified Free with no expiration; a read-only query confirmed zero application tables before initial migration and nine afterwards.

[Render Free documentation](https://render.com/docs/free) confirms 750 shared monthly hours, sleep after 15 minutes, roughly one-minute wake-up, suspension on exhausted hours, and suspension/build disabling instead of overage billing without a payment method. Do not use keep-alive pings. [Vercel Hobby](https://vercel.com/docs/plans/hobby) is personal/non-commercial with finite included usage. [Neon Free](https://neon.com/pricing) has finite compute/storage/transfer limits and scale-to-zero. Recheck provider/account conditions before future changes.

## Database before mutation

Verify exact project/branch/region/database/role and table inventory without exposing records or credentials. Only an independently verified new empty ResumeIQ database is authorized for automatic bootstrap. Do not reset branches, drop cloud tables or run production downgrades.

Use `postgresql+psycopg` and TLS. Runtime may use a pooled Neon hostname; migrations use a direct hostname. Keep URLs in provider secrets. Set `EXPECTED_DATABASE_HOST` and `EXPECTED_DATABASE_NAME` from the verified direct target. Enable `ALLOW_EMPTY_DATABASE_BOOTSTRAP=true` only for the verified first migration, then disable it. Startup takes a PostgreSQL session advisory lock, upgrades Alembic, and fails closed on errors.

## Backend

`render.yaml`: Docker, root `backend`, Free, Singapore, `main`, manual deploy. This file is a configuration template: reuse the existing ResumeIQ service and do not reapply it to create another service or regenerate its JWT secret. Preserve existing private settings during a branch transition. Production requires debug false, verified DB secrets, exact frontend HTTPS origins, and AI opt-in false with no AI key/model. Never run `seed_demo` in production. One Uvicorn worker binds Render's `PORT`.

## Frontend and sessions

Vercel root `frontend`, Vite, `npm ci`, `npm run build`, output `dist`, API base `/api/v1`. After observing the actual Render URL, run `node scripts/configure-hosting.mjs <verified-https-render-origin>` from `frontend`, review and commit its public routing config. The generator accepts only a plain HTTPS onrender.com origin. The committed `vercel.json` now forwards to the observed `https://resumeiq-api-zqip.onrender.com` service. Generated rewrites route API before SPA fallback, with no-store and frontend security headers.

Use same-origin proxying for host-only HttpOnly/Secure/Lax refresh cookies. Do not add wildcard or guessed preview CORS origins.

## Deployed resources

- Frontend: https://resumeiq-lemon-eight.vercel.app (Vercel Hobby, Node 22, root `frontend`, `npm ci`, `npm run build`, `dist`).
- API: https://resumeiq-api-zqip.onrender.com (Render Free, Docker, Singapore, one worker, manual deployments).
- Neon: existing `resumeiq-prod`, production, AWS Singapore, PostgreSQL 18, `neondb`, migration `0004`, nine application tables.
- Exact allowed Origin: `https://resumeiq-lemon-eight.vercel.app`. No wildcard preview origins.
- Vercel production branch tracks `codex/resumeiq-portfolio-release`. Its initial main-branch import was intentionally build-blocked and never published.
- First empty-database bootstrap completed; `ALLOW_EMPTY_DATABASE_BOOTSTRAP=false` was saved and applied on the next successful deployment.
- Secrets exist only in private Render settings; no AI key/model is configured. No card, disk or paid add-on was added.

## Public acceptance

Verify health/HTTPS, plans/regions/cost, synthetic registration/login/reload, refresh flags and rotation/replay/logout, fictional PDF and saved history, correct Neon persistence, profile/password invalidation, two-user isolation, deletion/cascades, no-store/error/Origin/resource limits, AI off, keyboard/mobile usability and recovery after natural idle. Never pay for uptime or defeat sleeping. Record actual URLs only after observing them. Keep main unmerged until explicit approval.

## Post-merge transition — prepared, not executed

16 October 2026: the owner explicitly authorized this transition. The README badge and `render.yaml` changes in step 2 are prepared on the feature branch before merging; completion and deployed revisions remain subject to verified CI and provider evidence.

Do not perform these steps until the owner explicitly approves merging PR #1. The current production branch remains `codex/resumeiq-portfolio-release` on both providers.

1. Fetch GitHub and confirm PR #1 is still open, its approved head has all four CI jobs green, and no unexpected commits have appeared. Merge that approved PR into `main` using the repository's permitted merge method. Record the resulting main SHA; a squash merge will have a different SHA from the feature head.
2. On `main`, update the README CI badge query to `branch=main`, replace the pre-merge deployment wording, and change the branch in `render.yaml` to `main`. Commit these release metadata/configuration changes through the approved workflow and wait for CI. Do not delete the feature branch until deployment verification is complete.
3. In Vercel, open the existing `tayyab-d919 / resumeiq` project → Settings → Environments → Production → Branch Tracking. Change the matching branch to `main`. Keep the existing project, root `frontend`, Vite preset, Node 22, `npm ci`, `npm run build`, `dist`, rewrites and domain. Confirm a Ready production deployment for the approved main SHA; if branch configuration alone does not create one, deploy that main revision explicitly in the same project. Do not promote the old failed main import.
4. In Render, open the existing `resumeiq-api` service (`srv-db86mulg1s2s7398dkfg`) → Settings → Build → Branch → Edit, select `main`, and save. Keep Auto-Deploy off. Use Manual Deploy for the verified main revision and confirm the service's deployed SHA and Live status. Keep Free compute, Singapore, root `backend`, Docker settings, one worker and `/api/v1/health` unchanged.
5. Retain the existing Neon `resumeiq-prod` / production / `neondb`. Keep the pooled runtime URL, direct migration URL, expected database identity, JWT secret and exact CORS origin unchanged. Keep `ALLOW_EMPTY_DATABASE_BOOTSTRAP=false` and AI disabled. Startup may run forward migrations under its advisory lock; never reset, drop or downgrade the cloud database.
6. Set the GitHub repository About website to `https://resumeiq-lemon-eight.vercel.app`. Verify the main CI badge and README links. No other repository or hosting service is part of this transition.
7. Verify both HTTPS health paths, landing/sample/deep links, fictional login/reload, PDF upload, saved report, JSON download and logout. Confirm application persistence across the backend deployment and clean up only newly created fictional test data. Record main SHA, Vercel deployment and Render deployment in release readiness.

Stable URLs remain `https://resumeiq-lemon-eight.vercel.app`, `/sample`, and `https://resumeiq-api-zqip.onrender.com/api/v1/health`. No project recreation, new domain, database copy, credential rotation or paid resource is required.

Possible interruptions: Vercel may skip a deployment when its configured source directory is unchanged, so verify the resulting revision; Render manual deployment is required while Auto-Deploy is off; free build/hour/transfer quotas can block deployment; Render sleep and Neon scale-to-zero add latency; old browser tabs may need a reload after lazy JavaScript chunks are replaced. Changing branch tracking before merging would expose the old main code and is prohibited.

Current final-verification snapshot (15 October 2026): Render still shows Hobby/Free, no card and $0 current/projected charges, with 7.15/750 shared hours, 7 MB/5 GB transfer and 2/500 pipeline minutes. Neon shows Free, no branch expiration, 0.81 CU-hours, 32.57 MB storage and 535.11 kB transfer. Vercel remains Hobby; its usage page showed 14.4 MB/100 GB transfer and 541/1,000,000 CDN requests in the displayed last-30-days period. These dated counters can lag and are not capacity or availability guarantees.
