"""Drift detection — catching the slow failure that no single deploy explains.

Chapter 0's third failure was quality sliding for weeks with no smoking gun: the input
mix shifted, the corpus aged, and the golden-set score (frozen) stayed green the whole
time. Drift is the failure mode that only a *rolling* measurement against *live* traffic
can see. This module is the three pieces of a drift monitor:

- ``rolling_mean`` — smooth the noisy daily signal so a real trend separates from jitter.
- ``mann_whitney_u`` — a non-parametric rank test: did a recent window's distribution
  shift from a reference window? No normality assumed, robust to the heavy tails of
  latency and score data — which is exactly why a t-test is the wrong tool here.
- ``slo_breach_index`` — the alert rule: the first day the smoothed signal crosses a
  guardrail.

Stdlib-only, **for learning, not production** — bridge to a monitoring stack (Evidently,
Arize, a Prometheus alert) that runs these windows continuously and pages someone.
"""

from __future__ import annotations

import math


def rolling_mean(series: list[float], window: int) -> list[float]:
    """Trailing mean over the last ``window`` points (shorter at the start). Smooths a
    jittery daily quality signal so a genuine downward trend stands out from noise."""
    if window < 1:
        raise ValueError("window must be >= 1")
    out: list[float] = []
    for i in range(len(series)):
        chunk = series[max(0, i - window + 1): i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def mann_whitney_u(a: list[float], b: list[float]) -> dict:
    """Mann–Whitney U statistic and a two-sided normal-approximation p-value for
    'a and b come from different distributions'. Ranks the pooled sample (averaging
    tied ranks), so it tests a distribution *shift* without assuming a shape — the right
    test for skewed production signals; the variance carries the standard tie correction.
    Returns ``{"u", "p"}``."""
    na, nb = len(a), len(b)
    if na == 0 or nb == 0:
        raise ValueError("both samples must be non-empty")
    pooled = sorted([(v, 0) for v in a] + [(v, 1) for v in b], key=lambda t: t[0])
    ranks = [0.0] * len(pooled)
    tie_sum = 0.0                                # Σ(t³ − t) over tie groups, for the variance
    i = 0
    while i < len(pooled):                       # average ranks within ties
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0           # ranks are 1-based
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        g = j - i + 1
        tie_sum += g ** 3 - g
        i = j + 1
    r_a = sum(ranks[k] for k in range(len(pooled)) if pooled[k][1] == 0)
    u_a = r_a - na * (na + 1) / 2.0
    u = min(u_a, na * nb - u_a)
    n = na + nb
    mu = na * nb / 2.0
    # variance with the standard tie correction (reduces to na*nb*(n+1)/12 when no ties)
    var = (na * nb / 12.0) * ((n + 1) - tie_sum / (n * (n - 1))) if n > 1 else 0.0
    sigma = math.sqrt(var) if var > 0 else 0.0
    if sigma == 0:
        return {"u": u, "p": 1.0}
    z = (u - mu) / sigma                         # u <= mu, so z <= 0
    return {"u": u, "p": min(1.0, 2.0 * _normal_cdf(z))}


def detect_drift(reference: list[float], recent: list[float], *, alpha: float = 0.05) -> bool:
    """True if ``recent`` differs from ``reference`` at significance ``alpha`` (Mann–
    Whitney). The distribution-shift alarm a single moving average can miss — variance
    can blow up while the mean holds."""
    return mann_whitney_u(reference, recent)["p"] < alpha


def slo_breach_index(series: list[float], *, guardrail: float, window: int,
                     above: bool = False) -> int | None:
    """First index where the rolling mean crosses the guardrail — quality dropping
    below it by default (``above=True`` for a latency-style ceiling). ``None`` if it
    never breaches. This is the alert the monitor actually fires."""
    rm = rolling_mean(series, window)
    for i, v in enumerate(rm):
        if (v > guardrail) if above else (v < guardrail):
            return i
    return None
