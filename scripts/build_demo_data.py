"""Generate precomputed JSON for the Evaluation guide's interactive demos.

The "dump" half of the dump -> JSON -> island pattern: all computation happens
here, offline, using the same `mini_eval` the reader builds; the browser islands
only read the JSON (no model, no server). Deterministic (seeded) so the committed
JSON is stable. Run: `python scripts/build_demo_data.py`.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "companion", "src"))

from mini_eval import (  # noqa: E402
    threshold_sweep, confusion_counts, precision, recall, f1,
    bootstrap_ci, paired_diff_ci, permutation_test,
    reliability_curve, expected_calibration_error, brier_score,
    precision_at_k, recall_at_k, ndcg_at_k,
    mean_pass_at_k,
    Response, PairwiseJudge, position_flip_rate,
)
from mini_rag import (  # noqa: E402
    TfidfIndex, chunk_fixed, chunk_sentences, chunk_paragraphs, boundary_coherence,
    RagPipeline, split_sentences,
    fold_tokenize, expand_query, coverage_score, hybrid_search,
    assemble_context, ABSTAIN,
    api_cost_usd, cascade_cost_usd, effective_cost_usd,
)

# The ACME refund policy — shared by the Ch 3 chunking demo and the Ch 4
# pipeline demo (continuity: same document, deeper failure modes).
POLICY_DOC = "\n\n".join([
    ("Thanks for shopping with ACME. This page explains our return and refund "
     "policies for standard orders, gift cards, and final-sale items. If anything "
     "here is unclear, our support team can walk you through the details."),
    ("Most items qualify for a full refund. To start, open your order history, "
     "choose the order that contains the item, and select the item you want to "
     "send back. If your order shipped in several packages, return each item "
     "separately. You may request a refund within 30 days of purchase, as long "
     "as the item is unopened and in its original packaging."),
    ("Once your return arrives at our warehouse, we inspect it within two "
     "business days. Approved refunds are paid to the original payment method. "
     "Bank processing times vary, so allow up to five business days for the "
     "money to appear."),
    ("Gift cards and final-sale items are non-refundable. Items marked as "
     "clearance may be exchanged for store credit instead. Shipping fees are "
     "refunded only when the return is our error."),
])

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "data")


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def threshold_demo() -> dict:
    """An imbalanced 'fraud-like' classifier: ~8% positive, overlapping scores.
    Ships the threshold sweep + a score histogram — enough for a slider-driven
    confusion matrix, PR curve, and score-distribution view."""
    rng = random.Random(7)
    n = 2000
    prevalence = 0.08
    y_true, y_score = [], []
    for _ in range(n):
        pos = rng.random() < prevalence
        # positives score higher on average, but the distributions overlap a lot
        mu = 0.68 if pos else 0.40
        sd = 0.16
        y_true.append(1 if pos else 0)
        y_score.append(_clamp01(rng.gauss(mu, sd)))

    sweep = threshold_sweep(y_true, y_score, n_steps=101)
    for row in sweep:  # round for compact, stable JSON
        for k, v in row.items():
            if isinstance(v, float):
                row[k] = round(v, 4)

    bins = 20
    pos_counts = [0] * bins
    neg_counts = [0] * bins
    for yt, s in zip(y_true, y_score):
        b = min(bins - 1, int(s * bins))
        (pos_counts if yt == 1 else neg_counts)[b] += 1

    return {
        "name": "Fraud-like classifier (synthetic, imbalanced)",
        "n": n,
        "pos": sum(y_true),
        "neg": n - sum(y_true),
        "prevalence": round(sum(y_true) / n, 4),
        "sweep": sweep,
        "hist": {"bins": bins, "pos": pos_counts, "neg": neg_counts},
    }


def judge_demo() -> dict:
    """Pairs where a small quality gap is overturned by position/verbosity bias.
    Ships each pair's verdict under naive vs debiased judging, plus aggregate
    position-flip rates, so the island can show verdicts flipping on order-swap."""
    pairs_raw = [
        ("Concise correct answer", 0.78, "Yes — use a cross-encoder reranker.", 0.70,
         "It depends; there are many factors to weigh here, and ultimately the "
         "best choice will come down to your specific latency and cost budget, "
         "the size of your candidate set, and how much retrieval quality matters."),
        ("Right call, terse", 0.81, "Cache the embeddings.", 0.74,
         "You could consider caching the embeddings, which is generally a good "
         "idea because recomputing them is expensive and the inputs rarely change."),
        ("Correct + short", 0.66, "Add a guardrail metric.", 0.61,
         "Adding a guardrail metric is one option among several; you might also "
         "track latency, cost, and a few business KPIs depending on the product."),
    ]
    pairs = []
    for i, (label, qa, ta, qb, tb) in enumerate(pairs_raw):
        a = Response(f"A{i}", ta, qa)   # better but shorter
        b = Response(f"B{i}", tb, qb)   # worse but much longer
        naive = PairwiseJudge(position_bias=0.06, verbosity_bias=0.0)
        verbose = PairwiseJudge(position_bias=0.0, verbosity_bias=0.0015)
        pairs.append({
            "label": label,
            "a": {"id": a.id, "text": a.text, "quality": qa, "len": len(ta)},
            "b": {"id": b.id, "text": b.text, "quality": qb, "len": len(tb)},
            "truth": a.id,  # A has higher latent quality in every pair
            "position": {
                "order_ab": naive.judge(a, b),
                "order_ba": naive.judge(b, a),
                "debiased": naive.judge_debiased(a, b),
            },
            "verbosity": {"order_ab": verbose.judge(a, b)},
        })

    pset = [(Response(p["a"]["id"], p["a"]["text"], p["a"]["quality"]),
             Response(p["b"]["id"], p["b"]["text"], p["b"]["quality"])) for p in pairs]
    return {
        "pairs": pairs,
        "position_flip_rate": round(position_flip_rate(
            PairwiseJudge(position_bias=0.06), pset), 3),
        "note": "A is the higher-quality answer in every pair. Watch the verdict.",
    }


def confidence_demo() -> dict:
    """Two lessons about eval uncertainty, precomputed for the Ch 3 island.

    (1) ci_by_n — bootstrap 95% CIs on precision/recall/F1 at one threshold over a
    *growing* eval set, so the reader watches the intervals tighten. (2) ab — two
    models on the *same* eval set where B leads A by a hair: the bootstrap CI on
    F1(B) − F1(A) plus a permutation p-value answer 'is the lead real, or noise?'"""
    metric_fns = {"precision": precision, "recall": recall, "f1": f1}
    threshold = 0.5

    # (1) one dataset, evaluated at growing prefixes ---------------------------
    rng = random.Random(13)
    yt, ys = [], []
    for _ in range(1000):
        pos = rng.random() < 0.4
        yt.append(1 if pos else 0)
        ys.append(_clamp01(rng.gauss(0.60 if pos else 0.42, 0.18)))
    ci_by_n = []
    for n in (100, 200, 500, 1000):
        yt_n, ys_n = yt[:n], ys[:n]
        c = confusion_counts(yt_n, ys_n, threshold)
        point = {name: round(fn(c), 4) for name, fn in metric_fns.items()}
        ci = {
            name: [round(v, 4) for v in bootstrap_ci(yt_n, ys_n, threshold, fn, n_boot=600, seed=100 + n)]
            for name, fn in metric_fns.items()
        }
        ci_by_n.append({"n": n, "n_pos": sum(yt_n), "point": point, "ci": ci})

    # (2) two models on the SAME eval set; B is a touch better — but is it real?
    rng2 = random.Random(29)
    n_ab = 600
    yt2, sa, sb = [], [], []
    for _ in range(n_ab):
        pos = rng2.random() < 0.4
        yt2.append(1 if pos else 0)
        sa.append(_clamp01(rng2.gauss(0.58 if pos else 0.44, 0.18)))
        sb.append(_clamp01(rng2.gauss(0.61 if pos else 0.41, 0.18)))
    res = paired_diff_ci(yt2, sa, sb, threshold, f1, n_boot=2000, seed=2024, return_dist=True)
    p = permutation_test(yt2, sa, sb, threshold, f1, n_perm=3000, seed=2024)
    dist = res["dist"]
    bins = 30
    lo_d, hi_d = min(dist), max(dist)
    span = (hi_d - lo_d) or 1.0
    counts = [0] * bins
    for d in dist:
        counts[min(bins - 1, int((d - lo_d) / span * bins))] += 1
    ab = {
        "metric": "F1",
        "threshold": threshold,
        "n": n_ab,
        "a_point": round(f1(confusion_counts(yt2, sa, threshold)), 4),
        "b_point": round(f1(confusion_counts(yt2, sb, threshold)), 4),
        "diff": round(res["diff"], 4),
        "ci": [round(res["lo"], 4), round(res["hi"], 4)],
        "excludes_zero": res["excludes_zero"],
        "p_value": round(p, 4),
        "hist": {"lo": round(lo_d, 4), "hi": round(hi_d, 4), "bins": bins, "counts": counts},
    }

    return {
        "name": "Confidence intervals & A/B significance (synthetic)",
        "note": "CIs shrink as the eval set grows; B leads A by a little — the test says whether that lead is real.",
        "threshold": threshold,
        "ci_by_n": ci_by_n,
        "ab": ab,
    }


def calibration_demo() -> dict:
    """A well-calibrated model vs an overconfident one on the same labels, for the
    Ch 4 reliability-diagram island. Both rank risk by the same signal; only the
    overconfident model's *probabilities* lie — high ECE, worse Brier."""
    rng = random.Random(17)
    n = 2000
    yt, true_p = [], []
    for _ in range(n):
        p = rng.random()
        true_p.append(p)
        yt.append(1 if rng.random() < p else 0)

    def sharpen(p: float, t: float = 0.45) -> float:
        eps = 1e-6
        p = min(1 - eps, max(eps, p))
        logit = math.log(p / (1 - p)) / t  # t < 1 pushes probabilities toward 0/1
        return 1.0 / (1.0 + math.exp(-logit))

    calibrated = [_clamp01(p + rng.gauss(0, 0.04)) for p in true_p]
    overconfident = [sharpen(p) for p in true_p]

    models = {}
    for name, probs in [("calibrated", calibrated), ("overconfident", overconfident)]:
        curve = [
            {"confidence": round(b["confidence"], 4), "accuracy": round(b["accuracy"], 4), "count": b["count"]}
            for b in reliability_curve(yt, probs, n_bins=10) if b["count"]
        ]
        models[name] = {
            "curve": curve,
            "ece": round(expected_calibration_error(yt, probs, 10), 4),
            "brier": round(brier_score(yt, probs), 4),
        }
    return {
        "name": "Calibration: reliable vs overconfident probabilities",
        "note": "Both models rank risk the same way; only the overconfident one's probabilities are wrong. Watch the curve pull off the diagonal.",
        "n": n,
        "models": models,
    }


