# Guide #3 — Production AI Systems (outline + status)

The third guide in the AI-engineering series: **operating AI systems after the demo works.**
Production-spine: deploy → serve → observe → evaluate-in-prod → respond, then judgment,
capstone, and craft. Company-agnostic, interview-prep-led, taught for transfer. Audience:
engineers moving into AI-native roles (SWE/DS background assumed; guides #1–#2 are the
prerequisites this guide builds on, not re-teaches).

Direction: `~/guides/docs/plans/active/2026-06-10_series_roadmap_v2.md` §6 (locked next after
guide #2) · demand spine: `~/guides/docs/research/role_demand_and_interview_signals/`.

## Status: COMPLETE (2026-06-13)

**All 13 chapters (0–12) authored** in the §5 shape, independently reviewed (3-agent
math / demo-honesty / pedagogy pass — `docs/REVIEW_FINDINGS_2026-06-13.md`), all findings
fixed; LOS↔anchor bijective in all 13; build + validate clean; `mini_prod` companion
(latency·cascade·trace·monitor·drift, 44 tests, building on `mini_rag.budget` + `mini_eval`).
The outline below is the planning artifact it was built from.

### Build log

- **Ch 0 authored** (2026-06-10) — the production loop (deploy/serve/observe/evaluate/respond),
  the green-dashboards-silent-failure opener continuing guide-2's support bot, three production
  myths via `ScenarioQuiz` (`production_myths_demo.json`, hand-authored). No companion code yet
  (by design — Ch 2 seeds `mini_prod`).

## Demand basis

Production/cost-latency ≈ **18%** of AI-eng interview signal (P0 baseline) — second only to
RAG — and **two of the top documented failure modes** land here: *"no production experience"*
and *"ignoring ops/cost/eval"*. Guide-2 Ch 7 (RAG in production) hands off to this guide
explicitly: it taught the builder's budget instincts; this guide owns the operate-side
lifecycle. Guide-1 Ch 11 (production eval & monitoring) is the measurement seed Ch 6–7 build on.

## Spine & outline (production lifecycle, ~13 ch)

"Transform, not port" the seeds; agnosticize company-tagged framing (the seeds carry
Google/Meta level tags and dated pricing — keep the *frameworks*, re-verify every number at
authoring time per the **Seed freshness notes** below).

> **Seed freshness notes (vol08) — verified 2026-06-10.** The seed repo's velocity scanner flags
> 25 HIGH "March 2026" `datedcontent` stamps in vol08, but those are mostly evergreen chapter
> intros, *not* 25 distinct stale numbers (see hub roadmap v2 §7). The figures that actually need
> re-checking at authoring time — and their current state as of 2026-06-10 — are concentrated in
> vol08's appendices + cost/safety chapters:
>
> - **Frontier model lineup + pricing** (`appendix_c` model comparison, `appendix_b` API ref, `ch13`
>   cost — all snapshot "Dec 2025"). The seed lists GPT-4o, Claude Sonnet 4 / Haiku 4, Gemini 2.0
>   Pro/Flash — **all superseded**. Current ($/MTok in/out):
>     - Anthropic — Opus 4.8 `claude-opus-4-8` $5/$25 (1M ctx) · Sonnet 4.6 `claude-sonnet-4-6` $3/$15
>       (1M) · Haiku 4.5 `claude-haiku-4-5` $1/$5 (200K) · Fable 5 `claude-fable-5` $10/$50 (1M).
>     - OpenAI — GPT-5.5 $5/$30 · GPT-5.4 $2.50/$15 · GPT-5.4 mini $0.75/$4.50 · o3 ~$2 in.
>     - Google — Gemini 3.1 Pro $2/$12 (2M ctx) · Gemini 3.5 Flash $1.50/$9 (1M); **Gemini 2.0 Flash/Pro
>       retired 1 Jun 2026.**
>   Re-pull at authoring — provider pricing drifts.
> - **Benchmark + embedding tables** (`appendix_c` MMLU/GSM8K/HumanEval + MTEB): the listed models no
>   longer exist — **rebuild the tables around the current frontier**, don't patch the numbers.
> - **API model IDs** (`appendix_b`): `claude-sonnet-4-20250514` → `claude-sonnet-4-6`; `gemini-2.0-pro`
>   → a current Gemini 3.x id.
> - **MCP / agent-framework landscape** (`ch08`): seed says "MCP supported by Claude, Cursor, Windsurf,
>   Cline as of early 2026" — understated. MCP was **donated to the Linux Foundation Dec 2025**
>   (OpenAI / Google / Microsoft co-sponsors); 10k+ public servers; first-party support now spans
>   OpenAI/ChatGPT, Google/Gemini, Microsoft, GitHub, VS Code, Cursor.
> - **OWASP LLM Top 10** (`ch11` safety → guide-3 Ch 8 guardrails): seed cites "v1.1, 2024" — current is
>   the **2025 edition** (adds System Prompt Leakage = LLM07:2025, Vector & Embedding Weaknesses =
>   LLM08:2025; Prompt Injection still LLM01).
> - **GPU economics** (`ch13`: A100 ~$2/hr, H100 ~$4/hr): re-verify at authoring; rates have trended down.

| Ch | Title | Primary seed (`~/interview_prep_series`) | Companion |
|----|-------|------------------------------------------|-----------|
| 0 | Why production is where AI systems live or die | vol09 ch18 (mindset) · vol08 ch12 | — |
| 1 | Deploying AI safely — shadow, canary, flags, fallback | vol08 ch12 (reference architecture, model fallback) · vol09 ch18 | — |
| 2 | Latency anatomy — TTFT, decode, and where time goes | vol09 ch15 · vol08 ch6 (prefill-vs-decode, KV cache) | `mini_prod.latency` |
| 3 | Throughput & efficiency levers — quantization, batching, speculation | vol08 ch6 · vol09 ch15 (continuous batching, PagedAttention, spec-decode) | extends `latency` |
| 4 | Cost engineering — routing, cascades, caching economics | vol08 ch13 · vol09 ch15 (cascades) | `mini_prod.cascade` (reuses `mini_rag.budget`) |
| 5 | The observability stack — metrics, logs, traces, evals | vol09 ch16 (4 pillars, OTel/spans, 3 layers) | `mini_prod.trace` |
| 6 | Evaluating in production — shadow evals, sampling, regression gates | vol09 ch16 · ch18 step-5 template · guide-1 ch11 bridge | `mini_prod.monitor` (reuses `mini_eval`) |
| 7 | Drift & quality decay — detecting the slow failure | vol09 ch16 (rolling windows, rank tests, SLO alerting) | `mini_prod.drift` |
| 8 | Guardrails in production — input/output gates, injection at runtime | vol08 ch12 (guardrails layer) · vol09 ch17 · vol25 ch16 | — (gated-write pattern reuses `mini_agent`) |
| 9 | Incidents & reliability ops — SLOs, runbooks, degradation modes | vol09 ch16 (SLO alerting + runbooks) | — |
| 10 | Self-host vs API vs hybrid (judgment) | vol08 ch13 (break-even) · vol09 ch15 | — |
| 11 | System-design capstone — production-grade | vol09 ch18 (5-step + step-5 eval template, walkthroughs) · vol08 ch12 | — |
| 12 | Interview craft & transfer — the production story | all six seeds' level cards · demand-spine failure modes | — |

Chapter-block handoffs (narrative chain, same discipline as guide #2): Ch 0 names the loop →
Ch 1 deploys into it → Ch 2–4 make serving fast and affordable → Ch 5 makes the system
visible → Ch 6–7 make quality measurable and its decay detectable → Ch 8–9 handle the bad
day → Ch 10 the standing judgment call → Ch 11–12 demonstrate transfer.

## Companion plan — `mini_prod` (shape decided at this planning pass)

One new stdlib-only package, **`mini_prod`** — "for learning, not production" — that *imports*
the earlier companions rather than rebuilding them (`mini_eval` = measurement, `mini_rag` =
the served pipeline + budget math, `mini_agent` = gated actions):

- **`latency`** (Ch 2–3): TTFT/decode-time estimator (prefill compute-bound vs decode
  memory-bound rules of thumb), deterministic queue/batching simulation, percentile math
  (p50/p99 from first principles).
- **`cascade`** (Ch 4): confidence-thresholded router + escalation, misrouting cost curves;
  reuses `mini_rag.budget.api_cost` for the economics.
- **`trace`** (Ch 5): span tree (start/end/attrs) + rollups — the OTel mental model without
  the dependency.
- **`monitor`** (Ch 6): traffic sampling + golden-set regression gate; scoring delegates to
  `mini_eval` (judge + metrics) — reuse is the lesson, mirroring guide-2 Ch 5.
- **`drift`** (Ch 7): rolling quality windows + Mann–Whitney U (stdlib implementation) +
  SLO-style alert rules.

Every module: tested, deterministic, bridged at chapter close to the production tool
(vLLM / OpenTelemetry / Arize Phoenix / LangSmith / provider routing).

## Chapter shape (§5) — same as guides 1–2

`<YouWillLearn>` → productive-failure opener + `<Pitfall>` → principle (+ code / KaTeX where
it carries load) → **ICAP island** (`client:visible`, frozen / no-model) → `<Practice>` with
`<details>` → `## How this is graded` (4-dim rubric) + `### Industry variation` → `## Stretch`.
`los[].anchor` ↔ `{/* anchor: <slug> */}` bijective in every chapter.

**Island candidates** (decide per-chapter at authoring): `ScenarioQuiz` reuse (Ch 0, 9, 11,
12 — hand-authored JSON only, never fabricated model output); computed candidates —
latency-anatomy explorer (Ch 2, from `mini_prod.latency`), cascade/cost explorer (Ch 4),
span-waterfall explorer (Ch 5), drift-window explorer (Ch 7 — guide-1's `DriftMonitorExplorer`
may reuse directly; check its data contract before building a new island).

## Demo policy (frozen / no-model)

Unchanged from guides 1–2: computed demo JSON from `scripts/build_demo_data.py` (seeded,
deterministic, emitted by `mini_prod`); hand-authored quiz JSON wherever live model outputs
would otherwise be fabricated.

## Industry-variation callouts to thread

Startup (monitoring debt vs ship velocity — when is a dashboard premature?) · enterprise
(audit trails, per-tenant isolation, change control) · fintech/regulated (explainability,
incident disclosure duties) · marketplace (latency SLAs as revenue) · frontier-lab
(research-to-prod velocity; the stack is assumed). IC4-vs-IC5 signals from the seeds' level
cards: IC5 leads with requirements/SLOs before boxes, estimates compute/memory/cost
unprompted, brings up eval before being asked.

## Completion gate (replicates guides 1–2)

Independent multi-agent review (math+facts / demo-honesty+islands / pedagogy+continuity) →
findings doc → all fixes applied → LOS anchors bijective → build + validate green → all
companion tests pass. Only then is guide #3 complete.
