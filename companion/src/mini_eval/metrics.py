"""Classification metrics, from scratch — the threshold trade-off made mechanical.

`mini_eval` is the *build-your-own* companion to the Evaluation guide: deliberately
minimal, stdlib-only, and labelled **for learning, not production**. Each function
exists so you can see the mechanism (and explain it cold in an interview), then
bridge to the production tool (scikit-learn / `eval-toolkit`).

A binary classifier outputs a *score* in [0, 1]; a *threshold* turns scores into
labels. Every metric below is a function of where you put that threshold — which
is the whole point of Chapter 2.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Counts:
    """Confusion-matrix counts at one threshold."""

    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.tn + self.fn


def confusion_counts(y_true: list[int], y_score: list[float], threshold: float) -> Counts:
    """Count TP/FP/TN/FN: predict positive when ``score >= threshold``."""
    if len(y_true) != len(y_score):
        raise ValueError("y_true and y_score must be the same length")
    tp = fp = tn = fn = 0
    for yt, s in zip(y_true, y_score):
        pred = 1 if s >= threshold else 0
        if yt == 1 and pred == 1:
            tp += 1
        elif yt == 0 and pred == 1:
            fp += 1
        elif yt == 0 and pred == 0:
            tn += 1
        else:  # yt == 1 and pred == 0
            fn += 1
    return Counts(tp, fp, tn, fn)


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def precision(c: Counts) -> float:
    """Of everything we flagged positive, how much was right. TP / (TP + FP)."""
    return _safe_div(c.tp, c.tp + c.fp)


def recall(c: Counts) -> float:
    """Of everything that was actually positive, how much we caught. TP / (TP + FN)."""
    return _safe_div(c.tp, c.tp + c.fn)


def f1(c: Counts) -> float:
    """Harmonic mean of precision and recall — punishes lopsided trade-offs."""
    p, r = precision(c), recall(c)
    return _safe_div(2 * p * r, p + r)


def accuracy(c: Counts) -> float:
    """(TP + TN) / N. The metric that lies on imbalanced data (see Ch 2 opener)."""
    return _safe_div(c.tp + c.tn, c.n)


def fpr(c: Counts) -> float:
    """False-positive rate FP / (FP + TN) — the x-axis of an ROC curve."""
    return _safe_div(c.fp, c.fp + c.tn)


def metrics_at(y_true: list[int], y_score: list[float], threshold: float) -> dict:
    """All the headline metrics at one operating point."""
    c = confusion_counts(y_true, y_score, threshold)
    return {
        "threshold": threshold,
        "tp": c.tp, "fp": c.fp, "tn": c.tn, "fn": c.fn,
        "precision": precision(c),
        "recall": recall(c),
        "f1": f1(c),
        "accuracy": accuracy(c),
        "fpr": fpr(c),
        "tpr": recall(c),  # recall == TPR, the y-axis of an ROC curve
    }


def threshold_sweep(
    y_true: list[int], y_score: list[float], n_steps: int = 101
) -> list[dict]:
    """Metrics across the full threshold range [0, 1] — the data behind every
    precision/recall, ROC, and PR curve. The single most useful eval artifact."""
    if n_steps < 2:
        raise ValueError("n_steps must be >= 2 (need both endpoints 0 and 1)")
    return [metrics_at(y_true, y_score, i / (n_steps - 1)) for i in range(n_steps)]


def average_precision(y_true: list[int], y_score: list[float]) -> float:
    """Average precision: the sum of precision × Δrecall as the boundary sweeps
    down the ranking (no interpolation). The threshold-free summary you report
    *with* a chosen operating point, never instead of one. Returns 0.0 when there
    are no positives. Bridge: ``sklearn.metrics.average_precision_score``."""
    total_pos = sum(y_true)
    if total_pos == 0:
        return 0.0
    # Sort by descending score. Equal scores form one tie group — a threshold
    # can't split them — so we advance through a whole group before scoring a
    # point. (Counting one example at a time would make AP depend on the
    # arbitrary input order of tied items.)
    order = sorted(range(len(y_score)), key=lambda i: y_score[i], reverse=True)
    tp = fp = 0
    ap = 0.0
    prev_recall = 0.0
    j, n = 0, len(order)
    while j < n:
        k = j
        while k < n and y_score[order[k]] == y_score[order[j]]:
            if y_true[order[k]] == 1:
                tp += 1
            else:
                fp += 1
            k += 1
        prec = tp / (tp + fp)
        rec = tp / total_pos
        ap += prec * (rec - prev_recall)  # rectangle: precision × Δrecall
        prev_recall = rec
        j = k
    return ap