def rag_demo() -> dict:
    """RAG evaluation in two halves for the Ch 9 island: retrieval quality (a
    ranked list with precision/recall/NDCG as k varies) and answer faithfulness
    (claims grounded — or not — in the retrieved context). Retrieval metrics come
    from mini_eval.retrieval; the grounding labels are authored."""
    chunks_raw = [
        ("d3", True, "Refunds are processed within 5 business days to the original payment method."),
        ("d7", False, "Our customer-service hours are 9am–5pm, Monday to Friday."),
        ("d1", True, "A refund can be requested within 30 days of purchase."),
        ("d9", False, "The company was founded in 2012 in Berlin."),
        ("d2", True, "Refund requests must include the original order number."),
        ("d5", False, "Gift cards and final-sale items are non-refundable."),
        ("d8", False, "Standard shipping is free on orders over $50."),
        ("d4", False, "Returned items must be unopened and in original packaging."),
        ("d6", False, "You can reach support through the in-app chat."),
        ("d0", False, "The mobile app is available on iOS and Android."),
    ]
    retrieved = [c[0] for c in chunks_raw]
    relevant = {c[0] for c in chunks_raw if c[1]}
    sweep = [{
        "k": k,
        "precision": round(precision_at_k(retrieved, relevant, k), 4),
        "recall": round(recall_at_k(retrieved, relevant, k), 4),
        "ndcg": round(ndcg_at_k(retrieved, relevant, k), 4),
    } for k in range(1, len(retrieved) + 1)]
    chunks = [{"rank": i + 1, "id": c[0], "relevant": c[1], "snippet": c[2]} for i, c in enumerate(chunks_raw)]

    claims = [
        {"text": "You can request a refund within 30 days of purchase.", "supported": True, "note": "grounded in chunk d1"},
        {"text": "Refunds go back to your original payment method in about 5 business days.", "supported": True, "note": "grounded in chunk d3"},
        {"text": "You'll also receive a $10 credit for the inconvenience.", "supported": False,
         "note": "Type-I hallucination: no retrieved chunk says this — the model invented it."},
    ]
    supported = sum(1 for c in claims if c["supported"])
    return {
        "name": "RAG evaluation: retrieval and faithfulness",
        "note": "Retrieval finds the context; faithfulness checks that the answer only used it.",
        "retrieval": {
            "query": "How do I get a refund?",
            "n_relevant": len(relevant),
            "chunks": chunks,
            "sweep": sweep,
        },
        "faithfulness": {
            "answer": "You can request a refund within 30 days of purchase. Refunds go back to your original payment method in about 5 business days. You'll also receive a $10 credit for the inconvenience.",
            "claims": claims,
            "score": round(supported / len(claims), 4),
            "note": "Two claims are grounded; the third is a Type-I hallucination — an unsupported addition. Faithfulness catches it; answer-vs-reference accuracy can miss it.",
        },
    }


