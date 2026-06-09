# Resume notes — guides-ai-engineering (as of 2026-06-09)

Part of the AI-native series roadmap (`~/guides/docs/plans/active/2026-06-04_session_handoff.md`
is the canonical direction; `~/guides/docs/plans/active/2026-06-08_roadmap_audit.md` is the state
audit). This is the **multi-guide** `guides-ai-engineering` repo — guides as Astro content
collections under `src/content/<guide>/`, one shared `companion/` lib, per-guide capstones.

## Guides
- **#1 Evaluation — COMPLETE, reviewed, PUBLIC.** 13 chapters (0–12) in the §5 shape; committed
  `f52ea51`, pushed to `github.com/brandon-behring/guides-ai-engineering`. Independent 5-dimension
  review done 2026-06-09; all findings fixed (`docs/REVIEW_FINDINGS_2026-06-08.md`); LOS anchors
  bijective in all 13.
- **#2 LLM App Engineering — IN PROGRESS.** RAG-centric, ~13 ch. Outline + status + slug list:
  `docs/guide-02-llm-app-engineering.md`. **Ch 0–1 authored**; `mini_rag` companion seeded. Next:
  Ch 2 (Retrieval 101) — first to import `mini_rag`.

## Companion (`companion/`, stdlib-only, "for learning, not production")
- `mini_eval` — 6 modules (metrics·confidence·calibration·retrieval·agent·judge), **24/24 tests**.
- `mini_rag` — seeded: `search` (TF-IDF + cosine + top_k), **7/7 tests**. Grows across guide #2 ch2–7.
  `pyproject.toml` ships both packages.

## Build / test
```bash
npm install && npm run build                 # astro build + book-scaffold validate
python3 companion/tests/test_mini_eval.py    # 24 tests
python3 companion/tests/test_mini_rag.py     # 7 tests
python3 scripts/build_demo_data.py           # regenerate the COMPUTED demo JSON (7 files, seeded)
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
