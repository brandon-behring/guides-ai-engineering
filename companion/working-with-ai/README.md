# Working with AI — companion (workflow artifacts)

Guide #4 ("Working with AI") teaches a **practice**, not a system, so its companion is **workflow
artifacts**, not a Python package like `mini_eval` / `mini_rag` / `mini_agent` / `mini_prod`. These are
the three things you fill in and reuse on real AI-assisted work — the loop made portable:

- [`preregistration.md`](./preregistration.md) — commit the target *before* you prompt (Ch 3). The
  shape, the invariants, the boundary tests. Copy it per task; fill it in before the first prompt.
- [`loop-checklist.md`](./loop-checklist.md) — the six-stage loop as a runnable checklist (Ch 0, 2–7):
  clarify → preregister → prompt → review → run → explain.
- [`review-rubric.md`](./review-rubric.md) — the four-dimension rubric operationalized as a self-grading
  sheet (Ch 1, 12). Score your own AI-assisted attempt the way an interviewer would.

**For learning, not production tooling.** The point is to internalize the loop until it's automatic;
once it is, you won't need the templates — you'll be doing them by reflex. Use them as scaffolding and
let them fall away (Ch 12: rehearse until the loop survives pressure).