def retrieval_demo() -> dict:
    """One TF-IDF index over a 10-doc support corpus, four queries with four
    lessons, for the guide-2 Ch 2 island: exact-vocabulary success, the
    paraphrase zero-hit ("money back" vs "refund"), stopword junk in the tail,
    and a morphology miss ("ship" vs "shipping") where a rare shared token
    ranks an unrelated doc. Everything computed by mini_rag.search; relevance
    labels authored."""
    corpus = [
        ("d0", "You may request a refund within 30 days of purchase."),
        ("d1", "We process each refund within 5 business days, paid to the original payment method."),
        ("d2", "To request a refund, include the original order number."),
        ("d3", "Gift cards and final-sale items are non-refundable."),
        ("d4", "Our customer service hours are 9am to 5pm, Monday to Friday."),
        ("d5", "Reach support any time through the in-app chat."),
        ("d6", "Standard shipping is free on orders over 50 dollars."),
        ("d7", "Returned items must be unopened and in original packaging."),
        ("d8", "The mobile app is available on iOS and Android."),
        ("d9", "Invoices include the order number, amount, and due date."),
    ]
    ids = [c[0] for c in corpus]
    index = TfidfIndex([c[1] for c in corpus])

    queries = [
        {
            "label": "Exact vocabulary",
            "query": "How do I request a refund?",
            "relevant": ["d0", "d1", "d2"],
            "lesson": ("The query shares the corpus's own words — \"request\", \"refund\" — "
                       "so all three refund documents surface. Lexical retrieval at its best."),
        },
        {
            "label": "Paraphrase",
            "query": "Can I get my money back?",
            "relevant": ["d0", "d1", "d2"],
            "lesson": ("Zero matches — yet d0–d2 answer this exactly. No query word appears "
                       "anywhere in the corpus, so every TF-IDF score is 0. Meaning matched; "
                       "spelling didn't. This miss is what dense embeddings fix."),
        },
        {
            "label": "Partial match",
            "query": "What are your support hours?",
            "relevant": ["d4", "d5"],
            "lesson": ("\"hours\" and \"support\" find the right two documents — but \"are\" "
                       "also drags in the gift-card policy as a junk tail hit. Shared tokens "
                       "are similarity, not relevance."),
        },
        {
            "label": "Morphology miss",
            "query": "Do you ship internationally?",
            "relevant": ["d6"],
            "lesson": ("\"ship\" ≠ \"shipping\" — without stemming they are different terms, so "
                       "the one shipping document scores 0. Meanwhile \"you\" appears in exactly "
                       "one doc, making it a RARE token with high IDF — and an unrelated refund "
                       "doc ranks first. Rare ≠ meaningful."),
        },
    ]

    out_queries = []
    for q in queries:
        hits = index.search(q["query"], k=10)
        retrieved = [ids[h.index] for h in hits]
        relevant = set(q["relevant"])
        sweep = [{
            "k": k,
            "precision": round(precision_at_k(retrieved, relevant, k), 4),
            "recall": round(recall_at_k(retrieved, relevant, k), 4),
        } for k in range(1, len(hits) + 1)]
        out_queries.append({
            "label": q["label"],
            "query": q["query"],
            "relevant": q["relevant"],
            "lesson": q["lesson"],
            "hits": [{
                "id": ids[h.index],
                "score": round(h.score, 4),
                "relevant": ids[h.index] in relevant,
            } for h in hits],
            "sweep": sweep,
        })

    return {
        "name": "One TF-IDF index, four queries",
        "note": ("All rankings computed by mini_rag (TF-IDF + cosine + top-k) over the corpus "
                 "below; relevance labels are authored ground truth."),
        "corpus": [{"id": i, "text": t} for i, t in corpus],
        "queries": out_queries,
    }


