"""Correctness tests for mini_eval. Run with `pytest`, or directly:
`python companion/tests/test_mini_eval.py` (no pytest needed)."""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_eval import (  # noqa: E402
    confusion_counts, precision, recall, f1, accuracy, metrics_at,
    threshold_sweep, average_precision,
    Response, PairwiseJudge, position_flip_rate, judge_accuracy,
)


def test_confusion_counts_and_metrics():
    y_true = [1, 1, 0, 0, 1, 0]
    y_score = [0.9, 0.4, 0.8, 0.2, 0.6, 0.1]
    c = confusion_counts(y_true, y_score, threshold=0.5)
    # predicted positive: 0.9,0.8,0.6 -> tp(0.9,0.6)=2, fp(0.8)=1; fn(0.4)=1, tn(0.2,0.1)=2
    assert (c.tp, c.fp, c.tn, c.fn) == (2, 1, 2, 1)
    assert abs(precision(c) - 2 / 3) < 1e-9
    assert abs(recall(c) - 2 / 3) < 1e-9
    assert abs(f1(c) - 2 / 3) < 1e-9


def test_accuracy_paradox():
    # 95% negatives; a classifier that flags nothing is 95% accurate, 0% recall.
    y_true = [0] * 95 + [1] * 5
    y_score = [0.0] * 100  # never crosses threshold -> all predicted negative
    m = metrics_at(y_true, y_score, threshold=0.5)
    assert abs(m["accuracy"] - 0.95) < 1e-9
    assert m["recall"] == 0.0  # the metric that lies, exposed


def test_threshold_sweep_recall_monotonic():
    y_true = [1, 0, 1, 0, 1]
    y_score = [0.8, 0.7, 0.5, 0.3, 0.9]
    sweep = threshold_sweep(y_true, y_score, n_steps=51)
    recalls = [row["recall"] for row in sweep]
    # raising the threshold can only drop (never raise) recall
    assert all(recalls[i] >= recalls[i + 1] for i in range(len(recalls) - 1))


def test_average_precision_perfect_ranking():
    y_true = [1, 1, 0, 0]
    y_score = [0.9, 0.8, 0.3, 0.1]  # all positives ranked above all negatives
    assert abs(average_precision(y_true, y_score) - 1.0) < 1e-9


def test_unbiased_judge_recovers_truth():
    pairs = [
        (Response("a", "x", 0.9), Response("b", "y", 0.4)),
        (Response("c", "z", 0.2), Response("d", "w", 0.8)),
    ]
    j = PairwiseJudge()  # no biases
    assert judge_accuracy(j, pairs) == 1.0
    assert position_flip_rate(j, pairs) == 0.0


def test_position_bias_flips_verdicts():
    # Two near-equal responses; a position bonus larger than the quality gap
    # makes whoever-is-first win -> the verdict flips on swap.
    pairs = [(Response("a", "aa", 0.51), Response("b", "bb", 0.49))]
    biased = PairwiseJudge(position_bias=0.1)
    assert position_flip_rate(biased, pairs) == 1.0
    assert biased.judge_debiased(*pairs[0]) == "tie"  # the swap catches it


def test_verbosity_bias_rewards_length():
    short_good = Response("good", "short", 0.8)
    long_bad = Response("bad", "x" * 200, 0.5)
    j = PairwiseJudge(verbosity_bias=0.01)  # +0.01 per char
    # long_bad gets +2.0 from length, overwhelming the 0.3 quality deficit
    assert j.judge(short_good, long_bad) == "bad"


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
