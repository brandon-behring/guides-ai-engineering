"""Agentic & task evaluation — success over multiple stochastic attempts.

An agent is stochastic: run the same task twice and it may pass once and fail once.
So "did it work?" becomes "how often, over how many tries?" — and the headline
metric is **pass@k**: the chance that *at least one* of k samples succeeds. Its honest
companion is **pass@1**, what a user gets on a single try.

A "task" here is summarized by ``(n_samples, n_correct)``: you ran it ``n`` times and
``c`` succeeded. ``pass_at_k`` is the unbiased estimator (Chen et al., 2021), which
avoids the optimistic bias of just checking whether any of your first k happened to
pass. Stdlib-only, **for learning, not production**.
"""

from __future__ import annotations

from math import comb


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k for one task: the probability that k samples drawn (without
    replacement) from the n you ran contain at least one of the c correct ones.

    pass@k = 1 − C(n−c, k) / C(n, k). With k=1 this is just c/n (pass@1)."""
    if k <= 0 or c <= 0:
        return 0.0
    if n - c < k:  # fewer than k failures exist, so any k samples must include a pass
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def mean_pass_at_k(tasks: list[tuple[int, int]], k: int) -> float:
    """Average pass@k across a suite of tasks; each task is ``(n_samples, n_correct)``.
    This is how a benchmark like HumanEval or SWE-bench reports a single pass@k."""
    if not tasks:
        return 0.0
    return sum(pass_at_k(n, c, k) for n, c in tasks) / len(tasks)
