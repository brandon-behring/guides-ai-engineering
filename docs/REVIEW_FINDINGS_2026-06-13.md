# Guide #3 (production-ai-systems) — independent review findings (2026-06-13)

Completion-gate review of chapters 1–12 (Ch 0 pre-reviewed), the `mini_prod` companion
(latency · cascade · trace · monitor · drift), the five computed demos, seven hand-authored
`ScenarioQuiz` demos, and the six islands. Three independent fresh-context reviewers, one per
dimension. All findings below are **resolved**.

## Verdicts

| Dimension | Verdict | Findings |
|---|---|---|
| Math + factual correctness | PASS-WITH-FIXES → **resolved** | 1 BLOCKER, 2 SHOULD-FIX, 1 NIT |
| Demo-honesty + island integrity | **PASS** | none (no fabricated output; 21/21 quiz `correct∈candidates`; all islands match JSON; DriftMonitor values ≤0.8) |
| Pedagogy + continuity + MDX | **PASS** | §5 complete ×12; LOS↔anchor bijective ×12; narrative threaded; voice consistent; 2 out-of-scope NITs |

## Findings + resolutions

1. **[BLOCKER] Ch 10 break-even off by 2×.** Prose said swapping to a $0.0006/q open model moved
   the crossover to "~83,000/day," but with the $3,000 GPU held fixed it is
   `3000/30/0.0006 = 166,667/day` (the 83,333 figure is the $1,500 GPU row, never introduced) —
   and it contradicted the chapter's own `break_even_demo.json`. **Fixed:** "~83,000/day" →
   "~167,000/day" (`10-self-host-vs-api.mdx`). The point (the crossover swings hugely with the
   API rate) is now *stronger* — a 10× jump.

2. **[SHOULD-FIX] Ch 7 offline score contradicted its chart.** Prose said the frozen offline set
   "scored a steady 0.92," but the paired `drift_demo.json` offline series (the line the reader
   sees rendered, labelled *groundedness*) is ~0.78 — and 0.92 would render off the island's 0.8
   y-axis. **Fixed:** "0.92" → "~0.78" in both prose lines (`07-drift-and-decay.mdx`). (The 0.92
   golden-set figure in Ch 0 is a different metric — launch task accuracy — and stands.)

3. **[SHOULD-FIX] Mann–Whitney variance omitted the tie correction.** `drift.mann_whitney_u`
   used the untied variance `na·nb·(n+1)/12`; the tests only covered the fully-separated and
   identical extremes, so a near-α tie bug was invisible. **Fixed:** applied the standard tie
   correction to the variance (`Σ(t³−t)` over tie groups), updated the docstring, and added
   `test_mann_whitney_handles_ties` (separated-with-ties → p<0.05; identical-with-ties → p>0.5).
   Reduces to the untied formula when there are no ties; the demos are unaffected (they don't
   call this function). `mini_prod` now 44 tests.

4. **[NIT] Ch 2 "tens of seconds" understated the demo.** The default broken-promo combo's p99 is
   78,004 ms (~78 s). **Fixed:** "tens of seconds" → "over a minute" (`02-latency-anatomy.mdx`).

## Out-of-scope notes (not actioned)

- Ch 0's `provenance.ai_tools` is "Claude Fable 5" / `last_verified: 2026-06-10` (vs Ch 1–12's
  "Claude Opus 4.8" / `2026-06-13`). Ch 0 was authored earlier by a different model; its
  provenance record is accurate as written and is left unchanged.
- MDX-escaped dollars (`\$1,725`) in Ch 4 / Ch 10 are correct (avoids KaTeX `$…$` math parsing)
  and build-verified.

## Post-fix verification

`npm run build` + `book-scaffold validate` clean (40 chapters); LOS↔anchor bijective in all 12;
companion suites green — `mini_eval` 24, `mini_rag` 29, `mini_agent` 12, `mini_prod` 44.
