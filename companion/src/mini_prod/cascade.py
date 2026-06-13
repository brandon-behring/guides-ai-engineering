"""Cost engineering — the model cascade and its one failure mode.

Chapter 0's bot ran 4x over budget after launch. The single biggest cost lever in
LLM serving is the *cascade*: send the easy majority of queries to a cheap model and
escalate only the hard ones to the frontier model. ``mini_rag.budget`` already has
the blended-cost arithmetic (``cascade_cost_usd``); this module adds the part that
decides *which* queries are easy — and measures the mistake that makes a cascade
quietly worse instead of cheaper.

The lesson the island makes visceral: a cascade's savings are only real if the
routing signal is **calibrated**. Route on a confidence score that doesn't track
correctness and you get a cheap system that is confidently wrong on exactly the hard
queries — all of the savings, none of the quality. (Calibration is the Evaluation
guide's subject; here it is the hinge of a cost decision.)

Stdlib-only, **for learning, not production** — bridge to a real router (a small
classifier, semantic-similarity gating, or a judged confidence) and to provider
pricing pages, which move the constants under you.
"""

from __future__ import annotations

from mini_rag.budget import cascade_cost_usd, effective_cost_usd


def route_cheap(confidence: float, threshold: float) -> bool:
    """Keep a query on the cheap model iff its confidence clears the threshold;
    otherwise escalate to the frontier model. Raising the threshold escalates more
    queries — costlier, but safer if (and only if) confidence tracks correctness."""
    return confidence >= threshold


def cascade_metrics(*, confidences: list[float], cheap_correct: list[int],
                    hard_correct: list[int], cost_easy: float, cost_hard: float,
                    threshold: float, cache_hit_rate: float = 0.0) -> dict:
    """Evaluate a cascade at one routing threshold over a labelled sample.

    Three equal-length lists indexed by query:
    - ``confidences``   — the cheap model's self-reported confidence (the routing signal)
    - ``cheap_correct`` — was the cheap model actually right? (1/0)
    - ``hard_correct``  — was the frontier model right? (1/0)

    Returns the cost AND the quality of the routed system, so the trade is visible —
    not just the savings. ``accuracy`` credits the cheap model on kept queries and
    the frontier model on escalated ones: that is the system the user actually meets.
    ``escalation_precision`` is how often an escalation was warranted (the cheap model
    would have been wrong) — a calibration read on the routing signal."""
    n = len(confidences)
    if not (n == len(cheap_correct) == len(hard_correct)):
        raise ValueError("confidences, cheap_correct, hard_correct must be equal length")
    if n == 0:
        raise ValueError("empty sample")

    kept = [i for i in range(n) if route_cheap(confidences[i], threshold)]
    escalated = [i for i in range(n) if i not in set(kept)]
    easy_fraction = len(kept) / n

    correct = (sum(cheap_correct[i] for i in kept)
               + sum(hard_correct[i] for i in escalated))
    accuracy = correct / n

    blended = cascade_cost_usd(easy_fraction, cost_easy, cost_hard)
    effective = effective_cost_usd(blended, cache_hit_rate)

    warranted = sum(1 for i in escalated if not cheap_correct[i])
    escalation_precision = warranted / len(escalated) if escalated else 1.0

    return {
        "threshold": threshold,
        "easy_fraction": easy_fraction,
        "accuracy": accuracy,
        "cost_q": blended,
        "eff_cost_q": effective,
        "escalation_precision": escalation_precision,
    }


def cascade_sweep(*, confidences: list[float], cheap_correct: list[int],
                  hard_correct: list[int], cost_easy: float, cost_hard: float,
                  thresholds: list[float], cache_hit_rate: float = 0.0) -> list[dict]:
    """``cascade_metrics`` across a list of thresholds → the cost/accuracy frontier.
    Reading it is the skill: find the threshold that holds accuracy near the
    all-frontier baseline while paying near the all-cheap cost — and notice that a
    *miscalibrated* signal has no such point (accuracy falls as you save)."""
    return [cascade_metrics(confidences=confidences, cheap_correct=cheap_correct,
                            hard_correct=hard_correct, cost_easy=cost_easy,
                            cost_hard=cost_hard, threshold=t,
                            cache_hit_rate=cache_hit_rate)
            for t in thresholds]


def baseline(*, cheap_correct: list[int], hard_correct: list[int],
             cost_easy: float, cost_hard: float) -> dict:
    """The two endpoints a cascade is judged against: all-cheap (cost floor, accuracy
    floor) and all-frontier (accuracy ceiling, cost ceiling). A good cascade lands
    near the top-left of the box they define; a bad one lands on the diagonal."""
    n = len(cheap_correct)
    if n == 0 or n != len(hard_correct):
        raise ValueError("cheap_correct and hard_correct must be equal, non-empty")
    return {
        "all_cheap": {"accuracy": sum(cheap_correct) / n, "cost_q": cost_easy},
        "all_hard": {"accuracy": sum(hard_correct) / n, "cost_q": cost_hard},
    }
