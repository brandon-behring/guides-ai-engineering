"""Correctness tests for mini_eval. Run with `pytest`, or directly:
`python companion/tests/test_mini_eval.py` (no pytest needed)."""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_eval import (  # noqa: E402
    confusion_counts, precision, recall, f1, accuracy, metrics_at,
    threshold_sweep, average_precision,
    bootstrap_ci, paired_diff_ci, permutation_test,
    brier_score, reliability_curve, expected_calibration_error,
    precision_at_k, recall_at_k, reciprocal_rank, ndcg_at_k,
    pass_at_k, mean_pass_at_k,
    Response, PairwiseJudge, position_flip_rate, judge_accuracy,
)


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def _synth(n, prevalence, mu_pos, mu_neg, sd, seed):
    """A synthetic scored dataset: labels ~ Bernoulli(prevalence), scores Gaussian."""
    rng = random.Random(seed)
    yt, ys = [], []
    for _ in range(n):
        pos = rng.random() < prevalence
        yt.append(1 if pos else 0)
        ys.append(_clip(rng.gauss(mu_pos if pos else mu_neg, sd)))
    return yt, ys


def _synth_ab(n, prevalence, mua, mub, sd, seed):
    """Two models scored on the *same* labels; mua/mub are (pos_mean, neg_mean)."""
    rng = random.Random(seed)
    yt, sa, sb = [], [], []
    for _ in range(n):
        pos = rng.random() < prevalence
        yt.append(1 if pos else 0)
        sa.append(_clip(rng.gauss(mua[0] if pos else mua[1], sd)))
        sb.append(_clip(rng.gauss(mub[0] if pos else mub[1], sd)))
    return yt, sa, sb


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


def test_bootstrap_ci_brackets_point_and_shrinks_with_n():
    yt, ys = _synth(1000, 0.4, 0.60, 0.42, 0.18, seed=11)
    point = recall(confusion_counts(yt, ys, 0.5))
    lo, hi = bootstrap_ci(yt, ys, 0.5, recall, n_boot=300, seed=1)
    assert lo <= point <= hi  # the CI contains the point estimate
    wide = bootstrap_ci(yt[:100], ys[:100], 0.5, recall, n_boot=300, seed=1)
    assert (hi - lo) < (wide[1] - wide[0])  # 10x the data -> a tighter interval


def test_bootstrap_ci_deterministic_under_seed():
    yt, ys = _synth(300, 0.4, 0.60, 0.42, 0.18, seed=5)
    a = bootstrap_ci(yt, ys, 0.5, f1, n_boot=200, seed=42)
    b = bootstrap_ci(yt, ys, 0.5, f1, n_boot=200, seed=42)
    assert a == b  # same seed -> identical interval


def test_paired_diff_ci_real_difference_and_identical():
    # B is clearly separated; A overlaps heavily -> a difference that survives noise.
    yt, sa, sb = _synth_ab(400, 0.4, (0.55, 0.45), (0.78, 0.22), 0.16, seed=3)
    res = paired_diff_ci(yt, sa, sb, 0.5, f1, n_boot=300, seed=2)
    assert res["diff"] > 0 and res["excludes_zero"] is True
    # A model compared with itself: zero difference, CI straddles zero.
    same = paired_diff_ci(yt, sa, sa, 0.5, f1, n_boot=300, seed=2)
    assert same["diff"] == 0.0 and same["excludes_zero"] is False


def test_permutation_test_real_vs_null():
    yt = [1] * 10 + [0] * 10
    perfect = [1.0] * 10 + [0.0] * 10  # recall 1.0
    nothing = [0.0] * 20               # predicts all negative -> recall 0.0
    p_real = permutation_test(yt, nothing, perfect, 0.5, recall, n_perm=1000, seed=7)
    assert p_real < 0.05               # a real gap is hard for chance to reproduce
    p_null = permutation_test(yt, perfect, perfect, 0.5, recall, n_perm=1000, seed=7)
    assert p_null > 0.5                # no gap -> nothing to detect


def test_brier_perfect_and_worst():
    assert brier_score([1, 0, 1, 0], [1.0, 0.0, 1.0, 0.0]) == 0.0  # perfect
    assert brier_score([1, 0, 1, 0], [0.0, 1.0, 0.0, 1.0]) == 1.0  # maximally wrong


def test_ece_zero_for_calibrated():
    # Each discrete confidence level has a matching empirical positive rate ->
    # confidence == accuracy in every bin -> ECE is exactly zero.
    yt, yp = [], []
    for p, n_ex in [(0.1, 20), (0.5, 20), (0.9, 20)]:
        n_pos = round(p * n_ex)
        yt += [1] * n_pos + [0] * (n_ex - n_pos)
        yp += [p] * n_ex
    assert expected_calibration_error(yt, yp, n_bins=10) < 1e-9


def test_ece_positive_for_overconfident():
    # Says 0.9 on a batch that is right only half the time -> a 0.4 gap.
    yt = [1] * 10 + [0] * 10
    yp = [0.9] * 20
    ece = expected_calibration_error(yt, yp, n_bins=10)
    assert abs(ece - 0.4) < 1e-9


