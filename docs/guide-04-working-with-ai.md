# Guide #4 — Working with AI (outline + status)

The fourth guide in the AI-engineering series: **engineering *with* an AI assistant — the way
interviews and real teams now judge it.** The skill is no longer producing code; it is
governing, verifying, and explaining code you did not type. Company-agnostic, interview-prep-led,
taught for transfer. Audience: engineers moving into AI-native roles (SWE/DS background assumed;
guides #1–#3 are siblings, not prerequisites — this guide is about the *practice* of AI-assisted
work, not building AI systems).

Direction: `~/guides/docs/plans/active/2026-06-10_series_roadmap_v2.md` §6 (Guide #4, promoted
candidate → planned 2026-06-14) · demand spine:
`~/guides/docs/research/role_demand_and_interview_signals/` (esp. `_gather_new_topics_2026-06-03.md`
§"AI-assisted-coding interviews"). Plan of record: `~/.claude/plans/what-is-the-roadmap-crystalline-sky.md`.

## Status: IN PROGRESS (2026-06-14)

**Phase 1 + Movements B–D complete.** Ch 0–11 authored (framing + the full loop + communication/anti-patterns + scale); outline + companion
shape locked; index + RESUME entries added. **Chapter count LOCKED at 13 (ch 0–12)** after the
Movement-B draft (2026-06-14), per the content-flow steer: the merge points (clarify/preregister,
prompting/reading, provenance) were assessed and each kept as a full chapter because each earns its
place — 13 by content, not padded to match the series.

### Build log

- **Ch 0 authored** (2026-06-14) — "Why working with AI is its own engineering skill." The shift
  (bottleneck moved from producing code → governing + explaining it), the working-with-AI **loop**
  (clarify → preregister → prompt → review → run → explain) as the guide's spine, and three
  AI-productivity myths via `ScenarioQuiz` (`ai_productivity_myths_demo.json`, hand-authored). No
  companion code (by design — this guide ships workflow artifacts, not a lib).
- **Ch 1 authored** (2026-06-14) — "What interviewers actually test." Maps the four assessed
  AI-coding dims onto the 4-dim rubric (`the-mapping`); why automating the typing *raises* the bar
  on comprehension/verification/communication (`stakes-rise`); a "read the signal" `ScenarioQuiz`
  (`interview_signal_demo.json`) diagnosing which dimension a behaviour exposes (`reading-the-signal`).
- **Ch 2 authored** (2026-06-14) — "Clarify before you code." Loop stage 1: the cost asymmetry of a
  confident wrong aim, sharpened by AI's no-pushback compliance (`wrong-aim`); finding the pivotal
  term to clarify (`what-to-clarify`); using the AI as a clarification partner without ceding the
  spec (`clarify-with-ai`); `clarify_demo.json` "spot the missing clarification".
- **Ch 3–6 authored** (2026-06-14, Movement B) — the loop's solo stages, each owning one stage with a
  hand-authored `ScenarioQuiz`: **Ch 3** preregistration (`theory-before-data`/`what-to-preregister`/
  `governance`; `preregistration_demo`), **Ch 4** strategic prompting (`prompt-as-spec`/`decompose`/
  `constraints-context`; `prompting_demo`), **Ch 5** reading AI code (`reading-is-hard`/`fluency-trap`/
  `read-against-spec`; `reading_ai_code_demo`), **Ch 6** verification (`ran-vs-verified`/`the-gate`/
  `debugging-ai`; `verification_demo`). Per-chapter weighted dims: rigor · trade-off · correctness · rigor.
- **Ch 7–8 authored** (2026-06-14, Movement C) — **Ch 7** communication-while-you-delegate (the guide's
  weighted dimension; `silence-fails`/`what-to-narrate`/`narrate-collaboration`; `communication_demo`),
  **Ch 8** anti-patterns (`four-antipatterns`/`contrasting-cases`/`short-term-reward`; `antipatterns_demo`).
- **Ch 9–11 authored** (2026-06-14, Movement D — at scale) — **Ch 9** agentic-workflows
  (`loop-at-scale`/`scope-checkpoints`/`govern-not-read`; `agentic_demo`), **Ch 10** evaluating-ai-output
  (`reading-doesnt-scale`/`golden-sets`/`nondeterministic`; `evaluating_ai_output_demo`; **bridge to
  `mini_eval` / Guide #1**), **Ch 11** provenance-accountability (`approval-is-ownership`/`provenance-trail`/
  `hardest-cases`; `provenance_demo`).

## Demand basis

