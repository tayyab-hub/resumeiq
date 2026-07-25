# ResumeIQ — Planning Documents

Phase 1 deliverables for **ResumeIQ — AI Resume Analyzer and Job Matching Platform**.
These are living documents: when an implementation decision contradicts one of them, update
the document in the same pull request as the code.

| # | Document | What it settles |
|---|---|---|
| 01 | [Requirements](01-requirements.md) | Problem statement, users, scope, functional (FR-*) and non-functional (NFR-*) requirements, constraints, open decisions |
| 02 | [User stories](02-user-stories.md) | 20 stories with testable acceptance criteria, mapped to requirement IDs |
| 03 | [Architecture](03-architecture.md) | Layering, request flow, data-flow boundaries, technology rationale, deployment, known limitations |
| 04 | [Database design](04-database-design.md) | ERD, eight tables, constraints, indexes, migration plan, representative queries |
| 05 | [API contract](05-api-contract.md) | 17 endpoints, request/response shapes, the complete error-code table, cross-cutting rules |
| 06 | [Scoring methodology](06-scoring-methodology.md) | The published rubric — eight categories, weights, formulas, limitations, worked example |
| 07 | [Security & privacy](07-security-privacy.md) | Threat model, 11 risk controls, data-minimisation plan, security testing checklist |
| 08 | [Testing strategy](08-testing-strategy.md) | Test pyramid, per-module test lists, CI configuration, manual checklist, test-data policy |
| 09 | [Project plan](09-project-plan.md) | 30-day schedule, first 22 GitHub issues, git workflow, risk register, definition of complete |

## Reading order

- **Starting the build?** 09 (schedule) → 03 (architecture) → 04 (database).
- **Implementing a feature?** Find its FR-ID in 01, its story in 02, its endpoint in 05.
- **Writing the scorer?** 06 is the specification; deviating from it is a bug in one of them.
- **Reviewing this project?** 01 §1 for the problem, 06 for the method, 07 §3 for the privacy
  posture, and 03 §11 for what it deliberately does not do.

## Status

| Phase | Status |
|---|---|
| 1 — Requirements, architecture, planning | Awaiting developer review |
| 2–15 | Not started |

## Decisions awaiting confirmation

See `01-requirements.md` §7. Summary: token storage strategy (**D1**), AI provider (**D2**),
résumé-text retention (**D3**), skill taxonomy source (**D4**), required/preferred split
heuristic (**D5**), backend hosting (**D6**).
