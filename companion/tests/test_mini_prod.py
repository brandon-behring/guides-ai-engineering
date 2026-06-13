"""Correctness tests for mini_prod. Run with `pytest`, or directly:
`python companion/tests/test_mini_prod.py` (no pytest needed)."""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_prod import (  # noqa: E402
    percentile, latency_summary, kv_cache_gb, max_batch_from_memory,
    request_service_ms, poisson_arrivals, simulate_queue, achieved_qps,
    route_cheap, cascade_metrics, cascade_sweep, baseline,
    Span, flatten, self_time_ms, total_duration_ms, rollup_by_attribute,
    slowest_span, span_rows,
    sample, golden_accuracy, regression_gate, sampling_plan,
    rolling_mean, mann_whitney_u, detect_drift, slo_breach_index,
)


def _close(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def _raises(fn) -> bool:
    try:
        fn()
    except (ValueError, ZeroDivisionError):
        return True
    return False


# ---- latency: percentiles ----------------------------------------------------

def test_percentile_exact_ranks():
    xs = list(range(101))                     # 0..100
    assert _close(percentile(xs, 0), 0.0)
    assert _close(percentile(xs, 50), 50.0)
    assert _close(percentile(xs, 99), 99.0)
    assert _close(percentile(xs, 100), 100.0)


def test_percentile_interpolates():
    # rank = 0.5 * (2-1) = 0.5 → halfway between 0 and 10
    assert _close(percentile([0.0, 10.0], 50), 5.0)
    # unsorted input is handled
    assert _close(percentile([10.0, 0.0], 50), 5.0)


def test_percentile_single_value():
    assert _close(percentile([7.0], 99), 7.0)


def test_percentile_errors():
    assert _raises(lambda: percentile([], 50))
    assert _raises(lambda: percentile([1.0], -1))
    assert _raises(lambda: percentile([1.0], 101))


def test_latency_summary_fields():
    xs = [float(i) for i in range(1, 101)]    # 1..100
    s = latency_summary(xs)
    assert s["n"] == 100
    assert _close(s["max"], 100.0)
    assert _close(s["mean"], 50.5)
    assert s["p50"] <= s["p95"] <= s["p99"] <= s["max"]


# ---- latency: memory ---------------------------------------------------------

def test_kv_cache_gb_formula():
    # 2(K,V) * 1 * 1000 * 10 * 1000 * 2 bytes / 1e9 = 0.04 GB
    assert _close(kv_cache_gb(batch=1, seq_len=1000, layers=10, hidden=1000), 0.04)
    # linear in batch
    assert _close(kv_cache_gb(batch=4, seq_len=1000, layers=10, hidden=1000), 0.16)


def test_max_batch_is_largest_that_fits():
    dims = dict(seq_len=1000, layers=10, hidden=1000)
    budget = 0.4
    m = max_batch_from_memory(kv_budget_gb=budget, **dims)
    # the defining property: m fits, m+1 does not
    assert kv_cache_gb(batch=m, **dims) <= budget
    assert kv_cache_gb(batch=m + 1, **dims) > budget


def test_longer_context_cuts_batch():
    short = max_batch_from_memory(kv_budget_gb=4.0, seq_len=1000, layers=24, hidden=2048)
    long = max_batch_from_memory(kv_budget_gb=4.0, seq_len=8000, layers=24, hidden=2048)
    assert long < short          # 8x the context, ~1/8 the batch


# ---- latency: service time bridges to mini_rag.budget ------------------------

def test_request_service_ms_matches_budget():
    # prefill 1*(1000/1000)=1.0 ; decode 0.5*1*100=50.0 ; total 51.0
    assert _close(request_service_ms(params_b=1, input_tokens=1000, output_tokens=100), 51.0)


# ---- latency: arrivals + queue -----------------------------------------------

def test_poisson_arrivals_deterministic_and_bounded():
    a = poisson_arrivals(rate_qps=100, seconds=2, seed=1)
    b = poisson_arrivals(rate_qps=100, seconds=2, seed=1)
    assert a == b                               # seeded → reproducible
    assert a == sorted(a)                        # monotone
    assert a and a[-1] < 2000.0                  # within the window
    # different seed → different sample
    assert poisson_arrivals(rate_qps=100, seconds=2, seed=2) != a


def test_poisson_arrivals_rate_error():
    assert _raises(lambda: poisson_arrivals(rate_qps=0, seconds=1, seed=1))


def test_queue_serializes_on_one_server():
    # three simultaneous arrivals, one slot, 10ms each → 10, 20, 30
    assert simulate_queue([0.0, 0.0, 0.0], servers=1, service_ms=10.0) == [10.0, 20.0, 30.0]


def test_queue_no_wait_with_enough_servers():
    # three simultaneous arrivals, three slots → each just its service time
    assert simulate_queue([0.0, 0.0, 0.0], servers=3, service_ms=10.0) == [10.0, 10.0, 10.0]


def test_queue_no_wait_when_spaced_out():
    # arrivals spaced wider than service → never queue
    assert simulate_queue([0.0, 100.0, 200.0], servers=1, service_ms=10.0) == [10.0, 10.0, 10.0]


def test_queue_tail_grows_under_overload():
    # offered load above capacity → p99 wait dominates; more servers tames it
    arr = poisson_arrivals(rate_qps=200, seconds=5, seed=3)
    hot = latency_summary(simulate_queue(arr, servers=1, service_ms=10.0))["p99"]
    cool = latency_summary(simulate_queue(arr, servers=8, service_ms=10.0))["p99"]
    assert hot > cool


def test_queue_errors():
    assert _raises(lambda: simulate_queue([0.0], servers=0, service_ms=10.0))


def test_achieved_qps():
    assert _close(achieved_qps([0.0, 1000.0]), 2.0)        # 2 reqs over 1s
    assert _raises(lambda: achieved_qps([5.0]))


# ---- cascade -----------------------------------------------------------------

def test_route_cheap_threshold_inclusive():
    assert route_cheap(0.9, 0.8) is True
    assert route_cheap(0.8, 0.8) is True       # >= is inclusive
    assert route_cheap(0.7, 0.8) is False


def test_cascade_all_cheap_at_zero_threshold():
    m = cascade_metrics(confidences=[0.1, 0.9], cheap_correct=[1, 0],
                        hard_correct=[1, 1], cost_easy=1.0, cost_hard=10.0,
                        threshold=0.0)
    assert _close(m["easy_fraction"], 1.0)
    assert _close(m["accuracy"], 0.5)          # mean(cheap_correct)
    assert _close(m["cost_q"], 1.0)            # blended = cost_easy when all cheap


def test_cascade_all_hard_above_max_confidence():
    m = cascade_metrics(confidences=[0.1, 0.9], cheap_correct=[1, 0],
                        hard_correct=[1, 1], cost_easy=1.0, cost_hard=10.0,
                        threshold=1.01)
    assert _close(m["easy_fraction"], 0.0)
    assert _close(m["accuracy"], 1.0)          # mean(hard_correct)
    assert _close(m["cost_q"], 10.0)


def test_cascade_mixed_routing():
    m = cascade_metrics(
        confidences=[0.9, 0.4, 0.95, 0.3], cheap_correct=[1, 0, 1, 0],
        hard_correct=[1, 1, 1, 1], cost_easy=1.0, cost_hard=10.0, threshold=0.5)
    assert _close(m["easy_fraction"], 0.5)     # keep idx 0,2 ; escalate 1,3
    assert _close(m["accuracy"], 1.0)          # cheap right on kept, hard right on escalated
    assert _close(m["cost_q"], 5.5)            # 0.5*1 + 0.5*10
    assert _close(m["escalation_precision"], 1.0)  # both escalations warranted


def test_cascade_unwarranted_escalation_scores_zero_precision():
    # escalated a query the cheap model would have gotten right → wasted spend
    m = cascade_metrics(confidences=[0.1], cheap_correct=[1], hard_correct=[1],
                        cost_easy=1.0, cost_hard=10.0, threshold=0.5)
    assert _close(m["escalation_precision"], 0.0)


def test_cascade_cache_discounts_cost():
    base = cascade_metrics(confidences=[0.9], cheap_correct=[1], hard_correct=[1],
                           cost_easy=2.0, cost_hard=10.0, threshold=0.5)
    cached = cascade_metrics(confidences=[0.9], cheap_correct=[1], hard_correct=[1],
                             cost_easy=2.0, cost_hard=10.0, threshold=0.5,
                             cache_hit_rate=0.5)
    assert _close(cached["eff_cost_q"], 0.5 * base["cost_q"])


def test_cascade_errors():
    assert _raises(lambda: cascade_metrics(confidences=[0.1, 0.2], cheap_correct=[1],
                   hard_correct=[1, 1], cost_easy=1.0, cost_hard=10.0, threshold=0.5))
    assert _raises(lambda: cascade_metrics(confidences=[], cheap_correct=[],
                   hard_correct=[], cost_easy=1.0, cost_hard=10.0, threshold=0.5))


def test_cascade_sweep_easy_fraction_monotone():
    conf = [0.1, 0.3, 0.5, 0.7, 0.9]
    rows = cascade_sweep(confidences=conf, cheap_correct=[1, 1, 0, 1, 1],
                         hard_correct=[1, 1, 1, 1, 1], cost_easy=1.0, cost_hard=10.0,
                         thresholds=[0.0, 0.4, 0.6, 0.8, 1.01])
    fracs = [r["easy_fraction"] for r in rows]
    assert fracs == sorted(fracs, reverse=True)   # higher threshold → fewer kept
    assert _close(fracs[0], 1.0) and _close(fracs[-1], 0.0)


def test_baseline_endpoints():
    b = baseline(cheap_correct=[1, 0, 1, 0], hard_correct=[1, 1, 1, 1],
                 cost_easy=1.0, cost_hard=10.0)
    assert _close(b["all_cheap"]["accuracy"], 0.5)
    assert _close(b["all_cheap"]["cost_q"], 1.0)
    assert _close(b["all_hard"]["accuracy"], 1.0)
    assert _close(b["all_hard"]["cost_q"], 10.0)


# ---- trace -------------------------------------------------------------------

def _sample_trace():
    return Span("request", 0, 100, {"stage": "request"}, children=[
        Span("retrieve", 0, 40, {"stage": "retrieve"}, children=[
            Span("embed", 0, 20, {"stage": "embed"}),
        ]),
        Span("generate", 40, 100, {"stage": "generate"}),
    ])


def test_span_duration():
    assert _close(Span("x", 5, 30).duration_ms, 25.0)


def test_self_time_excludes_children():
    root = _sample_trace()
    retrieve = root.children[0]
    assert _close(self_time_ms(retrieve), 20.0)        # 40 total − 20 embed child
    assert _close(self_time_ms(root), 0.0)             # 100 − (40 + 60): pure wrapper


def test_flatten_is_preorder():
    names = [s.name for s in flatten(_sample_trace())]
    assert names == ["request", "retrieve", "embed", "generate"]


def test_rollup_by_attribute_sums_self_time():
    r = rollup_by_attribute(_sample_trace(), "stage")
    assert _close(r["generate"], 60.0)
    assert _close(r["retrieve"], 20.0)
    assert _close(r["embed"], 20.0)
    assert _close(r["request"], 0.0)
    assert _close(sum(r.values()), total_duration_ms(_sample_trace()))   # self-times tile the total


def test_slowest_span_by_self_time():
    assert slowest_span(_sample_trace()).name == "generate"


def test_span_rows_depth_and_offset():
    rows = span_rows(_sample_trace())
    assert rows[0]["depth"] == 0 and _close(rows[0]["start_ms"], 0.0)
    gen = next(r for r in rows if r["name"] == "generate")
    assert gen["depth"] == 1 and _close(gen["start_ms"], 40.0)


# ---- monitor -----------------------------------------------------------------

def test_sample_deterministic_and_bounds():
    items = list(range(1000))
    assert sample(items, rate=0.3, seed=5) == sample(items, rate=0.3, seed=5)
    assert sample(items, rate=1.0, seed=5) == items
    assert sample(items, rate=0.0, seed=5) == []
    assert _raises(lambda: sample(items, rate=1.5, seed=5))


def test_golden_accuracy_is_fraction_correct():
    assert _close(golden_accuracy([1, 1, 0, 1]), 0.75)
    assert _raises(lambda: golden_accuracy([]))


def test_regression_gate_identical_passes_as_noise():
    g = regression_gate([1, 1, 0, 1, 1, 0, 1, 1, 0, 1],
                        [1, 1, 0, 1, 1, 0, 1, 1, 0, 1], seed=0)
    assert _close(g["delta"], 0.0)
    assert g["passed"] is True
    assert g["significant"] is False


def test_regression_gate_clear_regression_fails():
    g = regression_gate([1] * 40, [1] * 20 + [0] * 20, seed=0)
    assert _close(g["delta"], -0.5)
    assert g["significant"] is True
    assert g["passed"] is False


def test_regression_gate_errors():
    assert _raises(lambda: regression_gate([1, 0], [1], seed=0))
    assert _raises(lambda: regression_gate([], [], seed=0))


def test_sampling_plan_arithmetic():
    p = sampling_plan(qpd=10000, rate=0.05, cost_per_eval_usd=0.002)
    assert p["sampled_per_day"] == 500
    assert _close(p["daily_cost"], 1.0)
    assert _close(p["monthly_cost"], 30.0)
    assert _raises(lambda: sampling_plan(qpd=100, rate=2.0, cost_per_eval_usd=0.01))


# ---- drift -------------------------------------------------------------------

def test_rolling_mean_trailing_window():
    assert rolling_mean([1, 2, 3, 4], 2) == [1.0, 1.5, 2.5, 3.5]
    assert rolling_mean([5, 6, 7], 1) == [5.0, 6.0, 7.0]
    assert _raises(lambda: rolling_mean([1, 2], 0))


def test_mann_whitney_same_distribution_high_p():
    a = list(range(20))
    assert mann_whitney_u(a, list(range(20)))["p"] > 0.9


def test_mann_whitney_shifted_low_p():
    a = list(range(20))
    b = [x + 100 for x in range(20)]               # fully separated
    assert mann_whitney_u(a, b)["p"] < 0.01
    assert _raises(lambda: mann_whitney_u([], [1.0]))


def test_detect_drift():
    ref = [0.9, 0.91, 0.89, 0.9, 0.92, 0.9, 0.88, 0.9]
    same = [0.9, 0.9, 0.91, 0.89, 0.9, 0.92, 0.9, 0.9]
    shifted = [0.6, 0.58, 0.62, 0.59, 0.6, 0.57, 0.61, 0.6]
    assert detect_drift(ref, same) is False
    assert detect_drift(ref, shifted) is True


def test_slo_breach_index():
    series = [0.9, 0.88, 0.85, 0.7, 0.6]
    assert slo_breach_index(series, guardrail=0.8, window=1) == 3       # first day below
    assert slo_breach_index([0.9] * 5, guardrail=0.8, window=1) is None  # never breaches
    latency = [100, 120, 150, 300, 280]
    assert slo_breach_index(latency, guardrail=200, window=1, above=True) == 3


def _run_all() -> None:
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
