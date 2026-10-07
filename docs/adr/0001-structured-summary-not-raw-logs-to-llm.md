# ADR 0001: The LLM only ever sees a pre-computed StructuredSummary, never raw session logs

## Status

Accepted.

## Context

ProgressNote's job is to turn a week of a child's practice data into a
short note a parent will read and act on. The obvious, fast way to build
this is: take the raw practice sessions, put them in a prompt, ask an
LLM to summarize them and write the note. That approach is tempting
because it requires almost no feature-engineering work up front.

It is also the wrong architecture for this product, for one specific
reason: **trust in this product is destroyed by a single wrong detail,
and raw-log summarization by an LLM cannot bound the rate of wrong
details.**

Consider what "wrong" looks like here. It is not a stylistic quibble --
it is a parent reading "Jamie got 9 out of 10 blends questions right this
week" when the true number was 7 out of 10, or "subtraction has improved"
when the deterministic data shows three flat sessions in a row. Parents
do not have a way to audit this note against the underlying data (they
do not have access to the raw telemetry -- see `docs/privacy-note.md`).
The note is the only thing they see, so it has to be right, not
"generally in the right direction."

LLMs summarizing long, structured, numeric logs are known to occasionally
misread which number belongs to which entity, round incorrectly, or
generalize past what the data supports ("skill X is improving" from noisy
data that doesn't actually show a trend). None of these failure modes are
exotic adversarial inputs -- they are ordinary behavior for a model doing
free-form summarization of a table it was only shown once. Prompt
engineering ("please be careful with numbers", "double check your work")
reduces the rate but cannot make it zero, and zero is closer to what this
product needs, because a parent forms an opinion about the *product*
(not just that day's note) from a single bad detail.

## Decision

1. **All feature extraction happens in deterministic, non-LLM Python**
   (`app/features/`), before any note is generated. Mastery crossing,
   plateau detection, latency-trend classification, and engagement
   trend are all pure functions of `WeeklyReportRequest` and prior
   history. They are unit-testable and produce the same output every
   time given the same input.

2. **The output of the feature layer, `StructuredSummary`
   (`app/features/summarize.py`), is the only object any `NoteGenerator`
   implementation is allowed to receive.** `NoteGenerator.generate()`
   takes a `StructuredSummary`, not a `WeeklyReportRequest` and not raw
   `PracticeSession`/`PracticeItem` data. This is enforced by the type
   signature, not just convention: there is no code path in
   `app/notegen/` that has a reference to raw session data.

3. **`LLMNoteGenerator` builds its prompt exclusively from
   `StructuredSummary.model_dump()`.** The prompt sent to the model
   contains no session-level detail that isn't already aggregated onto a
   `StructuredSummary` field. If a fact would be useful for the note but
   isn't already computed onto `StructuredSummary`, the fix is to add a
   new deterministic feature function, not to widen what data reaches the
   prompt.

4. **Every generated note -- from any generator -- passes through a
   factuality guard** (`app/notegen/factuality.py`) before being
   returned. The guard extracts skill-area names and numbers mentioned in
   the note text and checks each one against the `StructuredSummary`
   object's own fields. A note that references a skill area or number not
   present anywhere on the summary fails the check, and the caller is
   expected to reject or retry rather than surface it to a parent.

Taken together, these four points mean an LLM (when one is wired in) is
being used strictly as a *phraser* of already-verified facts, not as a
*source* of facts. Its only remaining failure mode is saying something
not backed by the summary at all -- which the factuality guard catches
mechanically, without relying on another LLM's judgment.

## Consequences

**Positive:**
- The system's factual claims are bounded by a small, closed,
  fully-typed object (`StructuredSummary`), which is easy to reason about,
  test, and audit.
- `TemplateNoteGenerator` can produce a fully trustworthy note with zero
  external calls, which is valuable as a fallback when an LLM call fails,
  times out, or fails the factuality check.
- Feature-extraction logic (what counts as "stuck," "mastered," "a
  fluency regression") is centralized and versioned in code, rather than
  re-derived by a model on every request -- so behavior is consistent
  across students and over time.

**Costs / trade-offs:**
- Any new fact the note should be able to state requires adding a new
  deterministic feature function and a new field on `StructuredSummary`
  -- it cannot be added by just tweaking a prompt. This is intentional
  friction: it keeps the "what can the note say" surface area explicit
  and reviewable, at the cost of some development speed.
- The factuality guard's extraction (regex/keyword-based) is
  conservative and can flag phrasing it doesn't recognize as an
  "unverifiable" claim even when a human would consider it fine (e.g. a
  paraphrased number). This scaffold accepts more false rejections in
  exchange for fewer false acceptances -- silently allowing a
  hallucinated child-specific detail through is the failure mode this
  whole architecture exists to prevent.
