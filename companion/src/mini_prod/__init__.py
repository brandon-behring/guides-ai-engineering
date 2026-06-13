"""mini_prod — the build-your-own production-serving companion for Guide #3.

Stdlib-only, **for learning, not production**. It *imports* the earlier companions
(``mini_eval`` for measurement, ``mini_rag`` for the served pipeline + budget math)
rather than rebuilding them — reuse is part of the lesson. Module map:

- ``mini_prod.latency``  — latency distributions (percentiles), KV-cache memory
  limits, and a deterministic queueing simulation (Ch 2–3).
- ``mini_prod.cascade``  — the calibrated model cascade: routing policy + the
  cost/accuracy frontier, built on ``mini_rag.budget`` (Ch 4).
- ``mini_prod.trace``    — a span tree + self-time / attribute rollups: the
  OpenTelemetry mental model for "where did this request's time go?" (Ch 5).
- ``mini_prod.monitor``  — sampling live traffic + a CI-gated regression gate,
  reusing ``mini_eval`` metrics and confidence intervals (Ch 6).
- ``mini_prod.drift``    — rolling windows, a Mann–Whitney rank test, and an SLO
  breach alert: catching slow quality decay (Ch 7).
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
from .trace import (
    Span,
    flatten,
    self_time_ms,
    total_duration_ms,
    rollup_by_attribute,
    slowest_span,
    span_rows,
)
from .monitor import (
    sample,
    golden_accuracy,
    regression_gate,
    sampling_plan,
)
from .drift import (
    rolling_mean,
    mann_whitney_u,
    detect_drift,
    slo_breach_index,
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
    "Span",
    "flatten",
    "self_time_ms",
    "total_duration_ms",
    "rollup_by_attribute",
    "slowest_span",
    "span_rows",
    "sample",
    "golden_accuracy",
    "regression_gate",
    "sampling_plan",
    "rolling_mean",
    "mann_whitney_u",
    "detect_drift",
    "slo_breach_index",
]

__version__ = "0.1.0"
