"""Generate precomputed JSON for the Evaluation guide's interactive demos.

The "dump" half of the dump -> JSON -> island pattern: all computation happens
here, offline, using the same `mini_eval` the reader builds; the browser islands
only read the JSON (no model, no server). Deterministic (seeded) so the committed
JSON is stable. Run: `python scripts/build_demo_data.py`.
"""

from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "companion", "src"))

from mini_eval import threshold_sweep, Response, PairwiseJudge, position_flip_rate  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "data")


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def threshold_demo() -> dict:
    """An imbalanced 'fraud-like' classifier: ~8% positive, overlapping scores.
    Ships the threshold sweep + a score histogram — enough for a slider-driven
    confusion matrix, PR curve, and score-distribution view."""
    rng = random.Random(7)
    n = 2000
    prevalence = 0.08
    y_true, y_score = [], []
    for _ in range(n):
        pos = rng.random() < prevalence
        # positives score higher on average, but the distributions overlap a lot
        mu = 0.68 if pos else 0.40
        sd = 0.16
        y_true.append(1 if pos else 0)
        y_score.append(_clamp01(rng.gauss(mu, sd)))

    sweep = threshold_sweep(y_true, y_score, n_steps=101)
    for row in sweep:  # round for compact, stable JSON
        for k, v in row.items():
            if isinstance(v, float):
                row[k] = round(v, 4)

    bins = 20
    pos_counts = [0] * bins
    neg_counts = [0] * bins
    for yt, s in zip(y_true, y_score):
        b = min(bins - 1, int(s * bins))
        (pos_counts if yt == 1 else neg_counts)[b] += 1

    return {
        "name": "Fraud-like classifier (synthetic, imbalanced)",
        "n": n,
        "pos": sum(y_true),
        "neg": n - sum(y_true),
        "prevalence": round(sum(y_true) / n, 4),
        "sweep": sweep,
        "hist": {"bins": bins, "pos": pos_counts, "neg": neg_counts},
    }


def judge_demo() -> dict:
    """Pairs where a small quality gap is overturned by position/verbosity bias.
    Ships each pair's verdict under naive vs debiased judging, plus aggregate
    position-flip rates, so the island can show verdicts flipping on order-swap."""
    pairs_raw = [
        ("Concise correct answer", 0.78, "Yes — use a cross-encoder reranker.", 0.70,
         "It depends; there are many factors to weigh here, and ultimately the "
         "best choice will come down to your specific latency and cost budget, "
         "the size of your candidate set, and how much retrieval quality matters."),
        ("Right call, terse", 0.81, "Cache the embeddings.", 0.74,
         "You could consider caching the embeddings, which is generally a good "
         "idea because recomputing them is expensive and the inputs rarely change."),
        ("Correct + short", 0.66, "Add a guardrail metric.", 0.61,
         "Adding a guardrail metric is one option among several; you might also "
         "track latency, cost, and a few business KPIs depending on the product."),
    ]
    pairs = []
    for i, (label, qa, ta, qb, tb) in enumerate(pairs_raw):
        a = Response(f"A{i}", ta, qa)   # better but shorter
        b = Response(f"B{i}", tb, qb)   # worse but much longer
        naive = PairwiseJudge(position_bias=0.06, verbosity_bias=0.0)
        verbose = PairwiseJudge(position_bias=0.0, verbosity_bias=0.0015)
        pairs.append({
            "label": label,
            "a": {"id": a.id, "text": a.text, "quality": qa, "len": len(ta)},
            "b": {"id": b.id, "text": b.text, "quality": qb, "len": len(tb)},
            "truth": a.id,  # A has higher latent quality in every pair
            "position": {
                "order_ab": naive.judge(a, b),
                "order_ba": naive.judge(b, a),
                "debiased": naive.judge_debiased(a, b),
            },
            "verbosity": {"order_ab": verbose.judge(a, b)},
        })

    pset = [(Response(p["a"]["id"], p["a"]["text"], p["a"]["quality"]),
             Response(p["b"]["id"], p["b"]["text"], p["b"]["quality"])) for p in pairs]
    return {
        "pairs": pairs,
        "position_flip_rate": round(position_flip_rate(
            PairwiseJudge(position_bias=0.06), pset), 3),
        "note": "A is the higher-quality answer in every pair. Watch the verdict.",
    }


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, data in [("threshold_demo", threshold_demo()), ("judge_demo", judge_demo())]:
        path = os.path.join(OUT, f"{name}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"wrote {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
