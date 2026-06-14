# Resume notes — guides-ai-engineering (as of 2026-06-10)

Part of the AI-native series: **`~/guides/docs/plans/active/2026-06-10_series_roadmap_v2.md` is the
canonical roadmap** (design doc: `~/guides/docs/design/2026-06-10_design_v0.4.md`); the earlier
06-04 handoff + 06-08 audit are superseded (now in `~/guides/docs/plans/done/`). This is the
**multi-guide** `guides-ai-engineering` repo — guides as Astro content
collections under `src/content/<guide>/`, one shared `companion/` lib, per-guide capstones.

## Guides
- **#1 Evaluation — COMPLETE, reviewed, PUBLIC.** 13 chapters (0–12) in the §5 shape; committed
  `f52ea51`, pushed to `github.com/brandon-behring/guides-ai-engineering`. Independent 5-dimension
  review done 2026-06-09; all findings fixed (`docs/REVIEW_FINDINGS_2026-06-08.md`); LOS anchors
  bijective in all 13.
- **#2 LLM App Engineering — COMPLETE, reviewed (2026-06-10).** All 13 chapters (0–12) in the
  §5 shape; independent 3-agent review, all findings fixed (`docs/REVIEW_FINDINGS_2026-06-10.md`);
  LOS anchors bijective in all 13. Build log: `docs/guide-02-llm-app-engineering.md`.
  **LAUNCHED 2026-06-12** — this repo is live at `guides-ai-engineering.brandon-m-behring.workers.dev`
  (Workers static assets; root 302 → `/ai-engineering/`), hub at `guides.brandon-behring.dev`. The
  `/ai-engineering/*` mount on the hub domain is **LIVE (2026-06-14)** — a hub Worker path proxy, unblocked
  by scaffold **v4.24.0** (#140/#141 base-aware-link fixes; this repo bumped 4.14.2 → 4.24.0, the `_redirects`
  stopgaps removed). Launch state: `~/guides/docs/plans/active/2026-06-10_series_roadmap_v2.md` §5.
- **#3 Production AI Systems — COMPLETE, reviewed (2026-06-13).** All 13 chapters (0–12) in the
  §5 shape — the production loop (deploy/serve/observe/evaluate/respond) + judgment + capstone +
  craft. `mini_prod` companion (latency·cascade·trace·monitor·drift, 44 tests) builds on
  `mini_rag.budget` + `mini_eval`. Independent 3-agent review, all findings fixed
  (`docs/REVIEW_FINDINGS_2026-06-13.md`); LOS↔anchor bijective in all 13. Build doc:
  `docs/guide-03-production-ai-systems.md`.
