# Guide #2 — LLM Application Engineering (outline + status)

The second guide in the AI-engineering series: **building reliable systems on top of
models.** RAG-centric spine; agents and system design build on it. Company-agnostic,
interview-prep-led, taught for transfer. Audience: engineers moving into AI-native roles
(SWE/DS background assumed; foundations linked, not re-taught).

Direction: `~/guides/docs/plans/active/2026-06-04_session_handoff.md` (canonical) ·
demand spine: `~/guides/docs/research/role_demand_and_interview_signals/`.

## Status (2026-06-09)

- **Ch 0–1 authored** in the §5 shape; both reuse the `ScenarioQuiz` island (no fabricated
  model outputs). Quiz data hand-authored: `src/data/llm_claims_demo.json`,
  `src/data/prompt_robustness_demo.json`.
- **`mini_rag` companion seeded** — `companion/src/mini_rag/search.py` (TF-IDF + cosine + top_k)
  + `companion/tests/test_mini_rag.py`.
- Multi-guide routing live: a `generateId` on the chapters glob namespaces each id by its
  guide folder, so chapters serve at `/ai-engineering/chapters/<guide>/<slug>/` (e.g.
  `…/chapters/llm-app-engineering/why-llm-app-engineering/`). Slugs only need to be unique
  *within* a guide. (The `/chapters/` index still mixes both guides; per-guide grouping waits
  on scaffold #15.)
- **Next:** Ch 2 (Retrieval 101) — the first chapter to actually import `mini_rag`.

## Spine & outline (RAG-centric, ~13 ch)

Demand basis: RAG ~20% of AI-eng interviews (top non-foundational topic), agentic ~15%,
production/cost-latency ~18%, prompting/structured-output ~10%. "Transform, not port" the
seeds; agnosticize the insurance-domain framing.

| Ch | Title | Primary seed (`~/interview_prep_series`) | Companion |
|----|-------|------------------------------------------|-----------|
| 0 | Why app-eng is the scarce skill (RAG framing) | demand spine; vol09 ch2 | — |
| 1 | Prompt engineering as a discipline | vol08 ch3 · vol09 ch3 · AIES ch4 | — |
| 2 | Retrieval 101 — embeddings & vector search | vol08 ch10 · vol09 ch5 | `mini_rag.search` |
| 3 | Chunking & document representation | vol09 ch4 | `mini_rag.chunk` |
| 4 | RAG end-to-end (retrieve → generate) | vol09 ch6 · vol08 ch4 | `mini_rag.pipeline` |
| 5 | Evaluating RAG (bridges Guide 1) | vol09 ch9 (cross-ref `mini_eval.retrieval`) | bridge |
| 6 | Advanced RAG (rerank, HyDE, routing) | vol09 ch6 · vol08 ch10 | `mini_rag.rerank` |
| 7 | RAG in production (latency, cost) | vol09 ch15–16 | `mini_rag` profiler |
| 8 | Agents & tool use | vol08 ch8 · vol09 ch7 · ch11 (MCP) | `mini_agent.loop` |
| 9 | Multi-agent orchestration | vol09 ch12 · ch10 (frameworks) | `mini_agent` |
| 10 | Fine-tune vs RAG vs prompt (judgment) | vol09 ch13 (lightweight; demoted) | — |
| 11 | System-design capstone | vol09 ch18 · AIES ch5–6 | — |
| 12 | Interview craft & transfer | vol09 ch19–20 · AIES ch11 | — |

## Companion plan

One shared `companion/` (stdlib-only, "for learning, not production"):
- **`mini_rag`** (ch2–7): `search` (TF-IDF + cosine + top_k) → `chunk` → `pipeline`
  (retrieve→assemble→answer) → `rerank`. Ch 5 bridges to `mini_eval.retrieval` (which *scores*
  rankings) and RAGAS. `mini_rag` is the *mechanism*; `mini_eval` is the *measurement*.
- **`mini_agent`** (ch8–9): a ReAct-style `loop` (think→act→observe) + simple multi-agent coordination.
- Bridges: each chapter closes by mapping the toy to what LangChain / LlamaIndex / RAGAS /
  Anthropic primitives do in production.

## Chapter shape (§5) — same as guide 1

`<YouWillLearn>` → productive-failure opener + `<Pitfall>` → principle (+ code / KaTeX where it
carries load) → **ICAP island** (`client:visible`, frozen / no-model) → `<Practice difficulty>`
with `<details>` → `## How this is graded` (4-dim rubric) + `### Industry variation` → `## Stretch`.
Frontmatter carries `los[]`; **every `los[].anchor` must have a matching `{/* anchor: <slug> */}`
in prose** (bijective — the build doesn't enforce it; scaffold #130 would).

**4-dimension rubric (cross-guide spine):** Technical Correctness · Trade-off Awareness ·
Evaluation Rigor · Communication.

## Demo policy (frozen / no-model)

Public demos never call a live model. Two kinds of demo JSON in `src/data/`:
- **Computed** (sweeps, curves) → emitted by `scripts/build_demo_data.py` (seeded, deterministic).
- **Authored** (ScenarioQuiz items: prompt / candidates / correct / explanation / principle) →
  hand-written JSON, committed directly (e.g. `benchmark_demo.json`, `llm_claims_demo.json`).

## Industry-variation callouts to thread

Startup ship-velocity · enterprise RAG maturity + data isolation · fintech compliance/explainability ·
marketplace latency SLAs · frontier-lab research-to-prod. (Frontier-lab is a cross-cutting callout,
not a chapter.) AI-assisted-coding-interview skill (clarify→pseudocode→prompt→review→run→explain)
lands in Ch 12.
