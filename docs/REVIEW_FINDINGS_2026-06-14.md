# Independent review findings — Guide #4 "Working with AI" (2026-06-14)

Replicates the #1–3 completion gate: three **independent** reviewers, each a distinct lens, run over
all 13 chapters (`src/content/working-with-ai/00…12`), the 13 ScenarioQuiz demos (`src/data/*_demo.json`),
and the companion artifacts (`companion/working-with-ai/`). Reviewers were blind to each other.

## Verdict

**0 BLOCKERS across all three reviewers.** Guide is factually disciplined, the demos are honest, and the
argument is coherent. All MAJOR and MINOR findings fixed; selected nits applied. Build green after fixes:
58 pages, validate 53 chapters, no errors; LOS↔anchor bijective in all 13; every demo `correct∈candidates`.

Counts: **Facts** 0B/3M/2m/2n · **Demo integrity** 0B/2M/2m/2n · **Pedagogy & continuity** 0B/2M/2m/2n.

## Findings & resolutions

### A. Factual accuracy (reviewer 1)
- **M1 — overgeneralization (Ch 0):** "a majority of new code at large shops is AI-generated" — sources
  support only the Google-specific ~75%. **FIXED:** rewritten to "AI-generated code is a large and growing
  share of new code at major shops (Google reported ~75% internally in 2026 — a figure that will date)."
- **M2 — dangling "see the callout below" + un-quarantined stat (Ch 0):** the promised callout never
  existed; volatile ~75% sat in body prose against the durability policy. **FIXED:** removed the dangling
  pointer; the stat is now hedged + time-stamped inline. (Independently flagged by reviewer 3 as m1.)
- **M3 — "frontier employer" mis-cites Meta (Ch 0):** the "rely solely on prompting → you fail" quote is
  Meta's, and Meta is "big tech," not a frontier lab (the guide's own Industry-variation sections agree).
  **FIXED:** "a reported quote from how one major employer (Meta's AI-assisted round) describes its bar."
- **m1 — "documented rubrics … name four things" (Ch 1):** the 4 dims are a synthesis across the trend, not
  three published rubrics. **FIXED:** "Across the documented AI-assisted rounds (Meta, Google, Canva), four
  things are consistently assessed."
- **n1/n2 (nits):** "pilot" vs "round" for Google; frontier "ban AI" rests on DeepMind. Left as-is — already
  hedged ("some rounds"); acceptable per reviewer.
- **Confirmed sound:** the four dims, communication = #1 rejection (~40–45%), clarification = #2 failure,
  "preregistration not prompt theater," the Canva quote, and the correctly-omitted unverified 68% stat.

### B. Demo integrity (reviewer 2)
- **M1 — `interview_signal/reread-to-answer`:** Comprehension vs Communication distractor too close.
  **FIXED:** sharpened the scenario so comprehension is unambiguously the miss (candidate now answers
  *uncertainly/wrong* after re-reading: "it returns 0… no — it'd throw").
- **M2 — `myths/velocity`:** "is negative value" overstated as a flat claim. **FIXED:** "isn't value — it's
  deferred risk; …" (softened, matches the chapter's framing).
- **m1 — `interview_signal/polished-wrong-target` label:** correct in context (clarification→Trade-off per
  Ch 1 table). No change.
- **m2 — `agentic/cant-read-all` vs `evaluating/code-at-scale` share the "14 files" scenario.** **FIXED:**
  the evaluating item now reads "across many files; you've already reviewed the seams (Ch 9)" so it visibly
  *stacks* on Ch 9 rather than competing.
- **Nits:** the "no question needed" 4th-distractor pattern (predictable) and one purposeful strawman — left
  as-is (pedagogically defensible per reviewer). All 39 items: `correct∈candidates`, no fabricated model output.

### C. Pedagogy & continuity (reviewer 3)
- **M1 — loop mnemonic drifted (review/run vs read/verify):** stages 4–5 were named "review/run" in Ch 0 +
  Ch 1 + companion but "read/verify" in Ch 9/11/12, never reconciled. **FIXED — standardized on
  "clarify, preregister, prompt, review, run, explain" everywhere**, chosen for **source fidelity**: the
  demand research recommends exactly "clarify→pseudocode→prompt→review→run→explain"
  (`_gather_new_topics` L44). Ch 9/10/11/12 normalized (incl. the capstone walkthrough labels); also fixed a
  stray "narrate" → "explain" (Ch 9). Chapter titles ("Reading", "Verification") stay descriptive; the Ch 0
  table bridges stage→chapter.
- **M2 — undefined "Movements A/B/C" leaked into prose (Ch 1, 8, 9×2):** scaffold terms with no reader-facing
  referent. **FIXED:** replaced with concrete chapter spans (Ch 9 prereq → "Chapters 2–8"; etc.).
- **m1 — Ch 0 dangling callout / 75%:** same as Facts M2. **FIXED** (see A.M2).
- **m2 — `*(weighted)*` tag double-duty** (guide-wide Communication vs per-chapter accent). **FIXED:** added a
  one-sentence convention note in Ch 0's "How this is graded" defining the tag.
- **Nits:** motif repetition (cohesive, kept); Ch 1/12 sector ordering (intentional, kept).
- **Confirmed sound:** §5 shape 13/13, Next-chain + prerequisites flawless, anti-pattern↔loop-stage mapping,
  rubric per-chapter accents non-contradictory, cross-references accurate, companion coherent.

## Method note

Reviewers ran in parallel via independent subagents; findings synthesized, deduped (the Ch 0 callout issue
surfaced independently in A and C — high confidence), and applied here. Re-verified after fixes: 0 residual
"read, verify" enumerations, 0 "Movement" in prose, 0 of the three Ch 0 phrases, build + validate green.
