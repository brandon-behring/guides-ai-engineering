"""Calibration — does a predicted probability mean what it says?

A classifier can *rank* perfectly (AUC near 1) and still be a liar about
probabilities: it says "90% sure" on a batch that's right only 60% of the time.
When the probability is the product — an insurance price, a risk score a human acts
on — that gap *is* the failure, and ranking metrics never see it.

This module measures the gap three ways, all from ``(y_true, y_prob)`` with no
library:

- ``brier_score`` — mean squared error of the probabilities (a proper scoring rule).
- ``reliability_curve`` — bin by predicted probability; per bin, the mean confidence
  vs. the empirical accuracy. The data behind a calibration (reliability) diagram.
- ``expected_calibration_error`` — the bin-count-weighted average gap between
  confidence and accuracy. One number for "how miscalibrated is it?".

Stdlib-only, **for learning, not production** (bridge to sklearn's calibration
tools / temperature scaling when it counts).
"""

from __future__ import annotations


def _check(y_true: list[int], y_prob: list[float]) -> None:
    if len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must be the same length")


def brier_score(y_true: list[int], y_prob: list[float]) -> float:
    """Mean squared error between the predicted probability and the 0/1 outcome.
    0 is perfect; 0.25 is the chance baseline of always guessing 0.5; 1 is worst."""
    _check(y_true, y_prob)
    if not y_true:
        return 0.0
    return sum((p - y) ** 2 for y, p in zip(y_true, y_prob)) / len(y_true)


def reliability_curve(
    y_true: list[int], y_prob: list[float], n_bins: int = 10
) -> list[dict]:
    """Bin predictions into ``n_bins`` equal-width probability bins; per bin report
    mean confidence, empirical accuracy (positive rate), and count. The diagonal
    confidence == accuracy is perfect calibration; bins below it are overconfident.
    An empty bin reports confidence = accuracy = 0.0 as a sentinel (ECE skips it;
    filter on ``count > 0`` before plotting)."""
    _check(y_true, y_prob)
    sums = [0.0] * n_bins      # sum of predicted probs (confidence)
    hits = [0] * n_bins        # count of positives (for accuracy)
    counts = [0] * n_bins
    for y, p in zip(y_true, y_prob):
        b = min(n_bins - 1, int(p * n_bins))
        sums[b] += p
        hits[b] += y
        counts[b] += 1
    curve = []
    for b in range(n_bins):
        c = counts[b]
        curve.append({
            "lo": b / n_bins,
            "hi": (b + 1) / n_bins,
            "count": c,
            "confidence": (sums[b] / c) if c else 0.0,
            "accuracy": (hits[b] / c) if c else 0.0,
        })
    return curve


def expected_calibration_error(
    y_true: list[int], y_prob: list[float], n_bins: int = 10
) -> float:
    """ECE: the average gap |accuracy − confidence| across bins, weighted by how
    many predictions fall in each. The headline calibration number."""
    n = len(y_true)
    if n == 0:
        return 0.0
    curve = reliability_curve(y_true, y_prob, n_bins)
    return sum(
        b["count"] / n * abs(b["accuracy"] - b["confidence"])
        for b in curve if b["count"]
    )
