"""Production serving latency — distributions, memory limits, and queueing.

Chapter 0's support bot crossed its p99 SLA when a promo 10x'd traffic. That is not
a "the model got slower" problem — per-request latency never changed. It is a
*queueing* problem: more requests arrived than there were serving slots, so requests
waited. This module is the arithmetic of that.

It builds ON ``mini_rag.budget`` (prefill/decode time for one request) and adds the
three things production serving introduces that a single-request estimate misses:

- **Latency is a distribution.** You serve thousands of requests; the SLA is written
  against the *tail* (p95/p99), not the mean. ``percentile`` / ``latency_summary``.
- **Batch size is memory-bound.** Concurrency is capped by KV-cache memory, not the
  ALUs. ``kv_cache_gb`` / ``max_batch_from_memory``.
- **Throughput vs latency is a queue.** ``simulate_queue`` is a deterministic
  c-server discrete-event simulation: more concurrent slots (a bigger batch) absorb a
  load spike and tame the tail — until memory caps the batch. ``poisson_arrivals``
  generates reproducible bursty load.

Stdlib-only, **for learning, not production** — bridge to real load testing (Locust,
k6), a serving stack's own metrics (vLLM, TGI), and an APM's latency histograms.
"""

from __future__ import annotations

import math
import random

from mini_rag.budget import llm_latency_ms


def percentile(samples: list[float], p: float) -> float:
    """The p-th percentile of ``samples`` (p in [0, 100]), linear interpolation
    between closest ranks — the definition NumPy uses by default. This is the
    number an SLA is written against: "p99 < 2s" is a promise about the 99th
    request, which the mean cannot see."""
    if not samples:
        raise ValueError("samples is empty")
    if not 0.0 <= p <= 100.0:
        raise ValueError("p must be in [0, 100]")
    xs = sorted(samples)
    if len(xs) == 1:
        return float(xs[0])
    rank = (p / 100.0) * (len(xs) - 1)
    lo = math.floor(rank)
    if lo + 1 >= len(xs):
        return float(xs[-1])
    frac = rank - lo
    return float(xs[lo] + frac * (xs[lo + 1] - xs[lo]))


def latency_summary(samples: list[float]) -> dict:
    """p50/p95/p99/max/mean of a latency sample (whatever unit you pass in). The
    mean hides the tail; a production latency report always shows the percentiles
    because that is where SLAs live and where users churn."""
    return {
        "p50": percentile(samples, 50),
        "p95": percentile(samples, 95),
        "p99": percentile(samples, 99),
        "max": float(max(samples)),
        "mean": sum(samples) / len(samples),
        "n": len(samples),
    }


def kv_cache_gb(*, batch: int, seq_len: int, layers: int, hidden: int,
                bytes_per: int = 2) -> float:
    """GB of GPU memory the KV cache needs for ``batch`` concurrent requests, each
    holding ``seq_len`` tokens: two tensors (K and V) x layers x hidden x bytes.
    This — not compute — is what caps how many requests you can batch, and the
    reason decode is memory-bandwidth-bound rather than ALU-bound."""
    return 2 * batch * seq_len * layers * hidden * bytes_per / 1e9


def max_batch_from_memory(*, kv_budget_gb: float, seq_len: int, layers: int,
                          hidden: int, bytes_per: int = 2) -> int:
    """Invert ``kv_cache_gb``: how many requests fit in ``kv_budget_gb`` of leftover
    VRAM (total minus the weights). The hard ceiling on concurrency — and the reason
    a longer context window silently cuts your maximum batch size."""
    per_req = kv_cache_gb(batch=1, seq_len=seq_len, layers=layers,
                          hidden=hidden, bytes_per=bytes_per)
    if per_req <= 0:
        raise ValueError("per-request KV size must be positive")
    return int(kv_budget_gb / per_req)


def request_service_ms(*, params_b: float, input_tokens: int,
                       output_tokens: int) -> float:
    """Service time for one request on a saturated GPU — prefill + decode, straight
    from ``mini_rag.budget``. This is the ``service_ms`` you feed ``simulate_queue``:
    the queue is built on top of the single-request arithmetic you already have."""
    return llm_latency_ms(params_b, input_tokens, output_tokens)


def poisson_arrivals(*, rate_qps: float, seconds: float, seed: int) -> list[float]:
    """Reproducible arrival timestamps (ms) for a Poisson process at ``rate_qps``
    over ``seconds``. Exponential interarrival gaps make it bursty — like real
    traffic, not evenly spaced — which is *why* a queue forms below nominal
    capacity. Seeded, so the committed demo JSON is stable."""
    if rate_qps <= 0:
        raise ValueError("rate_qps must be positive")
    rng = random.Random(seed)
    mean_gap_ms = 1000.0 / rate_qps
    end_ms = seconds * 1000.0
    out: list[float] = []
    t_ms = 0.0
    while True:
        t_ms += rng.expovariate(1.0 / mean_gap_ms)
        if t_ms >= end_ms:
            break
        out.append(t_ms)
    return out


def simulate_queue(arrivals_ms: list[float], *, servers: int,
                   service_ms: float) -> list[float]:
    """Deterministic c-server queue: ``servers`` requests process concurrently (one
    batch slot each), each taking ``service_ms``. Returns per-request total latency
    (queue wait + service), in ms, in arrival order.

    This is the whole "10x traffic broke p99" story in one function: when arrivals
    outrun the ``servers / service_ms`` throughput, requests pile up and the *wait* —
    not the service — dominates the tail. More slots (a bigger batch) is the lever;
    ``kv_cache_gb`` is why you can't just set it to infinity."""
    if servers < 1:
        raise ValueError("servers must be >= 1")
    if service_ms < 0:
        raise ValueError("service_ms must be non-negative")
    slot_free = [0.0] * servers          # time each slot next becomes free
    latencies: list[float] = []
    for arr in sorted(arrivals_ms):
        s = min(range(servers), key=lambda i: slot_free[i])
        start = max(arr, slot_free[s])
        finish = start + service_ms
        slot_free[s] = finish
        latencies.append(finish - arr)
    return latencies


def achieved_qps(arrivals_ms: list[float]) -> float:
    """Offered load: requests divided by the span they arrived over (per second).
    Compare against capacity = ``servers * 1000 / service_ms`` to see how close to
    saturation you are — the ratio that predicts whether the tail blows up."""
    if len(arrivals_ms) < 2:
        raise ValueError("need >= 2 arrivals")
    span_s = (max(arrivals_ms) - min(arrivals_ms)) / 1000.0
    return len(arrivals_ms) / span_s if span_s > 0 else float("inf")