AI-assisted-coding is a **genuinely new interview competency** (2025–26), well-evidenced and dated:
Meta (CoderPad 3-panel, Oct 2025 — pick GPT/Claude/Gemini/Llama; 60-min multi-file bug→build→optimize),
Google ("code comprehension" round, May 2026 pilot — *75% of new code AI-generated*), Canva
(un-one-shottable problems, Jun 2025). What's assessed (4 dims): strategic prompting/clarification ·
code comprehension · verification & debugging (prompt→review→run→confirm) · communication during
automation. Meta's explicit signal: *"rely solely on prompting → you fail."* The **#1 documented
rejection cause across the whole demand baseline is communication (~40–45%)** — which is exactly this
guide's weighted rubric dimension. (Source: `_gather_new_topics_2026-06-03.md` L34–44;
`_independent_baseline_2026-06-03.md` failure modes.)

The durable, tool-version-proof thesis is in the research already: **"preregistration, not prompt
theater" — governance over automation** (commit files/invariants/tests *before* using AI). The guide
anchors on this; volatile company/tool/format specifics live only in dated `### Industry variation`
callouts so the core does not rot (see Durability policy below).

## Spine & outline (content-flow movements — count LOCKED at 13, ch 0–12)

Organized as **movements**; the chapter count emerged from the content and was **locked at 13 (ch
0–12) on 2026-06-14** after the Movement-B draft. `[private]` seeds live in `~/interview_prep_series/`
(optional pull; default is author-fresh from the public demand research, which is sufficient).
✅ = authored + verified + committed.

