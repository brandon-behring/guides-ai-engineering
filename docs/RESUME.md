# Resume notes — Evaluation guide (as of 2026-06-03)

Part of the AI-native series roadmap (`~/guides/docs/plans/active/2026-06-03_ai_engineering_series_roadmap.md`).
This repo is the `guides-ai-engineering` multi-guide repo; Evaluation is guide #1.

## Done (verified green)
- Repo skeleton on scaffold **v4.14.2**; `astro build` + `book-scaffold validate` pass.
- **`mini_eval`** companion: `metrics.py` + `judge.py`; 7/7 tests pass
  (`python3 companion/tests/test_mini_eval.py`).
- Demo data generator (`scripts/build_demo_data.py`) → `src/data/{threshold,judge}_demo.json`.
- Two Preact-island demos: `ThresholdExplorer`, `JudgeBiasExplorer`.
- **Chapters authored** in the §5 shape: **Ch 0** (why-evaluation), **Ch 2**
  (threshold-tradeoff + ThresholdExplorer), **Ch 7** (llm-as-judge + JudgeBiasExplorer).

## Next — task #6: the remaining chapters (§13 arc) + capstone
Author, in batches, in the §5 chapter shape (opener → principle + faded worked
example → multi-paradigm → ICAP demo → interleaved practice → rubric tie-in →
industry callout → PFL stretch → `provenance`). Use Ch 2 / Ch 7 as the templates.

- **Ch 1** Eval mindset (what-before-how; failure-mode-first; 3 contrasting systems).
- **Ch 3** Confidence & statistical rigor — *extend mini_eval* with bootstrap CIs.
- **Ch 4** Calibration & reliability — *extend mini_eval* (`calibration.py`: ECE,
  reliability curve); add a calibration ICAP demo.
- **Ch 5** Data integrity — leakage, **benchmark contamination**, reproducibility.
- **Ch 6** Reference-based vs reference-free.
- **Ch 8** Benchmark literacy (MMLU/GPQA/HumanEval/SWE-bench/GAIA/Arena/HELM/LiveBench).
- **Ch 9** RAG evaluation — *extend mini_eval* (`mini_rag` or a retrieval-metrics
  module: MRR/NDCG, faithfulness/context-precision); demo.
- **Ch 10** Agentic & task eval (trajectory/tool-use, success@k).
- **Ch 11** Production eval & monitoring (online, guardrails, drift, cost/latency-as-eval).
- **Ch 12** System design: design an eval strategy → the **capstone** (`capstone/`).

## Known items (carry-forward; none blocking)
1. **`/` index route collision** — custom `src/pages/index.astro` duplicates the
   scaffold's auto-injected index (warning now, future Astro hard-error). → file a
   `consumer:guides` issue on book-scaffold-astro (per the hub's upstream policy),
   not a local hack.
2. **Multi-guide routing** — currently single `chapters` collection (base
   `src/content/evaluation`) → URLs `/ai-engineering/chapters/<slug>`. When guide
   #2 lands, generalize to per-guide collections + `[guide]/...` routes so URLs
   become `/ai-engineering/<guide>/...`.
3. **`build-labels` finds 0 ids** — chapter anchors are MDX comments, not the
   scaffold's label mechanism; fine until cross-guide `<XRef>` is needed.
4. **`paradigms` enum** still the pedagogical-frameworks set (`default|udl|srl|
   andragogy`) inherited from the pilot, not the v0.3 presentation-modes set —
   open design item; chapters use `[default]`.

## Build / test
```bash
npm install && npm run build
python3 companion/tests/test_mini_eval.py
python3 scripts/build_demo_data.py   # if mini_eval changes, regenerate demo JSON
```
