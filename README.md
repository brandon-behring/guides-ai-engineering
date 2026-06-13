# guides-ai-engineering

The **AI-native dimensions of AI engineering** — company-agnostic, interview-prep-led
guides for engineers moving into AI-native roles. **Read it live →
[guides-ai-engineering.brandon-m-behring.workers.dev](https://guides-ai-engineering.brandon-m-behring.workers.dev)**
(mounts at `guides.brandon-behring.dev/ai-engineering/` once the hub path proxy ships). Part
of the [guides](https://github.com/brandon-behring/guides) hub.

Multi-guide repo: each guide is an Astro **content collection**. Built with
[`@brandon_m_behring/book-scaffold-astro`](https://github.com/brandon-behring/book-scaffold-astro)
(v4.14.2).

## What makes these different

- **Organized by demand, not by topic-list.** Chapters are framed by what
  AI-engineering interviews actually test and the documented reasons strong
  candidates fail — and taught for *transfer* to novel problems (productive-failure
  openers, worked-example fading, interleaved retrieval, stretch problems).
- **A four-dimension rubric as the spine.** Every chapter grades against Technical
  Correctness · Trade-off Awareness · Evaluation Rigor · Communication.
- **Build-your-own companion.** You construct minimal libraries (`mini_eval`,
  `mini_rag`, `mini_agent`) chapter-by-chapter to learn the mechanism, then bridge
  to the production tool (`eval-toolkit`, RAGAS). They also power the interactive demos.
- **Static, client-side interactive demos.** The `dump → JSON → Preact island`
  pattern: all computation happens offline in the companion; the browser only
  reads JSON. No model, no server.

## Guides

| Guide | Status |
| --- | --- |
| **Evaluation & benchmarking** (`src/content/evaluation/`) | **complete** — 13 chapters, independently reviewed; `mini_eval` companion |
| **LLM application engineering** (`src/content/llm-app-engineering/`) | **complete** — 13 chapters, independently reviewed; `mini_rag` + `mini_agent` companions |
| **Production AI systems** (`src/content/production-ai-systems/`) | **in progress** — chapter 0 live; `mini_prod` companion to come |

(Craft and working-with-AI guides to follow.)

## Layout

```
src/content/<guide>/       chapters (MDX), one folder per guide
src/components/            Preact island demos (ThresholdExplorer, JudgeBiasExplorer, …)
src/data/                  demo JSON — computed (see scripts/) or hand-authored (quizzes)
companion/                 build-your-own companion libs (mini_eval, mini_rag) + tests
scripts/build_demo_data.py generates the computed demo JSON from the companion libs
```

## Develop

```bash
npm install
npm run dev                      # local dev server
npm run build                    # production build
python3 companion/tests/test_mini_eval.py   # companion correctness tests
python3 companion/tests/test_mini_rag.py    # companion correctness tests
python3 companion/tests/test_mini_agent.py  # companion correctness tests
python3 scripts/build_demo_data.py          # regenerate computed demo data
```

## License

Content (chapter prose/MDX, figures): **CC BY 4.0** — see [`LICENSE`](LICENSE).
Code (`companion/`, `scripts/`, `src/` components + config): **MIT** — see
[`LICENSE-MIT`](LICENSE-MIT). AI-collaboration disclosure: see
`/ai-engineering/authors`.
