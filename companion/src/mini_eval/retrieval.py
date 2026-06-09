"""Retrieval metrics — grading the *search* half of a RAG system.

Before a generator can answer, retrieval has to surface the right context; these
are the ranked-list metrics that say whether it did. How much of the top-k is
relevant (precision@k), how much of the relevant set you found (recall@k), how
early the first hit lands (reciprocal rank), and how good the *ordering* is (NDCG).

A "query" here is a ranked list of retrieved doc ids plus the set of ids that are
actually relevant (the ground truth). Stdlib-only, **for learning, not production**
(bridge to RAGAS / trec_eval / ranx). Faithfulness and answer relevance — the
*generation* half — are judged content, not ranked lists, so they live in Chapter 9
as an LLM-as-judge task (Chapter 7), not here.
"""

from __future__ import annotations

from math import log2


def precision_at_k(retrieved: list, relevant: set, k: int) -> float:
    """Of the top-k retrieved docs, the fraction that are relevant. Distinct
    relevant docs are counted once, so a duplicated hit can't inflate it. The
    denominator is k even when fewer than k docs were retrieved — the convention
    that treats a short list as having missed the rest (trec_eval-style)."""
    if k <= 0:
        return 0.0
    hits = len(set(retrieved[:k]) & relevant)
    return hits / k


def recall_at_k(retrieved: list, relevant: set, k: int) -> float:
    """Of all relevant docs, the fraction that appear in the top-k. Counts distinct
    relevant docs, so a duplicated hit can't push recall above 1.0."""
    if not relevant:
        return 0.0
    hits = len(set(retrieved[:k]) & relevant)
    return hits / len(relevant)


def reciprocal_rank(retrieved: list, relevant: set) -> float:
    """1 / rank of the first relevant doc (1-indexed); 0 if none are retrieved.
    Average this over queries to get MRR — how high the first good hit usually is."""
    for i, d in enumerate(retrieved, start=1):
        if d in relevant:
            return 1.0 / i
    return 0.0


def hit_at_k(retrieved: list, relevant: set, k: int) -> float:
    """1.0 if any relevant doc is in the top-k, else 0.0 (a.k.a. recall@k > 0)."""
    return 1.0 if any(d in relevant for d in retrieved[:k]) else 0.0


def dcg_at_k(retrieved: list, relevant: set, k: int) -> float:
    """Discounted cumulative gain, binary relevance, over the top-k. A hit at
    rank i is worth 1/log2(i+1), so later hits count for less."""
    return sum(
        (1.0 if d in relevant else 0.0) / log2(i + 1)
        for i, d in enumerate(retrieved[:k], start=1)
    )


def ndcg_at_k(retrieved: list, relevant: set, k: int) -> float:
    """DCG normalized by the ideal ordering (every relevant doc ranked first), so
    1.0 is a perfect ranking. The metric that rewards *order*, not just presence."""
    dcg = dcg_at_k(retrieved, relevant, k)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / log2(i + 1) for i in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0
