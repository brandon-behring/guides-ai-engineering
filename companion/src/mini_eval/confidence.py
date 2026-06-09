"""Is the number real? — bootstrap confidence intervals and a paired model test.

A metric computed on a finite eval set is itself a random quantity: run the same
system on a different sample and you'd get a slightly different number. This module
puts *error bars* on the metrics from `metrics`, and answers the question every
model comparison really asks — **is B actually better than A, or is the lead
inside the noise?** — two ways:

- ``bootstrap_ci`` — a percentile confidence interval for one metric, by resampling
  the eval set with replacement (Chapter 3, "report a number with its uncertainty").
- ``paired_diff_ci`` — a bootstrap CI on the *difference* metric(B) − metric(A),
  evaluated on the *same* resampled examples (paired, so per-example difficulty
  cancels — the dominant variance component on most eval sets).
- ``permutation_test`` — a non-parametric p-value for "B ≠ A" by repeatedly swapping
  which model each example belongs to and seeing how often chance reproduces the
  observed gap.

Stdlib-only, seeded, **for learning, not production** (reach for scipy / a real
bootstrap library when it counts). Everything is built on `confusion_counts` and a
metric function (``precision``/``recall``/``f1``/...) from `metrics`, so a "metric"
here is anything of the shape ``Counts -> float``.
"""

from __future__ import annotations

from .metrics import Counts, confusion_counts
import random


def _percentile(xs_sorted: list[float], q: float) -> float:
    """Linear-interpolated percentile of an already-sorted list. q in [0, 1]."""
    if not xs_sorted:
        return 0.0
    if len(xs_sorted) == 1:
        return xs_sorted[0]
    pos = q * (len(xs_sorted) - 1)
    lo = int(pos)
    frac = pos - lo
    if lo + 1 < len(xs_sorted):
        return xs_sorted[lo] * (1 - frac) + xs_sorted[lo + 1] * frac
    return xs_sorted[lo]


def _metric_on_indices(
    y_true: list[int], y_score: list[float], idx: list[int],
    threshold: float, metric_fn,
) -> float:
    """Apply ``metric_fn`` to the confusion counts of the resampled subset ``idx``."""
    yt = [y_true[i] for i in idx]
    ys = [y_score[i] for i in idx]
    return metric_fn(confusion_counts(yt, ys, threshold))


def bootstrap_ci(
    y_true: list[int], y_score: list[float], threshold: float, metric_fn,
    n_boot: int = 1000, ci: float = 0.95, seed: int | None = None,
) -> tuple[float, float]:
    """Percentile bootstrap CI for ``metric_fn`` at ``threshold``.

    Resample ``len(y_true)`` examples with replacement ``n_boot`` times, recompute
    the metric on each resample, and return the (lower, upper) percentiles for the
    requested confidence level. The interval narrows as the eval set grows — the
    whole reason a number from 50 examples and a number from 5,000 are not the same
    claim."""
    n = len(y_true)
    rng = random.Random(seed)
    vals = [
        _metric_on_indices(
            y_true, y_score, [rng.randrange(n) for _ in range(n)], threshold, metric_fn
        )
        for _ in range(n_boot)
    ]
    vals.sort()
    alpha = 1.0 - ci
    return _percentile(vals, alpha / 2), _percentile(vals, 1.0 - alpha / 2)


def paired_diff_ci(
    y_true: list[int], score_a: list[float], score_b: list[float], threshold: float,
    metric_fn, n_boot: int = 1000, ci: float = 0.95, seed: int | None = None,
    return_dist: bool = False,
) -> dict:
    """Bootstrap CI on the difference metric(B) − metric(A), paired by example.

    Both models are scored on the *same* resampled examples each round, so a hard
    batch of examples raises (or lowers) both metrics together and cancels out of
    the difference. ``excludes_zero`` is the headline: if the CI doesn't straddle 0,
    the difference survives sampling noise at this confidence level. (A bound that
    lands exactly on 0 counts as *not* excluding — the conservative call.) Pass
    ``return_dist=True`` to also get the raw bootstrap differences (for a histogram)."""
    if not (len(y_true) == len(score_a) == len(score_b)):
        raise ValueError("y_true, score_a, score_b must be the same length")
    n = len(y_true)
    point = (
        metric_fn(confusion_counts(y_true, score_b, threshold))
        - metric_fn(confusion_counts(y_true, score_a, threshold))
    )
    rng = random.Random(seed)
    diffs = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]  # one resample, used for both models
        m_b = _metric_on_indices(y_true, score_b, idx, threshold, metric_fn)
        m_a = _metric_on_indices(y_true, score_a, idx, threshold, metric_fn)
        diffs.append(m_b - m_a)
    diffs.sort()
    alpha = 1.0 - ci
    lo = _percentile(diffs, alpha / 2)
    hi = _percentile(diffs, 1.0 - alpha / 2)
    out = {"diff": point, "lo": lo, "hi": hi, "excludes_zero": lo > 0.0 or hi < 0.0}
    if return_dist:
        out["dist"] = diffs
    return out


def permutation_test(
    y_true: list[int], score_a: list[float], score_b: list[float], threshold: float,
    metric_fn, n_perm: int = 10000, seed: int | None = None,
) -> float:
    """Two-sided paired permutation p-value for "metric(B) ≠ metric(A)".

    Under the null, the two models are exchangeable per example, so we repeatedly
    flip a coin for each example to decide which model's score plays "A" vs "B",
    recompute the metric difference, and count how often chance reaches the observed
    gap. Uses add-one smoothing so a p-value is never exactly 0."""
    obs = abs(
        metric_fn(confusion_counts(y_true, score_b, threshold))
        - metric_fn(confusion_counts(y_true, score_a, threshold))
    )
    rng = random.Random(seed)
    at_least = 0
    for _ in range(n_perm):
        sa, sb = [], []
        for a_i, b_i in zip(score_a, score_b):
            if rng.random() < 0.5:
                sa.append(b_i); sb.append(a_i)  # swap which model is A vs B
            else:
                sa.append(a_i); sb.append(b_i)
        d = abs(
            metric_fn(confusion_counts(y_true, sb, threshold))
            - metric_fn(confusion_counts(y_true, sa, threshold))
        )
        if d >= obs - 1e-12:  # tolerance absorbs float noise on metrics in [0, 1]
            at_least += 1
    return (at_least + 1) / (n_perm + 1)
