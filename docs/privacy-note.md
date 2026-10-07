# Privacy note

Children's educational practice data is a sensitive, regulated category.
In the United States it sits alongside COPPA-adjacent concerns (data
collected from or about children under 13) and, depending on the
partner's context, FERPA (education records) considerations as well.
Even when a specific regulation doesn't apply directly to a given
deployment, the underlying ethical bar is the same: this is data about a
child's learning struggles and progress, generated in a context (school
or tutoring) where the child did not meaningfully choose to be profiled,
and it deserves to be treated more carefully than generic product
analytics.

## What this scaffold actually does

- **This project runs entirely on synthetic data.** The only data
  generator in this repository, `scripts/gen_synthetic_sessions.py`,
  produces fabricated student IDs, fabricated practice items, and
  fabricated performance patterns. No real student, no real ed-tech
  partner, and no real practice session is referenced anywhere in this
  codebase.
- The example vendor adapter (`app/adapters/example_vendor.py`) is
  written against an illustrative, made-up raw payload shape for a
  hypothetical "ExampleVendor" -- it does not correspond to any real
  vendor's actual API or data format.
- The API-key authentication in `app/core/security.py` is a minimal
  placeholder appropriate for a portfolio scaffold, not a production
  authentication/authorization system.

## What a real deployment would need that this scaffold does not attempt

This is a deliberately narrow scaffold, and privacy engineering is one of
the things deliberately left out of scope. A real deployment handling
actual student data would need, at minimum:

- **Data minimization and retention limits** -- deciding how long raw
  session data and generated notes are kept, and deleting them on a
  schedule rather than indefinitely.
- **Encryption at rest and in transit** for both the raw practice data
  ingested from partners and the `generated_reports` table.
- **Per-partner data isolation and access control** -- today's API-key
  check only authenticates a request; a real system needs to guarantee
  one partner's API key can never retrieve another partner's students'
  reports.
- **A real consent and data-processing agreement framework** with each
  ed-tech partner, since ProgressNote would be a data processor acting on
  behalf of partners who are themselves subject to COPPA/FERPA/state
  student-privacy laws.
- **Audit logging** of who accessed which student's data and when.
- **A defined incident-response process** for a data breach involving
  children's data, which typically carries stricter notification
  requirements than general consumer data.
- **Legal review** specific to each jurisdiction the partner operates in
  -- privacy law for children's educational data varies meaningfully by
  state and country, and this note is not a substitute for that review.

None of the above is implemented here. Treat this repository as an
architecture and code scaffold demonstrating the factuality-guard design
pattern, not as something ready to process real student data.
