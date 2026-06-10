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
)

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
    doc = "\n\n".join([
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
        ("agent_demo", agent_demo()),
        ("monitoring_demo", monitoring_demo()),
    ]:
        path = os.path.join(OUT, f"{name}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"wrote {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
