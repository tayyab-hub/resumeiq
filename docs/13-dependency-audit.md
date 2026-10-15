# Dependency audit evidence — 15 October 2026

The original `main` lockfile was audited without installing its packages. It returned exit code 1 with 17 affected packages: two critical, ten high and five moderate. Counts include transitive propagation, not 17 independent exploitable application defects. Current locked dependencies pass both all-package and production-only npm audits and pip-audit in CI.

## JavaScript packages

Versions below come from the original and release lockfiles. Removed packages are no longer in the dependency tree. Direct/transitive describes the original manifest. Runtime means shipped browser dependencies, not a server-side Node execution path.

| Package | Original version(s) | Release version(s) | Severity | Relationship / scope | Advisory or vulnerable dependency |
|---|---|---|---|---|---|
| @vitest/mocker | 3.2.7 | 5.0.4 | moderate | transitive / build/test | [GHSA-82fw-gwwq-j7x9](https://github.com/advisories/GHSA-82fw-gwwq-j7x9) |
| axios | 1.18.1 | 1.20.0 | high | direct / browser runtime | [GHSA-vh66-26gq-q6x8](https://github.com/advisories/GHSA-vh66-26gq-q6x8), [GHSA-9fr6-4gfg-395g](https://github.com/advisories/GHSA-9fr6-4gfg-395g), [GHSA-c29m-xwm3-cm6r](https://github.com/advisories/GHSA-c29m-xwm3-cm6r), [GHSA-mghh-pgcx-3jjj](https://github.com/advisories/GHSA-mghh-pgcx-3jjj), [GHSA-x97p-jq2g-jp4f](https://github.com/advisories/GHSA-x97p-jq2g-jp4f), [GHSA-3pq3-5fj3-cg6v](https://github.com/advisories/GHSA-3pq3-5fj3-cg6v), [GHSA-542g-h47m-68v8](https://github.com/advisories/GHSA-542g-h47m-68v8), [GHSA-j8rh-479h-cp32](https://github.com/advisories/GHSA-j8rh-479h-cp32), [GHSA-4hqw-qxg8-jxx2](https://github.com/advisories/GHSA-4hqw-qxg8-jxx2), [GHSA-m8m8-qj5v-23w3](https://github.com/advisories/GHSA-m8m8-qj5v-23w3), [GHSA-44g4-m2mj-wpvx](https://github.com/advisories/GHSA-44g4-m2mj-wpvx), [GHSA-r4gj-5m52-g5wh](https://github.com/advisories/GHSA-r4gj-5m52-g5wh) |
| brace-expansion | 1.1.16, 5.0.8 | 1.1.21, 5.0.12 | high | transitive / build/test | [GHSA-mh99-v99m-4gvg](https://github.com/advisories/GHSA-mh99-v99m-4gvg), [GHSA-rgw5-rvv9-x895](https://github.com/advisories/GHSA-rgw5-rvv9-x895), [GHSA-q2hr-2g5m-vwhr](https://github.com/advisories/GHSA-q2hr-2g5m-vwhr), [GHSA-qhr7-859c-m2p7](https://github.com/advisories/GHSA-qhr7-859c-m2p7), [GHSA-6j4f-fj2g-mc7p](https://github.com/advisories/GHSA-6j4f-fj2g-mc7p) |
| braces | 3.0.3 | removed | high | transitive / build/test | [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) |
| chokidar | 3.6.0 | removed | high | transitive / build/test | braces |
| fast-glob | 3.3.3 | removed | high | transitive / build/test | micromatch |
| js-yaml | 4.3.0 | 4.3.2 | high | transitive / build/test | [GHSA-5p4m-2wfm-xmqj](https://github.com/advisories/GHSA-5p4m-2wfm-xmqj), [GHSA-2883-xcg3-v3hh](https://github.com/advisories/GHSA-2883-xcg3-v3hh) |
| micromatch | 4.0.8 | removed | high | transitive / build/test | braces |
| nanoid | 3.3.16 | 3.3.20 | high | transitive / build/test | [GHSA-2v37-7h3g-55p8](https://github.com/advisories/GHSA-2v37-7h3g-55p8) |
| postcss-nested | 6.2.0 | removed | moderate | transitive / build/test | postcss-selector-parser |
| postcss-selector-parser | 6.1.4 | removed | moderate | transitive / build/test | [GHSA-rj75-hqrm-r3gf](https://github.com/advisories/GHSA-rj75-hqrm-r3gf) |
| react-router | 6.30.4 | 7.18.4 | moderate | transitive / browser runtime | [GHSA-wrjc-x8rr-h8h6](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6), [GHSA-337j-9hxr-rhxg](https://github.com/advisories/GHSA-337j-9hxr-rhxg) |
| react-router-dom | 6.30.4 | 7.18.4 | moderate | direct / browser runtime | [GHSA-jjmj-jmhj-qwj2](https://github.com/advisories/GHSA-jjmj-jmhj-qwj2), react-router |
| source-map-js | 1.2.1 | 1.2.2 | high | transitive / build/test | [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q) |
| tailwindcss | 3.4.19 | 4.3.3 | high | direct / build/test | chokidar, fast-glob, micromatch, postcss-nested, postcss-selector-parser |
| tinypool | 1.1.1 | removed | critical | transitive / build/test | [GHSA-5gmw-xhrv-c9v3](https://github.com/advisories/GHSA-5gmw-xhrv-c9v3), [GHSA-85c8-ppgw-ccpr](https://github.com/advisories/GHSA-85c8-ppgw-ccpr) |
| vitest | 3.2.7 | 5.0.4 | critical | direct / build/test | @vitest/mocker, [GHSA-82fw-gwwq-j7x9](https://github.com/advisories/GHSA-82fw-gwwq-j7x9), tinypool |

## Reachability and upgrade decisions

- Axios is used for browser requests to a fixed relative API path. Its Node HTTP/HTTP2/proxy and data-URI adapter advisories are not exercised by that deployment path; prototype-pollution-related behavior still warranted updating. No successful exploit was demonstrated.
- React Router runs as a client-side SPA, with no SSR hydration endpoint. Navigation/redirect handling remains relevant; the router was upgraded and login/deep-link/reload behavior tested.
- Vite/Vitest/Tailwind and their watcher/glob/worker/CSS dependencies run in development or CI. They are not deployed as public development/test servers. Their attack surface includes untrusted source/test/config input in a build environment, so the dependency tree was upgraded rather than exempted.
- Compatible upgrades were grouped and lockfile installs retained. Vite 8, Vitest 5 and Tailwind 4 required configuration/CSS changes; TypeScript, ESLint, formatting, 52 frontend tests, production builds, real browser views and Docker builds passed. No blanket audit suppression or `audit fix --force` was used.

## Python packages

The saved baseline audit contained 18 advisory entries across three packages, including duplicate pip/pytest identifiers from its advisory feeds. These are recorded as returned; duplicates are not independent vulnerabilities. pip-audit did not supply a comparable severity classification for every entry.

| Package | Baseline | Release | Scope | Unique advisory IDs |
|---|---|---|---|---|
| pip | 26.1.2 | 26.2.1 | development/build tooling | `PYSEC-2026-3721` |
| pyjwt | 2.13.0 | 2.15.1 | JWT runtime | `PYSEC-2026-4140`, `PYSEC-2026-4141`, `PYSEC-2026-4142`, `PYSEC-2026-4143`, `PYSEC-2026-4144`, `PYSEC-2026-4145`, `PYSEC-2026-4146`, `PYSEC-2026-4147`, `PYSEC-2026-4148`, `PYSEC-2026-4149`, `PYSEC-2026-4150`, `PYSEC-2026-4151`, `PYSEC-2026-4152`, `PYSEC-2026-4183` |
| pytest | 8.4.2 | 9.1.1 | development/build tooling | `PYSEC-2026-1845` |

PyJWT is directly used for authentication; explicit algorithm/expiry/type validation and session-version checks are tested. The baseline advisories were treated as applicable dependency risk rather than presumed exploitable, and the current release was verified by full authentication tests. pip and pytest operate during installation/testing; neither exposes an application route. Hash-locked production/development requirements and Linux Docker/CI installs verify compatibility.

Residual risk: audit databases evolve, zero reported findings do not prove safety, and parser/logic defects can exist without advisories. No exception or ignored advisory is configured.