def chunking_demo() -> dict:
    """Chunking strategies on one refund-policy document, for the guide-2 Ch 3
    island. For each (strategy, size): the chunks themselves, boundary
    coherence, and a retrieval check — does the TOP-ranked chunk for the
    question still contain the 30-day limit? The document is tuned so fixed-
    size chunking cuts the key sentence at "...request a refund | within 30
    days" at sizes 40 and 80; overlap rescues 40 but not 80 (the refund-heavy
    run-up chunk outranks the answer). Sentence/paragraph packing never cuts
    mid-fact. All computed by mini_rag; nothing hand-simulated."""
    doc = POLICY_DOC
    query = "How long after purchase can I request a refund?"
    limit_phrase = "30 days"
    sizes = [40, 60, 80]
    strategies = [
        ("fixed", "Fixed-size", lambda t, s: chunk_fixed(t, s)),
        ("fixed_overlap", "Fixed + 10-word overlap", lambda t, s: chunk_fixed(t, s, 10)),
        ("sentence", "Sentence packing", lambda t, s: chunk_sentences(t, s)),
        ("paragraph", "Paragraph packing", lambda t, s: chunk_paragraphs(t, s)),
    ]

    combos = []
    for key, label, fn in strategies:
        for size in sizes:
            chunks = fn(doc, size)
            hits = TfidfIndex(chunks).search(query, k=1)
            top_index = hits[0].index if hits else -1
            top = chunks[top_index] if top_index >= 0 else ""
            fact_intact = limit_phrase in top
            sizes_w = [len(c.split()) for c in chunks]
            combos.append({
                "strategy": key,
                "size": size,
                "n_chunks": len(chunks),
                "avg_words": round(sum(sizes_w) / len(sizes_w), 1),
                "coherence": round(boundary_coherence(chunks), 2),
                "top_index": top_index,
                "fact_intact": fact_intact,
                "chunks": [{
                    "text": c,
                    "has_request": "request a refund" in c,
                    "has_limit": limit_phrase in c,
                    "is_top": i == top_index,
                } for i, c in enumerate(chunks)],
            })

    return {
        "name": "Chunking decides what a vector can say",
        "note": ("One document, one question, twelve chunking configs — every split "
                 "and every ranking computed by mini_rag.chunk + mini_rag.search."),
        "query": query,
        "fact": "You may request a refund within 30 days of purchase",
        "limit_phrase": limit_phrase,
        "strategies": [{"key": k, "label": l} for k, l, _ in strategies],
        "sizes": sizes,
        "combos": combos,
    }


def rag_pipeline_demo() -> dict:
    """Three runs of the full mini_rag pipeline over the paragraph-chunked
    policy doc, for the guide-2 Ch 4 island: a happy path, a retrieval failure
    (junk stopword hits vs a similarity floor), and a context-window failure
    (the answer-bearing chunk retrieved at rank #3 but excluded by the word
    budget). Each variant is a real RagPipeline.run(); verdicts are authored."""
    chunks = chunk_paragraphs(POLICY_DOC, 40)

    def run_variant(question: str, label: str, k: int, budget: int,
                    floor: float, verdict: str) -> dict:
        raw = TfidfIndex(chunks).search(question, k=k)
        trace = RagPipeline(chunks, k=k, budget_words=budget,
                            min_score=floor).run(question)
        included_ids = {h.index for h in trace.included}
        kept_ids = {h.index for h in trace.hits}
        hits = [{
            "chunk": h.index,
            "score": round(h.score, 3),
            "status": ("floored" if h.index not in kept_ids
                       else "included" if h.index in included_ids else "excluded"),
        } for h in raw]
        return {
            "label": label,
            "k": k, "budget": budget, "floor": floor,
            "hits": hits,
            "prompt": trace.prompt,
            "answer": {
                "text": trace.answer.text,
                "supported": trace.answer.supported,
                "source_chunk": (trace.included[trace.answer.source_chunk].index
                                 if trace.answer.source_chunk >= 0 else -1),
            },
            "verdict": verdict,
        }

    scenarios = [
        {
            "key": "happy", "label": "Happy path",
            "question": "How long after purchase can I request a refund?",
            "predict": "Four chunks compete. Which one ranks #1, and will the answer carry a citation?",
            "variants": [run_variant(
                "How long after purchase can I request a refund?",
                "k=4 · budget 200", 4, 200, 0.0,
                ("Every stage did its job: the 30-day chunk ranked #1, fit the "
                 "budget, and the grounded prompt + extractive generator quoted "
                 "the fact with its citation. Boring is the goal."))],
        },
        {
            "key": "junk", "label": "Retrieval failure",
            "question": "Can I get my money back?",
            "predict": ("No corpus chunk shares a meaningful word with this query "
                        "(Ch 2's paraphrase miss). Will the pipeline abstain — or "
                        "answer anyway?"),
            "variants": [
                run_variant("Can I get my money back?", "no similarity floor",
                            4, 200, 0.0,
                            ("Failure point 1 — retrieval. Nothing answers this query, "
                             "but shared filler words (\"can\", \"i\") gave three chunks "
                             "real nonzero scores, and the pipeline confidently assembled "
                             "junk. The generator then did its job on garbage: it quoted "
                             "support-team boilerplate. Similarity is not relevance.")),
                run_variant("Can I get my money back?", "floor = 0.12",
                            4, 200, 0.12,
                            ("The similarity floor turned all-junk retrieval into honest "
                             "emptiness, and the missing-context rule fired: \"I don't "
                             "know\" beats confident boilerplate. 0.12 is not a magic "
                             "number — you calibrate the floor against a golden set "
                             "(Chapter 5).")),
            ],
        },
        {
            "key": "omission", "label": "Context-window failure",
            "question": "Can I get a refund on gift cards?",
            "predict": ("The chunk that answers (\"Gift cards … are non-refundable\") "
                        "exists. Retrieval will find it — but will the generator get "
                        "to see it?"),
            "variants": [
                run_variant("Can I get a refund on gift cards?", "budget = 60 words",
                            4, 60, 0.0,
                            ("Failure point 2 — the context window. The answer WAS "
                             "retrieved, at rank #3 — and then excluded by the word "
                             "budget. The generator can only quote what assembly let "
                             "through, so it returned an overview sentence that mentions "
                             "gift cards without answering. Retrieval metrics look fine; "
                             "the answer is still wrong.")),
                run_variant("Can I get a refund on gift cards?", "budget = 200 words",
                            4, 200, 0.0,
                            ("Same retrieval, bigger budget: the exclusion chunk made it "
                             "into the context and the generator extracted it. Before "
                             "blaming the model, check what it actually saw — the trace "
                             "is the debugging surface.")),
            ],
        },
    ]

    return {
        "name": "One pipeline, three traces",
        "note": ("Every variant is a real mini_rag RagPipeline.run() over the same "
                 "paragraph-chunked policy doc; verdicts are authored."),
        "chunks": [{"id": i, "words": len(c.split()), "text": c} for i, c in enumerate(chunks)],
        "scenarios": scenarios,
    }