def test_reliability_curve_counts_sum():
    yt, yp = _synth(500, 0.4, 0.62, 0.40, 0.18, seed=8)
    curve = reliability_curve(yt, yp, n_bins=10)
    assert sum(b["count"] for b in curve) == 500
    # every non-empty bin's accuracy and confidence are valid probabilities
    assert all(0.0 <= b["accuracy"] <= 1.0 and 0.0 <= b["confidence"] <= 1.0 for b in curve)


def test_retrieval_precision_recall_at_k():
    retrieved = ["a", "b", "c", "d"]
    relevant = {"a", "c"}
    assert precision_at_k(retrieved, relevant, 2) == 0.5   # top-2 = a,b -> 1 hit / 2
    assert recall_at_k(retrieved, relevant, 2) == 0.5      # found a of {a,c}
    assert recall_at_k(retrieved, relevant, 4) == 1.0      # both relevant in top-4


def test_reciprocal_rank_and_ndcg_order():
    assert reciprocal_rank(["x", "a", "y"], {"a"}) == 0.5  # first hit at rank 2
    perfect = ndcg_at_k(["a", "b", "c"], {"a", "b"}, 3)     # relevant ranked first
    worse = ndcg_at_k(["c", "b", "a"], {"a", "b"}, 3)       # relevant ranked last
    assert abs(perfect - 1.0) < 1e-9 and worse < perfect    # NDCG rewards ordering


def test_pass_at_k_basic_and_monotonic():
    assert abs(pass_at_k(10, 3, 1) - 0.3) < 1e-9  # pass@1 == c/n
    assert pass_at_k(10, 0, 5) == 0.0            # never correct
    assert pass_at_k(10, 8, 5) == 1.0            # only 2 failures: 5 draws must hit one
    vals = [pass_at_k(20, 4, k) for k in range(1, 21)]
    assert all(vals[i] <= vals[i + 1] + 1e-12 for i in range(len(vals) - 1))  # rises with k


def test_mean_pass_at_k():
    tasks = [(10, 5), (10, 0), (10, 10)]
    assert abs(mean_pass_at_k(tasks, 1) - (0.5 + 0.0 + 1.0) / 3) < 1e-9


def test_average_precision_handles_ties_and_interior():
    # All scores tied: a threshold can't split them, so AP must not depend on the
    # arbitrary input order — and equals total_pos / n (precision at full recall).
    for labels in ([1, 0, 1, 0], [0, 0, 1, 1], [1, 1, 0, 0]):
        assert abs(average_precision(labels, [0.5] * 4) - 0.5) < 1e-9
    # An interior ranking with a known closed form: positives at ranks 1, 3, 4.
    ap = average_precision([1, 0, 1, 1, 0], [0.9, 0.8, 0.7, 0.6, 0.5])
    assert abs(ap - (1 + 2 / 3 + 3 / 4) / 3) < 1e-9


def test_brier_interior_value():
    # (0.7 - 1)^2 + (0.2 - 0)^2 = 0.09 + 0.04, divided by 2.
    assert abs(brier_score([1, 0], [0.7, 0.2]) - 0.065) < 1e-9


def test_permutation_test_moderate_gap():
    # A genuine but non-saturated B-advantage: chance reproduces it rarely (small p);
    # a negligible gap stays unresolved (large p). Exercises the interior of the
    # estimator, not just the perfect-vs-nothing extreme.
    yt, sa, sb = _synth_ab(80, 0.5, (0.55, 0.45), (0.72, 0.40), 0.15, seed=4)
    p = permutation_test(yt, sa, sb, 0.5, f1, n_perm=2000, seed=9)
    assert 0.0 < p < 0.05
    assert p == permutation_test(yt, sa, sb, 0.5, f1, n_perm=2000, seed=9)  # deterministic
    yt2, sa2, sb2 = _synth_ab(80, 0.5, (0.55, 0.45), (0.58, 0.44), 0.15, seed=4)
    p_tiny = permutation_test(yt2, sa2, sb2, 0.5, f1, n_perm=2000, seed=9)
    assert p_tiny > 0.3 and p_tiny > p  # a smaller true effect -> a larger p-value


def test_retrieval_dedup_bounds():
    # A duplicated relevant doc must not push recall above 1.0 or inflate precision.
    assert recall_at_k(["a", "a"], {"a"}, 2) == 1.0
    assert precision_at_k(["a", "a"], {"a"}, 2) == 0.5  # one distinct hit / k=2


def test_unbiased_judge_no_flip_on_equal_pair():
    # Equal quality AND equal length, no bias: nothing for order to bias, so the
    # flip rate is 0 — the arbitrary tie-break must not be charged as position bias.
    pairs = [(Response("a", "xx", 0.5), Response("b", "yy", 0.5))]
    assert position_flip_rate(PairwiseJudge(), pairs) == 0.0


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
