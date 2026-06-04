# guides-ai-engineering

The **AI-native dimensions of AI engineering** — company-agnostic, interview-prep-led
guides for engineers moving into AI-native roles. Deploys to
`guides.brandon-behring.dev/ai-engineering/`; part of the
[guides](https://github.com/brandon-behring/guides) hub.

Multi-guide repo: each guide is an Astro **content collection**. Built with
[`@brandon_m_behring/book-scaffold-astro`](https://github.com/brandon-behring/book-scaffold-astro)
(v4.14+).

## What makes these different

- **Organized by demand, not by topic-list.** Chapters are framed by what
  AI-engineering interviews actually test and the documented reasons strong
  candidates fail — and taught for *transfer* to novel problems (productive-failure
  openers, worked-example fading, interleaved retrieval, stretch problems).
- **A four-dimension rubric as the spine.** Every chapter grades against Technical
  Correctness · Trade-off Awareness · Evaluation Rigor · Communication.
- **Build-your-own companion.** You construct a minimal library (`mini_eval`,
  here) chapter-by-chapter to learn the mechanism, then bridge to the production
  tool (`eval-toolkit`, RAGAS). It also powers the interactive demos.
- **Static, client-side interactive demos.** The `dump → JSON → Preact island`
  pattern: all computation happens offline in the companion; the browser only
  reads JSON. No model, no server.

## Guides

| Guide | Status |
| --- | --- |
| **Evaluation & benchmarking** (`src/content/evaluation/`) | in progress — Ch 0, 2, 7 + `mini_eval` core |

(llm-app-engineering, production, craft, working-with-AI to follow.)

## Layout

```
src/content/evaluation/   chapters (MDX)
src/components/            Preact island demos (ThresholdExplorer, JudgeBiasExplorer)
src/data/                  precomputed demo JSON (generated, see scripts/)
companion/                 the build-your-own companion lib (mini_eval) + tests
scripts/build_demo_data.py generates the demo JSON from mini_eval
```

## Develop

```bash
npm install
npm run dev                      # local dev server
npm run build                    # production build
python3 companion/tests/test_mini_eval.py   # companion correctness tests
python3 scripts/build_demo_data.py          # regenerate demo data
```

## License

Content CC BY 4.0; code (companion, scripts, components) MIT. AI-collaboration
disclosure: see `/ai-engineering/authors`.