# The Ch 5 golden set — also re-run by the Ch 6 upgrade demo.
GOLDEN_SET = [
    {"q": "How long after purchase can I request a refund?",
     "relevant": [2], "fact": "30 days", "reachable": True},
    {"q": "Are gift cards refundable?",
     "relevant": [4], "fact": "non-refundable", "reachable": True},
    {"q": "How long until the money appears after a refund is approved?",
     "relevant": [3], "fact": "five business days", "reachable": True},
    {"q": "Can I get my money back?",
     "relevant": [2], "fact": "30 days", "reachable": False,
     "note": "answerable by the corpus, but shares no token with it — Ch 2's paraphrase miss"},
    {"q": "Do you offer gift wrapping?",
     "relevant": [], "fact": None, "reachable": False,
     "note": "out of scope — the only right answer is an abstain"},
    {"q": "Can I exchange a clearance item?",
     "relevant": [4], "fact": "store credit", "reachable": True,
     "note": "morphology trap: \"item\" ≠ \"items\", \"exchange\" ≠ \"exchanged\""},
]


def categorize_outcome(item: dict, *, supported: bool, answer_text: str,
                       included: set, raw_ids: set) -> tuple[str, str]:
    """Map one golden-set run to an outcome category + failure point (shared
    by the Ch 5 and Ch 6 demos). ``raw_ids`` are pre-floor candidate ids, so a
    chunk eaten by a floor reports as lost-in-assembly, not a ranking miss."""
    relevant = set(item["relevant"])
    if supported:
        if item["fact"] and item["fact"] in answer_text:
            return "correct", ""
        if not relevant or not item["reachable"]:
            return "junk", "FP1 retrieval — answered when it should abstain"
        if relevant <= included:
            return "extraction-miss", "FP3 extraction — fact in context, wrong sentence quoted"
        if relevant & raw_ids:
            return "lost-in-assembly", "FP2 context window — retrieved, then cut by the budget or the floor"
        return "retrieval-miss", "FP1 retrieval — the needed chunk never ranked"
    if not relevant or not item["reachable"]:
        return "abstain-safe", "the missing-context rule did its job"
    return "abstain-missed", "the fact was reachable; the floor/threshold ate it"


def rag_compare_demo() -> dict:
    """Two pipeline configs judged on one golden set, for the guide-2 Ch 5
    island. Six questions over the policy corpus — three answerable, one
    lexically-unreachable paraphrase, one out-of-scope, one morphology trap —
    each run through config A ("ship-it": budget 60, no floor) and config B
    ("hardened": budget 200, floor 0.12). Outcomes are categorized against
    authored ground truth and mapped to Ch 4's failure points; retrieval-half
    context recall comes from mini_eval.recall_at_k. Every answer is a real
    RagPipeline.run()."""
    chunks = chunk_paragraphs(POLICY_DOC, 40)

    golden = GOLDEN_SET
    configs = [
        {"key": "A", "label": "A — ship-it", "detail": "k=4 · budget 60 · no floor",
         "params": dict(k=4, budget_words=60, min_score=0.0)},
        {"key": "B", "label": "B — hardened", "detail": "k=4 · budget 200 · floor 0.12",
         "params": dict(k=4, budget_words=200, min_score=0.12)},
    ]

    questions = []
    raw_index = TfidfIndex(chunks)
    for item in golden:
        raw_ids = {h.index for h in raw_index.search(item["q"], k=4)}
        row = {"q": item["q"], "relevant": item["relevant"],
               "fact": item["fact"], "note": item.get("note", ""), "runs": {}}
        for cfg in configs:
            trace = RagPipeline(chunks, **cfg["params"]).run(item["q"])
            outcome, why = categorize_outcome(
                item, supported=trace.answer.supported, answer_text=trace.answer.text,
                included={h.index for h in trace.included}, raw_ids=raw_ids)
            relevant = set(item["relevant"])
            included_ids = [h.index for h in trace.included]
            ctx_recall = (recall_at_k(included_ids, relevant, max(len(included_ids), 1))
                          if relevant else None)
            row["runs"][cfg["key"]] = {
                "outcome": outcome,
                "why": why,
                "answer": trace.answer.text,
                "supported": trace.answer.supported,
                "included": included_ids,
                "context_recall": (round(ctx_recall, 2) if ctx_recall is not None else None),
            }
        questions.append(row)

    aggregates = {}
    for cfg in configs:
        outs = [q["runs"][cfg["key"]]["outcome"] for q in questions]
        recalls = [q["runs"][cfg["key"]]["context_recall"] for q in questions
                   if q["runs"][cfg["key"]]["context_recall"] is not None]
        aggregates[cfg["key"]] = {
            "correct": outs.count("correct"),
            "harmful": sum(outs.count(o) for o in
                           ("junk", "extraction-miss", "lost-in-assembly", "retrieval-miss")),
            "safe_abstain": outs.count("abstain-safe"),
            "missed_abstain": outs.count("abstain-missed"),
            "avg_context_recall": round(sum(recalls) / len(recalls), 2),
        }

    return {
        "name": "Two configs, one golden set",
        "note": ("Every cell is a real RagPipeline.run(); outcome categories are "
                 "authored ground truth; context recall via mini_eval.recall_at_k."),
        "verdict": ("B is safer than A — the floor converts one junk answer into an "
                    "honest abstain — but the golden set's real finding is that "
                    "NEITHER config is shippable: the failures concentrate in ranking "
                    "quality (morphology traps, run-up chunks outranking answers), "
                    "which no budget or floor can fix. That is Chapter 6's job. "
                    "Without this table, you'd have shipped A believing it worked."),
        "chunks": [{"id": i, "text": c} for i, c in enumerate(chunks)],
        "configs": [{k: c[k] for k in ("key", "label", "detail")} for c in configs],
        "questions": questions,
        "aggregates": aggregates,
    }


