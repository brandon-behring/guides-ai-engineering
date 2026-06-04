"""A mock-model LLM-as-judge harness — the biases, made reproducible.

The expensive, slow, non-deterministic part of LLM-as-judge is the model call.
The *interesting* part — position bias, verbosity bias, and how to debias with a
position swap — is pure bookkeeping you can reproduce with a deterministic mock
"model". That is what this module does: **no live LLM**, just a scoring function
plus the bias bookkeeping. (Bridge to production: this is what a thin wrapper
around an actual judge prompt + RAGAS / `eval-toolkit` formalizes.)

A `Response` carries its *latent quality* (the ground truth a perfect judge would
recover) and its text (whose length drives verbosity bias). A `PairwiseJudge`
decides which of two responses is better — and, like a real LLM judge, can be
nudged by where a response sits and how long it is.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    id: str
    text: str
    quality: float  # latent "true" quality a perfect judge would recover


def _default_score(r: Response) -> float:
    return r.quality


class PairwiseJudge:
    """Picks the better of two responses. ``position_bias`` is added to whichever
    response is shown *first*; ``verbosity_bias`` is added per character of length.
    Both default to 0 (an unbiased judge); turn them up to reproduce the failure
    modes interviews ask you to mitigate."""

    def __init__(
        self,
        score_fn=_default_score,
        position_bias: float = 0.0,
        verbosity_bias: float = 0.0,
    ) -> None:
        self.score_fn = score_fn
        self.position_bias = position_bias
        self.verbosity_bias = verbosity_bias

    def _score(self, r: Response, position: int) -> float:
        s = self.score_fn(r)
        if position == 0:
            s += self.position_bias
        s += self.verbosity_bias * len(r.text)
        return s

    def judge(self, first: Response, second: Response) -> str:
        """Verdict for the ordering (first, second). Returns the winner's id."""
        return first.id if self._score(first, 0) >= self._score(second, 1) else second.id

    def judge_debiased(self, a: Response, b: Response) -> str:
        """Run *both* orderings; only declare a winner if the verdict is
        order-independent. An inconsistent verdict ('tie') is the signal that
        position bias decided the original call — the standard mitigation."""
        v1 = self.judge(a, b)
        v2 = self.judge(b, a)
        return v1 if v1 == v2 else "tie"


def position_flip_rate(judge: PairwiseJudge, pairs: list[tuple[Response, Response]]) -> float:
    """Fraction of pairs whose verdict *flips* when you swap presentation order.
    A judge with no position bias scores 0; this is the headline diagnostic."""
    if not pairs:
        return 0.0
    flips = sum(1 for a, b in pairs if judge.judge(a, b) != judge.judge(b, a))
    return flips / len(pairs)


def judge_accuracy(judge: PairwiseJudge, pairs: list[tuple[Response, Response]]) -> float:
    """How often the (order-1) verdict matches the latent-quality ground truth.
    The number that quietly drops as you crank up the biases."""
    if not pairs:
        return 0.0
    correct = 0
    for a, b in pairs:
        truth = a.id if a.quality >= b.quality else b.id
        if judge.judge(a, b) == truth:
            correct += 1
    return correct / len(pairs)
