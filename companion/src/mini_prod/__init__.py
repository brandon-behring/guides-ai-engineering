"""mini_prod — the build-your-own production-serving companion for Guide #3.

Stdlib-only, **for learning, not production**. It *imports* the earlier companions
(``mini_eval`` for measurement, ``mini_rag`` for the served pipeline + budget math)
rather than rebuilding them — reuse is part of the lesson. Module map:

- ``mini_prod.latency``  — latency distributions (percentiles), KV-cache memory
  limits, and a deterministic queueing simulation (Ch 2–3).
- ``mini_prod.cascade``  — the calibrated model cascade: routing policy + the
  cost/accuracy frontier, built on ``mini_rag.budget`` (Ch 4).

(Chapters 5–7 add ``trace``, ``monitor``, and ``drift``.)
"""

from .latency import (
    percentile,
    latency_summary,
    kv_cache_gb,
    max_batch_from_memory,
    request_service_ms,
    poisson_arrivals,
    simulate_queue,
    achieved_qps,
)
from .cascade import (
    route_cheap,
    cascade_metrics,
    cascade_sweep,
    baseline,
)

__all__ = [
    "percentile",
    "latency_summary",
    "kv_cache_gb",
    "max_batch_from_memory",
    "request_service_ms",
    "poisson_arrivals",
    "simulate_queue",
    "achieved_qps",
    "route_cheap",
    "cascade_metrics",
    "cascade_sweep",
    "baseline",
]

__version__ = "0.1.0"