def rag_upgrade_demo() -> dict:
    """Before/after for the guide-2 Ch 6 island: config B (Ch 5's hardened
    baseline) vs config C (the upgrade kit: folded vectorizer + query
    expansion + RRF fusion + coverage rerank + coverage floor, with extraction
    reusing the working query and the coverage scorer). Same golden set, same
    outcome categories — every cell computed by mini_rag."""
    chunks = chunk_paragraphs(POLICY_DOC, 40)
    synonyms = {"get my money back": "request a refund"}

    def run_b(question: str) -> dict:
        trace = RagPipeline(chunks, k=4, budget_words=200, min_score=0.12).run(question)
        raw_ids = {h.index for h in TfidfIndex(chunks).search(question, k=4)}
        return {
            "supported": trace.answer.supported, "answer": trace.answer.text,
            "included": [h.index for h in trace.included], "raw_ids": raw_ids,
        }

    def run_c(question: str) -> dict:
        index = TfidfIndex(chunks, tokenizer=fold_tokenize)
        pool = hybrid_search(index, question, synonyms=synonyms, k=4, min_coverage=0.0)
        hits = [h for h in pool if h.score >= 0.34]
        included, _ = assemble_context(hits, 200)
        variants = expand_query(question, synonyms)
        workq = (max(variants, key=lambda v: coverage_score(v, hits[0].doc))
                 if hits else question)
        # extraction with the same coverage scorer, over the working query
        best_text, best_score, best_chunk = ABSTAIN, 0.0, -1
        for ci, h in enumerate(included):
            for s in split_sentences(h.doc):
                sc = coverage_score(workq, s)
                if sc > best_score:
                    best_text, best_score, best_chunk = s, sc, ci
        supported = best_score >= 0.3
        return {
            "supported": supported,
            "answer": best_text if supported else ABSTAIN,
            "included": [h.index for h in included],
            "raw_ids": {h.index for h in pool},
        }

    configs = [
        {"key": "B", "label": "B — hardened (Ch 5)", "detail": "TF-IDF · floor 0.12 · budget 200", "run": run_b},
        {"key": "C", "label": "C — upgraded (Ch 6)", "detail": "fold + expand + RRF + coverage rerank", "run": run_c},
    ]

    questions = []
    for item in GOLDEN_SET:
        row = {"q": item["q"], "relevant": item["relevant"],
               "fact": item["fact"], "note": item.get("note", ""), "runs": {}}
        for cfg in configs:
            r = cfg["run"](item["q"])
            outcome, why = categorize_outcome(
                item, supported=r["supported"], answer_text=r["answer"],
                included=set(r["included"]), raw_ids=r["raw_ids"])
            row["runs"][cfg["key"]] = {
                "outcome": outcome, "why": why, "answer": r["answer"],
                "supported": r["supported"], "included": r["included"],
                "context_recall": (round(recall_at_k(
                    r["included"], set(item["relevant"]),
                    max(len(r["included"]), 1)), 2) if item["relevant"] else None),
            }
        questions.append(row)

    aggregates = {}
    for cfg in configs:
        outs = [q["runs"][cfg["key"]]["outcome"] for q in questions]
        recalls = [q["runs"][cfg["key"]]["context_recall"] for q in questions
                   if q["runs"][cfg["key"]]["context_recall"] is not None]
        aggregates[cfg["key"]] = {
            "correct": outs.count("correct"),
            "harmful": sum(outs.count(o) for o in
                           ("junk", "extraction-miss", "lost-in-assembly", "retrieval-miss")),
            "safe_abstain": outs.count("abstain-safe"),
            "missed_abstain": outs.count("abstain-missed"),
            "avg_context_recall": round(sum(recalls) / len(recalls), 2),
        }

    return {
        "name": "The upgrade kit, judged by the same exam",
        "note": ("Config C = folded vectorizer + query expansion + RRF fusion + "
                 "coverage rerank + a coverage floor; extraction reuses the working "
                 "query and the coverage scorer. Every cell computed by mini_rag."),
        "verdict": ("The ranking upgrades fix exactly what Chapter 5 localized to "
                    "ranking: the paraphrase now finds the policy (expansion), the "
                    "morphology trap is dead (folding), and the off-topic junk became "
                    "an honest abstain (a floor in coverage units). The one residual "
                    "failure is extraction — the toy generator quoting the wrong "
                    "sentence from the right chunk. That stage's upgrade isn't more "
                    "retrieval; it's a real LLM — which is why faithfulness measurement "
                    "(guide 1, Ch 9) arrives the same day the LLM does."),
        "chunks": [{"id": i, "text": c} for i, c in enumerate(chunks)],
        "configs": [{k: c[k] for k in ("key", "label", "detail")} for c in configs],
        "questions": questions,
        "aggregates": aggregates,
    }


