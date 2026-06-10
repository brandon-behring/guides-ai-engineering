"""Latency and cost arithmetic for a RAG request — back-of-envelope, on purpose.

Production conversations about RAG are conversations about two budgets: the
millisecond budget (will p95 hold?) and the dollar budget (what does a query
cost at 10K/day?). Both are arithmetic you can do before building anything,
and interviewers expect exactly that arithmetic. The rules of thumb encoded
here are the standard first-principles estimates (label them as estimates —
then *measure*):

- **Prefill** (process the whole input, compute-bound):
  ~1 ms per billion params per 1K input tokens.
- **Decode** (generate one token at a time, memory-bandwidth-bound):
  ~0.5 ms per token per billion params. Output length multiplies this —
  never quote a latency without stating the output-length assumption.
- **API cost**: (input_tokens x rate_in + output_tokens x rate_out) / 1e6.

Stdlib-only, **for learning, not production** — bridge to real profiling
(OpenTelemetry spans per stage), provider pricing pages, and serving stacks
(vLLM continuous batching, prompt caching) that move these constants.
"""

from __future__ import annotations

from dataclasses import dataclass


def prefill_ms(params_b: float, input_tokens: int) -> float:
    """Time to first token, roughly: ~1 ms per billion parameters per 1K
    input tokens (compute-bound; GPU saturated)."""
    return params_b * (input_tokens / 1000.0)


def decode_ms(params_b: float, output_tokens: int) -> float:
    """Generation time, roughly: ~0.5 ms per token per billion parameters
    (memory-bound; the KV cache is being read, not the ALUs). Scales linearly
    with output length — the term beginners forget."""
    return 0.5 * params_b * output_tokens


def llm_latency_ms(params_b: float, input_tokens: int, output_tokens: int) -> float:
    """Prefill + decode. The decode term usually dominates: 500 output tokens
    cost 25x more generation time than 20."""
    return prefill_ms(params_b, input_tokens) + decode_ms(params_b, output_tokens)


def api_cost_usd(input_tokens: int, output_tokens: int,
                 rate_in_per_m: float, rate_out_per_m: float) -> float:
    """Cost of one call at per-million-token rates."""
    return (input_tokens * rate_in_per_m + output_tokens * rate_out_per_m) / 1e6


@dataclass(frozen=True)
class RequestBudget:
    """One RAG request's latency ledger (ms per stage) and token ledger.
    ``total_ms`` is the sum — the number to hold against the SLA; the stage
    breakdown is the number to hold against your profiler."""

    embed_ms: float
    search_ms: float
    rerank_ms: float
    prefill_ms: float
    decode_ms: float
    input_tokens: int
    output_tokens: int

    @property
    def total_ms(self) -> float:
        return (self.embed_ms + self.search_ms + self.rerank_ms
                + self.prefill_ms + self.decode_ms)

    @property
    def ttft_ms(self) -> float:
        """Time to first token — everything before decode starts. What a
        *streaming* user actually waits for."""
        return self.embed_ms + self.search_ms + self.rerank_ms + self.prefill_ms


def rag_request_budget(*, params_b: float, k_chunks: int, chunk_tokens: int,
                       prompt_tokens: int, question_tokens: int,
                       output_tokens: int, embed_ms: float = 20.0,
                       search_ms: float = 15.0, rerank_ms: float = 0.0) -> RequestBudget:
    """Assemble a request budget from pipeline knobs. The RAG-specific move:
    input tokens = k x chunk size + prompt scaffolding + question — Chapter 4's
    context budget is literally a line item on the bill."""
    input_tokens = k_chunks * chunk_tokens + prompt_tokens + question_tokens
    return RequestBudget(
        embed_ms=embed_ms,
        search_ms=search_ms,
        rerank_ms=rerank_ms,
        prefill_ms=prefill_ms(params_b, input_tokens),
        decode_ms=decode_ms(params_b, output_tokens),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def cascade_cost_usd(easy_fraction: float, cost_easy: float, cost_hard: float) -> float:
    """Blended per-query cost of a model cascade: route the easy fraction to
    the cheap model, escalate the rest. The single biggest cost lever in LLM
    serving — IF the escalation signal is calibrated (a confidently-wrong
    small model routes nothing; see the Evaluation guide on calibration)."""
    if not 0.0 <= easy_fraction <= 1.0:
        raise ValueError("easy_fraction must be in [0, 1]")
    return easy_fraction * cost_easy + (1.0 - easy_fraction) * cost_hard


def effective_cost_usd(cost_per_query: float, cache_hit_rate: float,
                       cached_cost: float = 0.0) -> float:
    """Per-query cost after a response cache: hits cost ~nothing, misses cost
    full price. A 30% hit rate is a 30% discount on the whole bill."""
    if not 0.0 <= cache_hit_rate <= 1.0:
        raise ValueError("cache_hit_rate must be in [0, 1]")
    return cache_hit_rate * cached_cost + (1.0 - cache_hit_rate) * cost_per_query


def break_even_queries_per_day(gpu_monthly_usd: float, api_cost_per_query: float) -> float:
    """Daily query volume where self-hosting (fixed GPU cost) matches the API
    bill. Below this, the API is cheaper; far above it, self-hosting wins —
    unless latency or data residency already made the choice for you."""
    if api_cost_per_query <= 0:
        raise ValueError("api_cost_per_query must be positive")
    return gpu_monthly_usd / 30.0 / api_cost_per_query
