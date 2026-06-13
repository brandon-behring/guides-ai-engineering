"""Distributed tracing, the OpenTelemetry mental model without the dependency.

Chapter 5's question is "where did this one request's time go?" — and the answer is a
*trace*: a tree of spans, each a timed unit of work carrying attributes. A metric tells
you p99 is high; a trace tells you *which stage* of *which request* spent the time. This
module is the span tree and the two readings that matter — **self-time** (where work
actually happened, excluding children) and **rollup by attribute** (total time per stage
across the trace).

Stdlib-only, **for learning, not production** — bridge to OpenTelemetry / Jaeger /
Arize Phoenix, where spans are emitted by instrumentation and aggregated by a backend.
The shape (span tree, attributes, self-time, rollups) is exactly theirs.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Span:
    """One timed unit of work. ``children`` are sub-spans within this span's window;
    ``attributes`` are the key/values you aggregate by (stage, model, cache_hit…)."""

    name: str
    start_ms: float
    end_ms: float
    attributes: dict = field(default_factory=dict)
    children: list["Span"] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return self.end_ms - self.start_ms


def flatten(root: Span) -> list[Span]:
    """Pre-order list of every span in the tree (root first, then each subtree)."""
    out = [root]
    for c in root.children:
        out.extend(flatten(c))
    return out


def self_time_ms(span: Span) -> float:
    """Exclusive time — this span's duration minus the time its children account for.
    The honest 'where did the work happen' number: a parent that is nothing but
    children is a wrapper with ~0 self-time, even if its total duration is large."""
    return span.duration_ms - sum(c.duration_ms for c in span.children)


def total_duration_ms(root: Span) -> float:
    """Wall-clock time of the whole trace — the number a latency metric reports."""
    return root.duration_ms


def rollup_by_attribute(root: Span, key: str) -> dict:
    """Sum self-time across the trace, grouped by an attribute value — e.g. total ms
    per ``stage``. This is the trace-to-metric bridge: a metric is a rollup of spans."""
    out: dict = {}
    for s in flatten(root):
        if key in s.attributes:
            out[s.attributes[key]] = out.get(s.attributes[key], 0.0) + self_time_ms(s)
    return out


def slowest_span(root: Span) -> Span:
    """The span with the most self-time — where to look first when a request is slow."""
    return max(flatten(root), key=self_time_ms)


def span_rows(root: Span) -> list[dict]:
    """Flatten to rows for a waterfall view: name, offset from the trace start, own
    duration, self-time, nesting depth, and the stage attribute. The island reads
    exactly this."""
    t0 = root.start_ms
    rows: list[dict] = []

    def walk(s: Span, depth: int) -> None:
        rows.append({
            "name": s.name,
            "start_ms": round(s.start_ms - t0, 1),
            "duration_ms": round(s.duration_ms, 1),
            "self_ms": round(self_time_ms(s), 1),
            "depth": depth,
            "stage": s.attributes.get("stage", ""),
        })
        for c in s.children:
            walk(c, depth + 1)

    walk(root, 0)
    return rows
