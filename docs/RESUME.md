# Resume notes — Evaluation guide (as of 2026-06-08)

Part of the AI-native series roadmap (`~/guides/docs/plans/active/2026-06-03_ai_engineering_series_roadmap.md`;
direction in `~/guides/docs/plans/active/2026-06-04_session_handoff.md`; build log in
`~/guides/docs/plans/active/2026-06-08_roadmap_audit.md`). This repo is the
`guides-ai-engineering` multi-guide repo; **Evaluation is guide #1 and is now complete.**

## Done (verified green)
- Repo on scaffold **v4.14.2**; `astro build` + `book-scaffold validate` pass (**13 chapters**).
- **`mini_eval`** companion — six modules, **24/24 tests pass**
  (`python3 companion/tests/test_mini_eval.py`):
  - `metrics.py` (confusion matrix, P/R/F1, threshold sweep, AP — Ch 2)
  - `confidence.py` (bootstrap CI, paired diff CI, permutation test — Ch 3)
  - `calibration.py` (Brier, reliability curve, ECE — Ch 4)
  - `retrieval.py` (precision@k, recall@k, MRR, NDCG — Ch 9)
  - `agent.py` (pass@k, mean pass@k — Ch 10)
  - `judge.py` (mock LLM-as-judge + bias diagnostics — Ch 7)
- Demo data generator (`scripts/build_demo_data.py`) → 7 JSON files in `src/data/`.
- **Nine Preact-island demos**: ThresholdExplorer, JudgeBiasExplorer, ConfidenceExplorer,
  ReliabilityExplorer, RagEvalExplorer, PassAtKExplorer, DriftMonitorExplorer,
  MetricMatchExplorer, and the reusable ScenarioQuiz (Ch 8/5/6/12).
- **All 13 chapters authored** (0–12) in the §5 shape, each rubric-anchored with LOS +
  anchors and an ICAP island: 0 why-eval · 1 mindset · 2 threshold · 3 confidence ·
  4 calibration · 5 data-integrity · 6 reference-based-vs-free · 7 llm-as-judge ·
  8 benchmark-literacy · 9 RAG · 10 agentic · 11 production · 12 capstone.

## Next — the publish bar is met
- **Publish gate (complete guide) = MET.** Pushing `guides-ai-engineering` to GitHub is
  the outward-facing step and needs the user's go — the repo currently has **no remote**.
  (Decision trail: publish was gated on the complete Evaluation guide; see the 06-08 audit.)
- **Independent review + polish pass — DONE (2026-06-09):** 5-dimension independent review
  (companion math / demo-honesty / factual / pedagogy / island+MDX); all findings fixed across
  three tiers. Record: `docs/REVIEW_FINDINGS_2026-06-08.md`. Build green, 24/24 tests, all 13
  chapters' LOS anchors bijective.
- **Still recommended before publish:** file the `consumer:guides` issues below.
- **Then guide #2** (e.g. llm-app-engineering) — which triggers the multi-guide routing
  generalization in item 2 below.

## Known items (carry-forward; none blocking)
1. **`/` index route collision** — custom `src/pages/index.astro` duplicates the
   scaffold's auto-injected index (warning now, future Astro hard-error). → file a
   `consumer:guides` issue on book-scaffold-astro (per the hub's upstream policy),
   not a local hack.
2. **Multi-guide routing** — currently single `chapters` collection (base
   `src/content/evaluation`) → URLs `/ai-engineering/chapters/<slug>`. When guide
   #2 lands, generalize to per-guide collections + `[guide]/...` routes.
3. **`build-labels` finds 0 ids** — chapter anchors are MDX comments, not the
   scaffold's label mechanism; fine until cross-guide `<XRef>` is needed.
4. **`paradigms` enum** still the pedagogical-frameworks set (`default|udl|srl|
   andragogy`) inherited from the pilot, not the v0.3 presentation-modes set —
   open design item; chapters use `[default]`.

## Build / test
```bash
npm install && npm run build
python3 companion/tests/test_mini_eval.py    # 19 tests
python3 scripts/build_demo_data.py           # if mini_eval changes, regenerate demo JSON
```
