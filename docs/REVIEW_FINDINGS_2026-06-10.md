# Independent review — Guide #2 (llm-app-engineering), 2026-06-10

Companion record to `REVIEW_FINDINGS_2026-06-08.md` (guide #1). Same gate, same
method: **three independent reviewer agents with no authoring context**, run
against the complete 13-chapter guide (review scope: ch 02–12; ch 00–01 predate
this round and were reviewed at the guide-2 kickoff). Dimensions covered:
**math/statistics · factual claims · demo honesty · island/MDX integrity ·
pedagogy-shape conformance + narrative continuity.**

## Verdict

**Pass after fixes — all findings resolved same day.** Zero demo-honesty
violations (T1) were found: all 8 computed demo JSONs regenerate byte-identical
from `scripts/build_demo_data.py`, every chapter-cited number reproduces from
companion code (verified by recomputation), all island data contracts match
their JSON, dist HTML has zero `undefined`/`NaN`, and companion tests pass
65/65. The §5 chapter contract held in full for 8 of 11 chapters pre-fix and
all 13 post-fix; LOS↔anchor bijection holds in all 13.

Totals across the three reviews: **4 T1 · 8 T2 · ~19 T3** (some findings
duplicated across reviewers; deduplicated below). All applied.

## T1 (must-fix) — all fixed

1. **Ch4↔Ch5 handoff contradiction** — ch4's stretch described configs
   ("A reranks; B doubles budget") that contradicted ch5's opener and the
   actual `rag_compare_demo.json` (A = tight budget/no floor; B = floor +
   ~3× budget). *Fixed:* ch4 stretch rewritten to match data; the premature
   "rerank" leak (ch6 content) removed; ch5 opener's residual "reranks
   nothing" phrasing aligned.
2. **Ch6↔Ch7 handoff contradiction** — same incident retold with numbers 10×
   apart (180ms→520ms vs 1.8s→5.6s). *Fixed:* both sides now say the
   *retrieval stage* went 180ms→520ms and *end-to-end p95* blew past the
   2-second SLA.
3. **Ch11 anchor order violated the LOS list** (body: five-steps →
   tradeoff-talk → diagnose-gap; LOS listed diagnose-gap second). *Fixed:*
   LOS 11.2 ↔ 11.3 swapped so frontmatter order matches the body; the
   diagnose-gap anchor living on the quiz section is accepted as the
   capstone's intended shape (mirrors guide-1 ch12).
4. **Invented multiplier** — ch6 claimed cross-encoders are "5–10× better"
   at judging relevance; published gains are +5–20 nDCG points. *Fixed:*
   restated as "substantially better (typically worth +5–20 nDCG points over
   the first stage's ordering)."

## T2 (should-fix) — all fixed

5. **Communication-statistic over-attribution** (ch12 + quiz JSON) — "~40–45%
   in hiring-manager surveys" / "every documented dataset" traced to ONE
   published ~50-hire review (per the demand dossier). *Fixed:* attributed
   precisely ("one published review of ~50 hiring decisions… practitioner
   guides consistently rank them first"); "every documented dataset" softened;
   frontmatter description + research_debt + quiz explanation aligned.
6. **Break-even expression didn't evaluate to its result** (ch7 practice):
   "$864 / $0.0005 ≈ 58K/day" omitted the ÷30. *Fixed:* "$864/month ÷ 30 days
   ÷ $0.0005/query ≈ 58K queries/day."
7. **PipelineCompareExplorer hardcoded ch5's predict text**, contradicting
   itself on screen when reused by ch6 (B vs C). *Fixed:* predict copy moved
   into each JSON (`predict` field); component renders `data.predict`.
8. **Ch5 data contradicted its own abstain taxonomy** — the paraphrase row
   (answerable but lexically unreachable) was labeled `abstain-safe`, and the
   practice answer used a third untaught term. *Fixed:* new explicit category
   **`abstain-unreachable`** added to `categorize_outcome`, the ch5 table
   (8 rows), the island's outcome map, and the practice answer; both compare
   and upgrade JSONs regenerated (Q4-B now `abstain-unreachable`; aggregates
   unchanged by design — unreachable counts as a safe abstain).
9. **"Extraction" overloaded** across ch3 (PDF text) and ch4/5 (answer
   selection). *Fixed:* ch3 → "text extraction" / "text-extraction audit";
   ch4 FP3 → "Answer extraction"; ch5 table + island label →
   "answer-extraction miss"; builder why-string updated.
10. **Ch11 YouWillLearn bullet didn't mirror an LOS.** *Fixed:* bullets now
    mirror the (reordered) LOS — framework+mock, trade-off+rubric, gap
    diagnosis.
11. **Ch11→12 chain was thematic only.** *Fixed:* ch12 opener now explicitly
    picks up ch11's interview-as-a-system stretch.

## T3 (polish) — all fixed

- Ch2: garbled self-check ("which score is exactly zero" → "which *two*
  scores"; equal-idf framing corrected).
- Ch3: pseudo-quantified pitfall ("10% better chunking beats 2× embedding
  spend" → qualitative); coherence range corrected to the demo's actual span
  (0.17–0.67); stretch's fictional ranks softened to match the ch4 demo.
- Ch4: opener/communication-bullet ranks aligned to the real demo (#3);
  "majority of failures are retrieval" attributed to practitioner
  postmortems; practice stem now glosses the four RAGAS metric names.
- Ch5: LOS 5.3 category list completed (retrieval-miss added); "safe abstain"
  → "honest abstain" in the Communication bullet.
- Ch6: see-it text now counts "four red cells" and discloses that config C
  also upgrades answer-extraction (working query + coverage scorer); the
  +15–25% recall figure carries the same verify-yourself hedge as the cascade
  claim; LOS 6.2/6.3 + YWL bullets rescoped (rewriting belongs to 6.2).
- Ch7: latency rule-of-thumb constants qualified (modern accelerator,
  quantized weights; 2–4× slower on older fp16).
- Ch9: "not promptly" typo → "not a prompt tweak".
- Ch12: Google's AI-assisted round correctly tensed as an *announced pilot*
  (Meta and Canva: shipped); NoteBox "Twelve chapters" → "Every chapter".
- Quiz JSONs: "named/documented" framings softened to their actual evidence
  strength; Meta/Google/Canva claim corrected; "prompt theater" phrasing
  de-attributed.
- RagPipelineExplorer: answer attribution labeled "chunk id N (not list
  position)" to prevent rank/id misreading.

## Reviewer-noted strengths (kept for the record)

- "The quantitative spine of these chapters is exceptionally solid — every
  worked example, explorer dataset, and cost/latency figure reproduces
  mechanically from the companion code (a genuinely rare property)."
- Demo-honesty review found **zero** T1s; ch8's scripted-policies disclosure
  called "exemplary policy compliance."
- Narrative chain verified connected 01→12 (post-fix: all three flagged seams
  repaired); gift-card/refund through-line consistent everywhere it recurs.
- Weighted-dimension distribution (post-review note): Trade-off ×5,
  Communication ×3, Eval Rigor ×2 (+ch1), Technical Correctness ×1 — skew
  acknowledged; TC is deliberately concentrated in ch4 (the mechanism
  chapter), and the skew toward Trade-off matches the guide's judgment-led
  thesis. Left as-is, recorded here.

## Re-verification after fixes

- `python3 scripts/build_demo_data.py` → regenerated; new category present;
  byte-stable on second run.
- Tests: mini_eval 24/24 · mini_rag 29/29 · mini_agent 12/12.
- `npm run build` → validate ✓ 27 chapters, no errors; dist grep for
  `undefined|NaN` → zero hits; ch6's stale predict text confirmed gone from
  built HTML.
- LOS↔anchor bijection: all 13 chapters OK.
