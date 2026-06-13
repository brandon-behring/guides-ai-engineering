"""Evaluating in production — sampling live traffic and gating on the result.

You cannot run a full offline eval on every production request (Chapter 4: eval spend
is real). So eval-in-prod is *sampling*: score a fraction of live traffic with the same
metric you gate releases on, and decide whether quality has regressed. The catch this
module makes mechanical: because you sampled, the measured accuracy is an *estimate with
error*, so a regression gate must fire on whether a drop survives sampling noise — not on
the point estimate. That significance test is `mini_eval.confidence`, reused here exactly
as the Evaluation guide built it (reuse is the lesson — the metric and the test you gate
on in prod are the ones you validated offline).

Stdlib-only, **for learning, not production** — bridge to an eval platform (LangSmith,
Arize, Braintrust) that samples, scores with a judge, and tracks the gate over time.
"""

from __future__ import annotations

import random

from mini_eval.metrics import accuracy, confusion_counts
from mini_eval.confidence import paired_diff_ci


def sample(items: list, *, rate: float, seed: int) -> list:
    """Deterministically keep ~``rate`` of live traffic for scoring. You evaluate the
    sample, not the population — which is why the number you get has error bars."""
    if not 0.0 <= rate <= 1.0:
        raise ValueError("rate must be in [0, 1]")
    rng = random.Random(seed)
    return [x for x in items if rng.random() < rate]


def golden_accuracy(correct: list[int]) -> float:
    """Accuracy of a graded eval slice, computed through ``mini_eval`` — ``correct`` is
    per-item 1/0 (graded by a judge upstream). Treating each item as 'should be right'
    (label 1) makes accuracy = fraction correct, via the same metric used offline."""
    if not correct:
        raise ValueError("empty eval slice")
    y_true = [1] * len(correct)
    y_score = [float(c) for c in correct]
    return accuracy(confusion_counts(y_true, y_score, threshold=1.0))


def regression_gate(baseline_correct: list[int], candidate_correct: list[int], *,
                    margin: float = 0.0, n_boot: int = 1000, seed: int = 0) -> dict:
    """Promote a candidate only if it is not *significantly* worse than the baseline on
    the same sampled, graded items. Reuses ``mini_eval.confidence.paired_diff_ci`` to put
    a CI on (candidate − baseline) accuracy; the gate fails only when the whole CI sits
    below ``-margin`` — i.e. the regression is real, not sampling noise. A 2-point drop on
    40 samples usually straddles zero and should *not* block a release."""
    n = len(baseline_correct)
    if n != len(candidate_correct) or n == 0:
        raise ValueError("baseline and candidate must be equal, non-empty")
    y_true = [1] * n
    res = paired_diff_ci(y_true, [float(c) for c in baseline_correct],
                         [float(c) for c in candidate_correct], threshold=1.0,
                         metric_fn=accuracy, n_boot=n_boot, seed=seed)
    base = golden_accuracy(baseline_correct)
    cand = golden_accuracy(candidate_correct)
    real_regression = res["hi"] < -margin          # upper bound of the gain is still a loss
    return {
        "baseline_acc": round(base, 4),
        "candidate_acc": round(cand, 4),
        "delta": round(cand - base, 4),
        "ci_lo": round(res["lo"], 4),
        "ci_hi": round(res["hi"], 4),
        "significant": res["excludes_zero"],
        "passed": not real_regression,
        "reason": ("real regression: the difference CI is entirely below the margin"
                   if real_regression else
                   "within sampling noise (or not worse) — do not block on this"),
    }


def sampling_plan(*, qpd: int, rate: float, cost_per_eval_usd: float) -> dict:
    """The cost side of eval-in-prod (Chapter 4 again): sampling rate × volume × per-eval
    cost. A higher rate detects regressions faster and tighter, and costs more — the
    sampling rate is a detection-vs-spend dial, not a free setting."""
    if not 0.0 <= rate <= 1.0:
        raise ValueError("rate must be in [0, 1]")
    per_day = qpd * rate
    return {
        "sampled_per_day": round(per_day),
        "daily_cost": round(per_day * cost_per_eval_usd, 2),
        "monthly_cost": round(per_day * cost_per_eval_usd * 30, 2),
    }
