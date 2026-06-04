# companion — `mini_eval`

The **build-your-own** companion library for the AI Engineering guides. Deliberately
minimal, stdlib-only, **for learning, not production** — you build it
chapter-by-chapter to see the mechanism, then bridge to the production tools
(`eval-toolkit`, RAGAS, scikit-learn).

## Modules

- `mini_eval.metrics` — confusion matrix, precision/recall/F1/accuracy, the
  threshold sweep, average precision (Evaluation Ch 2).
- `mini_eval.judge` — a mock-model LLM-as-judge harness with position/verbosity
  bias and the swap-and-aggregate debias (Evaluation Ch 7).

Future guides add modules to the same package (`mini_rag`, `mini_agent`, ...).

## Use

```bash
python3 tests/test_mini_eval.py          # run the correctness tests (no pytest needed)
pip install -e .                          # or install editable (hatchling, src-layout)
```

```python
from mini_eval import threshold_sweep, PairwiseJudge, position_flip_rate
```

It is also the engine behind the guides' interactive demos: `scripts/build_demo_data.py`
runs these functions offline and dumps JSON the browser islands read.