- **#4 Working with AI — IN PROGRESS (2026-06-14).** Engineering *with* an AI assistant the way
  interviews now judge it (governing/verifying/explaining code you didn't type). Ch 0 authored
  (`why-working-with-ai` — the shift + the working-with-AI loop clarify→preregister→prompt→review→run→explain
  + 3 AI-productivity myths via `ScenarioQuiz`). Ships **workflow artifacts, not a `mini_*` lib**
  (roadmap §6); demos hand-authored. Content-flow spine (**~11–13 ch, emergent** — count locked after
  the Movement-B draft). Outline + work-order: `docs/guide-04-working-with-ai.md`. Plan of record:
  `~/.claude/plans/what-is-the-roadmap-crystalline-sky.md`. Weighted dimension: **Communication**.

## Companion (`companion/`, stdlib-only, "for learning, not production")
- `mini_eval` — 6 modules (metrics·confidence·calibration·retrieval·agent·judge), **24/24 tests**.
- `mini_rag` — 5 modules (search·chunk·pipeline·rerank·budget), **29/29 tests**.
- `mini_agent` — 3 modules (loop·tools·orchestrate + crew), **12/12 tests**.
- `mini_prod` — 5 modules (latency·cascade·trace·monitor·drift), **44/44 tests**; builds on `mini_rag.budget` + `mini_eval`.
  `pyproject.toml` ships all four packages.
- **Working with AI (#4)** ships **no Python package** — workflow artifacts (preregistration
  template · loop checklist · review rubric), planned Phase 2; demos are hand-authored ScenarioQuiz JSON.

## Build / test
```bash
npm install && npm run build                 # astro build + book-scaffold validate
python3 companion/tests/test_mini_eval.py    # 24 tests
python3 companion/tests/test_mini_rag.py     # 29 tests
python3 companion/tests/test_mini_agent.py   # 12 tests
python3 companion/tests/test_mini_prod.py    # 44 tests
python3 scripts/build_demo_data.py           # regenerate the COMPUTED demo JSON (20 files, seeded)
```
ScenarioQuiz / quiz-style demo JSON (`benchmark_demo.json`, `llm_claims_demo.json`,
`prompt_robustness_demo.json`, …) are **hand-authored**, not emitted by `build_demo_data.py`.

## Routing (multi-guide)
One `chapters` collection, base `./src/content` (with a `!frontmatter/**` guard so
`frontmatter/authors.mdx` stays out). A `generateId` on the glob namespaces each id by its guide
folder, so chapters serve at `/ai-engineering/chapters/<guide>/<slug>/` (e.g.
`…/chapters/evaluation/why-evaluation/`, `…/chapters/llm-app-engineering/why-llm-app-engineering/`);
slugs only need to be unique *within* a guide. The scaffold's `/chapters/` index still lists all
guides mixed (interim; per-guide index / first-class multibook = scaffold **#15**, deferred).
`book-scaffold validate` counts files under the collection base, so it reports 16 (13 + 2 chapters +
`authors.mdx`) — cosmetic; "no errors".

## Known items (carry-forward; none blocking)
1. **`/` index route collision** — the custom `src/pages/index.astro` (guide picker) duplicates the
   scaffold's auto-injected index (WARN now, future Astro hard-error). Filed: book-scaffold-astro **#129**.
2. **Per-guide index / landing** — URLs are now per-guide (`/chapters/<guide>/<slug>/`), but the
   shared `/chapters/` index still mixes guides; a per-guide index + guides landing waits on scaffold
   **#15** (multibook, deferred). Not blocking.
3. **`build-labels` finds 0 ids** — chapter anchors are MDX comments, not the scaffold's label
   mechanism; fine until cross-guide `<XRef>` is needed.
4. **`paradigms` enum** still the pedagogical-frameworks set (`default|udl|srl|andragogy`), not the
   v0.3 presentation-modes set — open design item; chapters use `[default]`.
5. **LOS↔anchor lint** — the build does not enforce `los[].anchor` ↔ prose `{/* anchor */}`
   bijection; enhancement filed as book-scaffold-astro **#130**. Enforce by eye until it ships.

---

## Guide-2 completion push (2026-06-10, in flight) — self-contained work order

Goal: author Ch 2–12, grow the companion, pass the guide-1-style independent 5-dim review →
guide #2 **complete** → the launch workstream (roadmap v2 §5) opens. Work in chapter order;
**commit per chapter-block**; update the status table in `docs/guide-02-llm-app-engineering.md`
as each chapter lands.

### Chapter conventions (copy from `01-prompt-engineering-discipline.mdx` — the template)
- **File**: `src/content/llm-app-engineering/<NN>-<slug>.mdx`. Frontmatter: `title`, `slug`,
  `description`, `freshness: literature-survey`, `last_verified`, `tags`, `sources: []`,
  `draft: false`, `mode: tutorial`, `target: transfer`, `ordering: problem-first`,
  `commitment: long-lived`, `paradigms: [default]`, `research_debt_addressed: |`,
  `task_classes`, `provenance` (ai_tools + audit_history + citation_backstop: manual), `los[]`.
- **LOS ids**: `LAE-<ch>.<n>` (e.g. LAE-2.1), each with `bloom`, `statement`, `anchor`,
  `threshold`. **Every `los[].anchor` needs exactly one `{/* anchor: <slug> */}` on a `##`
  heading** — bijective, checked by eye.
- **Body shape (§5)**: `<YouWillLearn prerequisites=…>` (3 bullets mirroring the LOS) →
  productive-failure opener (concrete scenario, "Predict:" prompt) → `<Pitfall title=…>` →
  principle sections (anchored; code/KaTeX only where it carries load; companion code imported
  conceptually, shown as Python) → **island demo** (`client:visible`, frozen data) → `<Practice
  id=… difficulty={n}>` with `<details><summary>One defensible answer</summary>` → `## How this
  is graded` (4 bullets: Technical Correctness · Trade-off Awareness · Evaluation Rigor ·
  Communication — name the chapter's weighted dimension) → `### Industry variation` (3 bullets
  from: startup velocity · enterprise maturity/compliance · fintech · marketplace latency ·
  frontier-lab; + AI-assisted-interview note where apt) → `## Stretch: …` (PFL — related-but-
  unseen problem, hands off to the next chapter).
- **Voice**: second person, concrete, failure-first; no fabricated model outputs anywhere —
  quiz items are hand-authored claims/scenarios, computed demos come from companion code.

### Demo conventions
- **Computed** JSON → add a `<name>_demo()` function to `scripts/build_demo_data.py` (seeded
  `random.Random(<n>)`, round floats, import from companion) + register in `main()`.
- **Authored** JSON (ScenarioQuiz) → hand-write `src/data/<name>_demo.json` matching
  `ScenarioQuiz.tsx`'s shape (check the TSX before authoring; existing examples:
  `prompt_robustness_demo.json`, `llm_claims_demo.json`).
- New islands: Preact `.tsx` in `src/components/`, props `{ data }`, imported with
  `client:visible`; theme via CSS vars like existing explorers. Prefer **reusing** existing
  islands (`ScenarioQuiz`, `RagEvalExplorer`) over new ones unless interactivity is the lesson.

### Seed map (transform, not port; agnosticize insurance/company framing)
`V9 = ~/interview_prep_series/vol09_ai_engineering/chapters/`,
`V8 = ~/interview_prep_series/vol08_llm_foundations/chapters/`,
`AIES = ~/interview_prep_series/vol_ai_eng_interview/` (chapter files inside).
| Ch | Slug | Seeds | Companion work | Demo |
|----|------|-------|----------------|------|
| 2 | retrieval-101 | V9/05_vector_databases.tex · V8/10_retrieval.tex | `mini_rag.search` (built) | NEW retrieval explorer (computed) |
| 3 | chunking-document-representation | V9/04_document_processing.tex | NEW `mini_rag.chunk` | chunk-size sweep (computed) |
| 4 | rag-end-to-end | V9/06_rag_production.tex · V8/04_rag_architecture.tex | NEW `mini_rag.pipeline` | step-through or ScenarioQuiz |
| 5 | evaluating-rag | V9/09_evaluation_topology.tex | bridge to `mini_eval.retrieval` (no new code) | reuse RagEvalExplorer (`rag_demo.json`) |
| 6 | advanced-rag | V9/06 · V8/10 | NEW `mini_rag.rerank` | rerank before/after (computed) |
| 7 | rag-in-production | V9/15_serving_inference.tex · V9/16_observability.tex | NEW `mini_rag` cost/latency model | budget explorer (computed) |
| 8 | agents-tool-use | V8/08_agents.tex · V9/07_agentic_architectures.tex · V9/11_mcp.tex | NEW `mini_agent.loop` (mock tools, scripted policy, no LLM) | agent-trace step-through (frozen trace) |
| 9 | multi-agent-orchestration | V9/12_multi_agent_systems.tex · V9/10_llm_frameworks.tex | extend `mini_agent` (orchestrator/workers) | reuse trace island or ScenarioQuiz |
| 10 | finetune-vs-rag-vs-prompt | V9/13_finetuning.tex (lightweight) | — | ScenarioQuiz (authored decisions) |
| 11 | system-design-capstone | V9/18_system_design.tex · AIES ch5–6 | — | rubric-scored capstone (capstone_demo pattern) |
| 12 | interview-craft-transfer | V9/19 + V9/20 · AIES ch11 · demand-spine AI-assisted-coding deep-dive | — | ScenarioQuiz |

### Completion gate (after Ch 12)
Independent **5-dim review** by a fresh agent (math / demo-honesty / factual / pedagogy-shape /
island+MDX integrity) → `docs/REVIEW_FINDINGS_<date>.md` → apply ALL fixes → LOS↔anchor
bijection across all 13 → `npm run build` + validate + both test files green → update README
guide table + this file + guide-02 doc → commit + push. Then tell the user the **launch
workstream is unblocked** (roadmap v2 §5 — their Cloudflare dashboard session).