def budget_demo() -> dict:
    """The two budgets of a production RAG bot, for the guide-2 Ch 7 island:
    a lever grid (answer length x context chunks x model tier x cache rate)
    where every cell's latency and cost are computed via mini_rag.budget.
    Latency model: retrieval stages are constants; per-model TTFT and
    tokens/sec are representative API-class numbers (stated, not measured —
    the lesson is the structure, and 'measure your provider' is the takeaway)."""
    QPD = 10_000                      # queries/day
    SLA_MS = 2000.0                   # p95 target on total latency
    STAGES_MS = {"embed": 20.0, "search": 15.0, "rerank": 80.0}
    CHUNK_TOKENS, PROMPT_TOKENS, QUESTION_TOKENS = 300, 150, 50
    MODELS = {
        "small": {"label": "small (mini-tier)", "ttft_ms": 250.0, "tok_per_s": 150.0,
                  "rate_in": 0.15, "rate_out": 0.60},
        "large": {"label": "large (frontier)", "ttft_ms": 550.0, "tok_per_s": 40.0,
                  "rate_in": 2.50, "rate_out": 10.00},
    }
    CASCADE_EASY = 0.7                # fraction routed to the small model

    outputs = [50, 200, 500]
    ks = [2, 4, 8]
    model_keys = ["small", "large", "cascade"]
    caches = [0.0, 0.3, 0.6]

    def cell(output: int, k: int, model: str, cache: float) -> dict:
        input_tokens = k * CHUNK_TOKENS + PROMPT_TOKENS + QUESTION_TOKENS
        stages = sum(STAGES_MS.values())

        def lat(mkey: str) -> tuple[float, float]:
            m = MODELS[mkey]
            ttft = stages + m["ttft_ms"]
            decode = output / m["tok_per_s"] * 1000.0
            return ttft, decode

        def cost(mkey: str) -> float:
            m = MODELS[mkey]
            return api_cost_usd(input_tokens, output, m["rate_in"], m["rate_out"])

        if model == "cascade":
            # p95 is the escalated (slow) path; cost is the blended average
            ttft, decode = lat("large")
            cost_q = cascade_cost_usd(CASCADE_EASY, cost("small"), cost("large"))
        else:
            ttft, decode = lat(model)
            cost_q = cost(model)

        eff_cost = effective_cost_usd(cost_q, cache)
        total = ttft + decode
        return {
            "output": output, "k": k, "model": model, "cache": cache,
            "input_tokens": input_tokens,
            "ttft_ms": round(ttft), "decode_ms": round(decode),
            "total_ms": round(total), "sla_ok": total <= SLA_MS,
            "cost_q": round(cost_q, 5), "eff_cost_q": round(eff_cost, 5),
            "cost_month": round(eff_cost * QPD * 30, 0),
        }

    combos = [cell(o, k, m, c) for o in outputs for k in ks
              for m in model_keys for c in caches]

    return {
        "name": "Two budgets: milliseconds and dollars",
        "note": ("Latency and cost computed by mini_rag.budget; per-model TTFT and "
                 "tokens/sec are representative API-class constants (the structure is "
                 "the lesson — measure your own provider). Cache hits affect the bill, "
                 "not the p95 (misses still pay full latency). Cascade p95 = the "
                 "escalated path; cascade cost = the 70/30 blend."),
        "qpd": QPD, "sla_ms": SLA_MS,
        "levers": {
            "output": outputs, "k": ks,
            "model": [{"key": "small", "label": "small (mini-tier)"},
                      {"key": "large", "label": "large (frontier)"},
                      {"key": "cascade", "label": "cascade 70/30"}],
            "cache": caches,
        },
        "defaults": {"output": 200, "k": 4, "model": "large", "cache": 0.0},
        "combos": combos,
    }


def agent_loop_demo() -> dict:
    """Four real runs of mini_agent.run_agent for the guide-2 Ch 8 island:
    the competent path (facts -> policy -> gated write), the gate holding on
    a gift card, a hallucinated tool surfaced-and-recovered, and the loop
    guard ending a stuck agent. Scripted policies, deterministic; every
    thought/action/observation below is actual loop output."""
    import mini_agent.tools as agent_tools
    from mini_agent import (run_agent, make_support_tools,
                            support_policy, confused_policy, stuck_policy)

    tools = make_support_tools()
    writes = {t.name: t.writes for t in tools}

    scenarios_spec = [
        {"key": "happy", "label": "Eligible refund",
         "goal": "Customer: please refund order 18342",
         "policy": support_policy,
         "predict": ("Three tools are available, one of which moves money. "
                     "In what order will a competent agent use them — and how "
                     "many steps until it's done?"),
         "lesson": ("Facts first (order_status), policy second (policy_lookup), and "
                    "only then the write — with the eligibility reasoning recorded in "
                    "the thoughts. The trace is the audit log.")},
        {"key": "gate", "label": "The gate holds",
         "goal": "Customer: please refund order 20117 (a gift card)",
         "policy": support_policy,
         "predict": ("The order is a gift card, and the policy says those are "
                     "non-refundable. Will start_refund get called anyway?"),
         "lesson": ("The write tool never fired: the policy checked category before "
                    "eligibility and refused with the reason. A wrong READ is free to "
                    "retry; a wrong WRITE is an incident — gate the writes.")},
        {"key": "hallucinated", "label": "Hallucinated tool",
         "goal": "Customer: what's the refund policy for order 18342?",
         "policy": confused_policy,
         "predict": ("This agent's first move is to call check_warranty — a tool "
                     "that doesn't exist. Crash, or recover?"),
         "lesson": ("The unknown tool became an observation, not an exception — and "
                    "the error message listed what IS available, so the very next step "
                    "recovered. Tool errors the model can read are a design choice.")},
        {"key": "stuck", "label": "Stuck loop",
         "goal": "Customer: please refund order 18342",
         "policy": stuck_policy,
         "predict": ("This agent re-checks the order status forever. What stops "
                     "it — and after how many steps?"),
         "lesson": ("The loop guard aborted after the same (tool, args) repeated: "
                    "no progress, only spend. Without it, max_steps is the only "
                    "backstop — and every wasted step is a paid LLM call in production.")},
    ]

    out = []
    for spec in scenarios_spec:
        agent_tools._REFUNDS_STARTED.clear()
        trace = run_agent(spec["goal"], tools, spec["policy"], max_steps=8)
        out.append({
            "key": spec["key"], "label": spec["label"], "goal": spec["goal"],
            "predict": spec["predict"], "lesson": spec["lesson"],
            "status": trace.status, "answer": trace.answer,
            "steps": [{
                "n": i + 1,
                "thought": s.thought,
                "tool": s.action.tool if s.action else None,
                "args": (", ".join(f"{k}={v!r}" for k, v in s.action.args.items())
                         if s.action else ""),
                "writes": bool(s.action and writes.get(s.action.tool, False)),
                "observation": s.observation,
            } for i, s in enumerate(trace.steps)],
        })

    return {
        "name": "One loop, four traces",
        "note": ("Every trace is real run_agent output over scripted policies — "
                 "deterministic stand-ins for the LLM in the reasoning seat. The "
                 "loop, tools, guards, and gates are exactly what production keeps."),
        "tools": [{"name": t.name, "description": t.description, "writes": t.writes}
                  for t in tools],
        "scenarios": out,
    }


