# Preregistration template

> Fill this in **before** your first prompt. The point (Ch 3) is to commit the standard before you see
> the AI's output, so the output is gated against it instead of becoming it. Copy this file per task.

## Task

_One-sentence statement of what you're building._

## Clarify (Ch 2) — the pivots

- **Pivotal term(s):** _the word(s) the whole solution turns on (e.g. "duplicate", "recent", "valid")._
- **Resolved as:** _your confirmed or assumed meaning._
- **Un-answerable assumptions (narrated):** _what you assumed because you couldn't ask, kept swappable._

## Shape

- **Interface / signature:** _e.g. `merge(ranges: list[Range]) -> list[Range]`._
- **Files / units touched:** _the skeleton; for multi-file work, the units and their seams (Ch 9)._

## Invariants (must always hold)

1. _e.g. empty input → empty output (no crash)._
2. _e.g. output is sorted / disjoint / idempotent._
3. _e.g. the property that guards the failure the happy path hides._

## Boundary tests (write them now, from the spec — not after seeing the code)

| Input | Expected | Why it matters |
|-------|----------|----------------|
| _empty_ | _e.g. `[]`_ | boundary the AI tends to skip |
| _touching / adjacent_ | … | the off-by-one zone |
| _nested / duplicate_ | … | the case the example omits |
| _out-of-order / malformed_ | … | the messy-input reality |

## Constraints (incl. negatives — Ch 4)

- _e.g. standard library only; do not add dependencies._
- _e.g. do not change the public signature._

---

**Check before prompting:** could someone else verify your output using only this file? If not, the
gate is too vague — sharpen the invariants and tests until "right" is unambiguous.