| Mvt | Ch | Slug | What it does | Demand seed |
|----|----|----|----|----|
| **A — The shift** | 0 ✅ | `why-working-with-ai` | Bottleneck moved to judgment + communication; the loop; three myths | `_gather_new_topics` §AI-assisted-coding |
| | 1 ✅ | `what-interviewers-test` | The 4 assessed dims mapped onto the series 4-dim rubric; how each is scored + fails | L39–40 |
| **B — The durable loop** | 2 ✅ | `clarify-before-you-code` | Loop stage 1: pin the real problem before prompting (failure mode #2) | baseline failure modes |
| | 3 ✅ | `preregistration` | Loop stage 2: commit shape/invariants/tests *before* prompting — governance over automation | L41–42 |
| | 4 ✅ | `strategic-prompting` | Loop stage 3: prompt as spec; decompose vs one-shot; constraints | L39 |
| | 5 ✅ | `reading-ai-code` | Loop stage 4: comprehension; the fluency trap; read against the spec | L39 |
| | 6 ✅ | `verification-under-automation` | Loop stage 5: ran vs verified; the gate; debugging AI output | L39–40 |
| **C — Hardest dim + failure** | 7 | `communication-while-you-delegate` | Loop stage 6 (runs throughout): **#1 failure mode / guide's weighted dim** | baseline (~40–45%) |
| | 8 | `anti-patterns` | Copy-paste automation, prompt theater, automation bias; contrasting cases | L43–44 |
| **D — At scale** | 9 | `agentic-workflows` | Un-one-shottable problems; scoping, checkpoints, review gates across a repo | L38 (Canva) |
| | 10 | `evaluating-ai-output` | Gate AI-written code on a golden set — **bridge to `mini_eval`** | series cross-link |
| | 11 | `provenance-accountability` | Who owns the AI's bug; audit trails for AI code; regulated callouts | A4 sectors L15–16 |
| **E — Transfer** | 12 | `interview-craft-transfer` | Capstone: mock AI-assisted interview (preregister→build→explain), self-graded vs rubric | `[private]` vol09 ch19–20 · AIES |

**Merge/split points — RESOLVED 2026-06-14:** assessed all three after the Movement-B draft and kept
each as a full chapter — `clarify` and `preregistration` are distinct stages (understand the problem
vs commit the solution's contract); `strategic-prompting` and `reading-ai-code` are opposite stages
(produce vs comprehend); `provenance-accountability` carries a distinct, demand-grounded topic
(ownership/audit of AI code). Final count: **13**, by content, not padding.

**Narrative chain:** A names the shift + the loop → B builds the loop stage by stage → C confronts the
hardest dimension and its failure mode → D scales the loop to real repos and gates its output → E
demonstrates transfer under interview conditions.

## Companion plan — workflow artifacts, not a lib (roadmap §6)

Unlike #1–3 (`mini_*` Python libs that also compute the demos), Guide #4 ships **workflow artifacts**.
**Option A (default)** — no Python package, under `companion/working-with-ai/`:

- `preregistration.md` — the files/invariants/tests-first template the reader fills in before prompting.
- `loop-checklist.md` — clarify → preregister → prompt → review → run → explain.
- `review-rubric.md` — the 4-dim rubric operationalized for AI-generated code (self-grading sheet).

Demos are **hand-authored `ScenarioQuiz` JSON** (frozen AI session traces, diff-reviews, anti-pattern
spots, communication rewrites) — honest because no live model output is fabricated.

**Option B (optional upgrade)** — Option A plus one tiny deterministic module
`companion/src/mini_assist/review.py` (score a diff-review / explanation against the 4-dim rubric) +
a `scripts/build_demo_data.py` entry + `tests/test_mini_assist.py`, buying 1–2 *computed* demos.
Recommendation: start with A; promote a single demo (likely the capstone rubric self-scorer) to B only
if hand-authored JSON proves too static.

## Chapter shape (§5) — same as guides 1–3

`<YouWillLearn prerequisites=…>` → productive-failure opener ("Predict:…") + `<Pitfall>` → principle
sections (anchored `{/* anchor: <slug> */}`; code/KaTeX only where it carries load) → **ICAP island**
(`client:visible`, frozen/no-model) → `<Practice id difficulty>` + `<details>` → `## How this is graded`
(4-dim rubric — **Communication is this guide's weighted dimension**) + `### Industry variation` →
`## Stretch` (PFL, hands to next chapter). `los[].anchor` ↔ prose anchors **bijective** in every chapter.

- **LOS ids**: `WAI-<ch>.<n>` (e.g. WAI-0.1).
- **Frontmatter**: `title, slug, description, freshness: literature-survey, last_verified, tags, sources: [], draft: false, mode, target: transfer, ordering, commitment: long-lived, paradigms: [default], research_debt_addressed, task_classes, provenance{ai_tools, audit_history, citation_backstop: manual}, los[]`. The Ch 0 "why" chapter uses `mode: explanation`; build/how-to chapters use `mode: tutorial`.
- **Demos**: hand-authored `ScenarioQuiz` JSON (check `src/components/ScenarioQuiz.tsx` shape); reuse the island — new Preact islands only if a computed demo (Option B) needs one.
- **Voice**: second person, concrete, failure-first; no fabricated model outputs anywhere.

## Demo policy (frozen / no-model)

Unchanged from guides 1–3 (design v0.4 §2.6): static client-side only, no live LLM. For a guide *about*
working with live AI, demos use **frozen AI session traces / hand-authored scenarios** (the AI's
outputs are pre-written, never fabricated live). Live-LLM interactivity is the personal simulator's job
(out of scope). Demo honesty is a review-gate dimension.

## Durability policy (the dating-fast hedge)

Anchor chapters on the **long-lived core** — governance over automation, preregistration, the
clarify→…→explain loop, the 4 dims, communication. Quarantine the **volatile** — specific company
interview *formats*, specific tools, specific stats — into dated `### Industry variation` / interview-note
callouts tagged with `last_verified`, so the core ages without rotting.

## Industry-variation callouts to thread

Startup (AI velocity prized — but gate it: review + a test gate so speed isn't debt) · big tech
(AI-assisted coding mainstream; comprehension explicitly assessed; system design assumes LLM
integration + cost/latency) · fintech/regulated (provenance + accountability for AI-written code are
first-order; who reviewed it, what it was tested against, who owns the bug) · marketplace (latency/
quality of AI-assisted features as revenue) · frontier-lab (some rounds ban AI to test raw ability,
others assume it — governing automation transfers either way).

## Craft-capstone overlap (flag — decision is the user's, not made here)

Guide #4's `communication-while-you-delegate` + `interview-craft-transfer` chapters substantially *are*
the still-open "craft-capstone guide" (roadmap §3, OPEN). Building #4 is strong evidence to later
resolve that OPEN as **"absorb"** (no separate craft guide). Noted, not decided.

## Completion gate (replicates #1–3)

Independent multi-agent review (facts / demo-honesty + islands / pedagogy + continuity) →
`docs/REVIEW_FINDINGS_<date>.md` → apply ALL fixes → LOS↔anchor bijective in every chapter →
`npm run build` + validate green → companion artifacts present (Option A) / tests pass (Option B) →
update `src/pages/index.astro` (label → Complete), `README.md` guide table, `docs/RESUME.md`, this doc →
commit + push per chapter-block. Only then is Guide #4 complete.
