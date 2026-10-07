# ProgressNote

A B2B API that ed-tech and tutoring platforms call with a student's
structured weekly practice data, and get back a plain-English "what a
good tutor would tell the parent" note plus a recommended next-session
focus.

This is **not** a tutoring app and it is **not** a chatbot. It is
infrastructure: a narrow, well-typed service that a platform's backend
calls once a week per student, and that returns a note their product can
show a parent as-is.

## The problem

Most ed-tech and tutoring apps already collect rich per-item practice
telemetry -- which questions a kid got right, how long each answer took,
which skill it was testing. Almost none of that data reaches the parent
in a useful form. What parents actually see is usually a bare accuracy
percentage or a streak counter, which tells them *that* something is
happening but not *what to do about it*. A human tutor, looking at the
same data, would say something like: "Blends are clicking now -- great
week. Subtraction is still not sticking after three sessions in a row,
so let's slow down there next time." That synthesis is valuable and
currently rare, because:

- Writing tutor-quality notes at scale requires hiring curriculum writers
  or tutors to review data by hand, which does not scale past a small
  number of students.
- Naively pointing an LLM at raw practice logs is fast to build but
  fragile to trust: a model can misread a raw log, round a number
  wrong, or reference an item that does not mean what it looks like it
  means -- and a single hallucinated specific detail in a note about
  someone's child destroys parent trust in the product immediately.

ProgressNote is built around a stronger claim: **the factuality
discipline is the product, not the prose.** An LLM (or, in the default
configuration of this scaffold, no LLM at all) should never see raw
session logs. It should only ever see a pre-computed, structured summary,
and every claim in the generated note must be traceable back to a field
in that structured summary. If it isn't, the note is rejected before it
reaches a parent.

### Why a parent can't just "ask ChatGPT"

The obvious objection is: if an LLM can write the note, why not skip the
whole pipeline and have the parent (or the ed-tech company) paste the
data into a chatbot? Two reasons:

1. **Parents don't have the data.** A student's raw per-item practice
   telemetry lives inside the vendor's own systems -- it is not
   something a parent can export, and most ed-tech companies would not
   want to hand it to a parent unfiltered even if they could (kids'
   practice data is a sensitive category; see `docs/privacy-note.md`).
   The value ProgressNote provides to the *platform* is a codified
   feature-extraction rubric it can call as an API, not a prompt a
   parent could type themselves.
2. **The hard part isn't the phrasing, it's the rubric.** "What counts as
   newly mastered? What counts as stuck? How do you tell fatigue from a
   hard skill?" are curriculum-design questions with real, debatable
   answers. ProgressNote answers them once, in deterministic Python
   (`app/features/`), so every note -- LLM-written or not -- is grounded
   in the same rules. A prompt alone can't encode that; a raw LLM call
   would re-derive (and likely get subtly wrong) these judgments on every
   request.

## Architecture overview

```
vendor raw export
      |
      v
  SessionAdapter (app/adapters/)         -- maps vendor shape -> canonical schema
      |
      v
  WeeklyReportRequest (app/schemas/practice.py)   -- canonical input contract
      |
      v
  feature layer (app/features/)          -- pure, deterministic, non-LLM
      |                                      mastery / plateau / fluency / engagement
      v
  StructuredSummary (app/features/summarize.py)   -- the ONLY thing a note
      |                                               generator is allowed to see
      v
  NoteGenerator (app/notegen/)
      |    TemplateNoteGenerator  -- rule-based, zero dependencies, default
      |    LLMNoteGenerator       -- prompt built ONLY from StructuredSummary
      v
  factuality guard (app/notegen/factuality.py)    -- verifies every claim in
      |                                               the note traces to the summary
      v
  POST /v1/reports/weekly response
  { parent_note, next_focus, confidence, factuality_passed }
```

See `docs/architecture.md` for a fuller diagram and `docs/adr/0001-*.md`
for the reasoning behind the structured-summary boundary.

## Project layout

```
app/
  schemas/practice.py     canonical Pydantic v2 input contract
  adapters/                vendor raw-shape -> canonical-schema mapping
  features/                deterministic feature extraction (the centerpiece)
  notegen/                 template + LLM note generators, factuality guard
  api/v1/router.py         POST /v1/reports/weekly
  core/                    config + API-key auth
  db/                      SQLAlchemy async models + session factory
migrations/                Alembic, configured for async SQLAlchemy
scripts/gen_synthetic_sessions.py   synthetic demo data generator
docs/                       architecture, ADRs, privacy note
tests/                      pytest tests for the feature layer
```

## Setup (not yet executed)

This project was scaffolded without running, building, or installing
anything. The commands below are what *would* be run to actually stand it
up -- none of them have been executed yet, and nothing has been verified
to run.

```bash
# Install dependencies (declared in pyproject.toml, never installed here)
uv sync

# Start Postgres (and the API, once the Dockerfile/compose file are verified)
docker compose up -d db

# Apply the database migration
alembic upgrade head

# Run the API locally
uvicorn app.main:app --reload

# Generate a synthetic demo request
python scripts/gen_synthetic_sessions.py > sample_request.json

# Call the API (example)
curl -X POST http://localhost:8000/v1/reports/weekly \
  -H "X-API-Key: dev-local-key" \
  -H "Content-Type: application/json" \
  -d @sample_request.json

# Run tests
pytest
```

## Scope, deliberately

- One example vendor adapter (`app/adapters/example_vendor.py`), not a
  marketplace of integrations.
- `TemplateNoteGenerator` is the only generator guaranteed to produce a
  note with zero external calls; it is what's wired into the API by
  default.
- `LLMNoteGenerator` is real, complete interface and prompt-construction
  code, but it is never invoked in this scaffold -- no API key, no
  network call, nothing to run.
- All demo data comes from `scripts/gen_synthetic_sessions.py`. No real
  student data is used or referenced anywhere in this repository.