def orchestra_demo() -> dict:
    """Two real run_supervisor runs for the guide-2 Ch 9 island: the triage
    day (three tickets, three specialists, clean contexts) and the sick day
    (the refund worker loops; the failure is isolated and the ticket rerouted
    to a human). Scripted router + policies — every handoff and inner step is
    actual output."""
    import mini_agent.tools as agent_tools
    from mini_agent import (run_supervisor, make_support_crew, sick_day_crew,
                            triage_router)

    def serialize(trace) -> dict:
        return {
            "status": trace.status,
            "summary": trace.summary,
            "handoffs": [{
                "n": i + 1,
                "thought": h.thought,
                "worker": h.worker,
                "goal": h.goal,
                "worker_status": h.trace.status,
                "worker_answer": h.trace.answer,
                "inner_steps": [{
                    "thought": s.thought,
                    "tool": s.action.tool if s.action else None,
                    "args": (", ".join(f"{k}={v!r}" for k, v in s.action.args.items())
                             if s.action else ""),
                    "observation": s.observation,
                } for s in h.trace.steps],
            } for i, h in enumerate(trace.handoffs)],
        }

    agent_tools._REFUNDS_STARTED.clear()
    happy = run_supervisor("Handle the queue: T1, T2, T3",
                           make_support_crew(), triage_router)
    agent_tools._REFUNDS_STARTED.clear()
    sick = run_supervisor("Handle the queue: T1, T2, T3",
                          sick_day_crew(), triage_router)

    crew = make_support_crew()
    return {
        "name": "One supervisor, three specialists",
        "note": ("Both runs are real run_supervisor output over scripted "
                 "router/policies. Expand a handoff to read the worker's inner "
                 "loop — each worker's context contains ONLY its own ticket."),
        "workers": [{"name": w.name, "description": w.description,
                     "n_tools": len(w.tools)} for w in crew],
        "scenarios": [
            {"key": "triage", "label": "Triage day",
             "task": "Handle the queue: T1 (policy question) · T2 (refund request) · T3 (wants a human)",
             "predict": ("Three tickets, three specialists with different tools. "
                         "Who gets what — and does any worker ever see another "
                         "worker's ticket?"),
             "lesson": ("Each specialist ran with a clean context (only its own "
                        "ticket), least-privilege tools, and returned through the "
                        "supervisor — no worker-to-worker chatter. The supervisor's "
                        "lane plus the inner traces is the whole debugging story."),
             **serialize(happy)},
            {"key": "sickday", "label": "Sick day (failure isolation)",
             "task": "Same queue — but the refund worker is stuck in Chapter 8's loop",
             "predict": ("The refund specialist will fail (loop guard). Does the "
                         "whole queue fail with it?"),
             "lesson": ("Failure isolation: the worker's loop_detected status became "
                        "a record the router could read, the ticket was rerouted to "
                        "the front desk, and the queue still completed — degraded, "
                        "not dead. One agent's failure should cost one handoff, "
                        "never the run."),
             **serialize(sick)},
        ],
    }


def agent_demo() -> dict:
    """pass@k curves for a flaky vs a reliable agent, for the Ch 10 island. Each
    suite is 40 tasks sampled K times; pass@k rises with attempts, but pass@1 (the
    first-try success a user actually gets) tells the flaky agent's true story."""
    rng = random.Random(31)
    K = 10
    scenarios = []
    for label, p in [("Flaky agent", 0.35), ("Reliable agent", 0.80)]:
        tasks = []
        for _ in range(40):
            tp = _clamp01(p + rng.gauss(0, 0.08))           # task-level jitter
            c = sum(1 for _ in range(K) if rng.random() < tp)
            tasks.append((K, c))
        curve = [{"k": k, "pass": round(mean_pass_at_k(tasks, k), 4)} for k in range(1, K + 1)]
        scenarios.append({
            "label": label, "K": K, "n_tasks": len(tasks),
            "pass1": curve[0]["pass"], "passK": curve[-1]["pass"], "curve": curve,
        })
    return {
        "name": "pass@k: attempts vs reliability",
        "note": "pass@k rises with attempts; pass@1 is what a user gets on the first try.",
        "scenarios": scenarios,
    }


def monitoring_demo() -> dict:
    """A frozen offline metric vs a live online signal over 30 days, for the Ch 11
    island. The offline number stays flat and green (the eval set never changes);
    the online signal drifts past its guardrail after the input mix shifts — the
    failure only monitoring catches. Synthetic, seeded; no model involved."""
    rng = random.Random(23)
    days = 30
    guardrail = 0.55  # max tolerable human-override rate
    series = []
    for d in range(days):
        offline = _clamp01(0.30 + rng.gauss(0, 0.01))               # frozen set -> flat
        drift = 0.0 if d < 12 else (d - 12) * 0.025                  # shift starts ~day 12
        online = _clamp01(0.30 + drift + rng.gauss(0, 0.02))
        series.append({"day": d, "offline": round(offline, 4), "online": round(online, 4)})
    breach = next((p["day"] for p in series if p["online"] > guardrail), None)
    return {
        "name": "Offline looks fine; online drifts",
        "note": "The frozen offline eval stays flat and green; the live signal drifts past the guardrail. Only monitoring catches it.",
        "days": days,
        "guardrail": guardrail,
        "breach_day": breach,
        "ylabel": "human-override rate",
        "series": series,
    }


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, data in [
        ("threshold_demo", threshold_demo()),
        ("judge_demo", judge_demo()),
        ("confidence_demo", confidence_demo()),
        ("calibration_demo", calibration_demo()),
        ("rag_demo", rag_demo()),
        ("retrieval_demo", retrieval_demo()),
        ("chunking_demo", chunking_demo()),
        ("rag_pipeline_demo", rag_pipeline_demo()),
        ("rag_compare_demo", rag_compare_demo()),
        ("rag_upgrade_demo", rag_upgrade_demo()),
        ("budget_demo", budget_demo()),
        ("agent_loop_demo", agent_loop_demo()),
        ("orchestra_demo", orchestra_demo()),
        ("agent_demo", agent_demo()),
        ("monitoring_demo", monitoring_demo()),
    ]:
        path = os.path.join(OUT, f"{name}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"wrote {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
