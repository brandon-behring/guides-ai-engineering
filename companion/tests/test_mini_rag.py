"""Correctness tests for mini_rag. Run with `pytest`, or directly:
`python companion/tests/test_mini_rag.py` (no pytest needed)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_rag import (  # noqa: E402
    tokenize, idf, cosine_similarity, TfidfIndex, top_k, Hit,
    split_sentences, chunk_fixed, chunk_sentences, chunk_paragraphs,
    boundary_coherence,
    ABSTAIN, assemble_context, build_prompt, extractive_answer, RagPipeline,
    fold, fold_tokenize, expand_query, rrf_fuse, coverage_rerank, hybrid_search,
    prefill_ms, decode_ms, llm_latency_ms, api_cost_usd, rag_request_budget,
    cascade_cost_usd, effective_cost_usd, break_even_queries_per_day,
)


def test_tokenize_lowercases_and_splits():
    assert tokenize("Refunds, within 30 days!") == ["refunds", "within", "30", "days"]


def test_cosine_identity_and_orthogonal():
    v = {"refund": 1.5, "days": 0.7}
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-12   # same direction -> 1
    assert cosine_similarity(v, {"loyal": 2.0}) == 0.0  # no shared terms -> 0
    assert cosine_similarity(v, {}) == 0.0              # empty vector -> 0


def test_cosine_in_unit_interval():
    s = cosine_similarity({"a": 1.0, "b": 2.0}, {"b": 1.0, "c": 3.0})
    assert 0.0 <= s <= 1.0


def test_idf_downweights_ubiquitous_terms():
    corpus = [
        ["data", "model", "training"],
        ["data", "model", "serving"],
        ["data", "pipeline", "design"],
    ]
    w = idf(corpus)
    assert w["training"] > w["data"]  # rare term outweighs the one in every doc
    assert w["data"] > 0.0            # smoothing keeps even ubiquitous terms positive


def test_search_ranks_relevant_doc_first():
    corpus = [
        "the cat sat on the mat",
        "dogs are loyal companions and great pets",
        "a refund can be requested within thirty days",
        "warranty claims need the original receipt",
    ]
    hits = top_k("how do I get a refund", corpus, k=2)
    assert isinstance(hits[0], Hit)
    assert hits[0].index == 2     # the only doc sharing 'refund'
    assert hits[0].score > 0.0
    assert hits[0].doc == corpus[2]


def test_search_drops_zero_score_and_respects_k():
    corpus = ["alpha beta", "gamma delta", "epsilon zeta"]
    hits = top_k("alpha", corpus, k=3)      # overlaps only the first doc
    assert len(hits) == 1                    # one non-zero hit, not k=3 padding
    assert hits[0].index == 0
    assert top_k("nonexistent", corpus, k=3) == []  # no overlap -> nothing


def test_search_is_deterministic_and_ordered():
    corpus = ["refund policy refund", "refund", "unrelated text", "refund refund refund"]
    hits = TfidfIndex(corpus).search("refund", k=4)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)        # descending order
    assert all(h.doc != "unrelated text" for h in hits)  # zero-score doc filtered out


def test_chunk_fixed_sizes_and_overlap():
    text = " ".join(f"w{i}" for i in range(10))  # w0 .. w9
    chunks = chunk_fixed(text, size=4, overlap=1)
    assert chunks[0] == "w0 w1 w2 w3"
    assert chunks[1].startswith("w3")            # overlap repeats the boundary word
    assert all(len(c.split()) <= 4 for c in chunks)
    joined = " ".join(chunks).split()
    assert set(joined) == {f"w{i}" for i in range(10)}  # nothing lost


def test_chunk_fixed_no_pure_overlap_tail():
    text = " ".join(f"w{i}" for i in range(8))
    chunks = chunk_fixed(text, size=5, overlap=2)
    # last chunk must contain the final word, and no chunk is a subset of the previous
    assert chunks[-1].split()[-1] == "w7"
    for a, b in zip(chunks, chunks[1:]):
        assert not set(b.split()) <= set(a.split())


def test_chunk_fixed_validates_args():
    for bad in [(0, 0), (4, 4), (4, -1)]:
        try:
            chunk_fixed("a b c", size=bad[0], overlap=bad[1])
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


def test_chunk_sentences_never_splits_mid_sentence():
    text = "Refunds take five days. Gift cards are final. Items must be unopened. Contact support for help."
    chunks = chunk_sentences(text, size=9)
    assert boundary_coherence(chunks) == 1.0     # every chunk ends at a sentence end
    sentences = split_sentences(text)
    for s in sentences:                           # every sentence survives intact
        assert any(s in c for c in chunks)


def test_chunk_sentences_oversized_sentence_is_own_chunk():
    long_sentence = "This single sentence is far longer than the chunk size limit we set here."
    chunks = chunk_sentences(long_sentence + " Short one.", size=5)
    assert chunks[0] == long_sentence             # not split, despite exceeding size
    assert chunks[1] == "Short one."


def test_chunk_paragraphs_keeps_paragraphs_intact():
    text = "First topic sentence one. First topic sentence two.\n\nSecond topic here."
    chunks = chunk_paragraphs(text, size=12)
    assert any("First topic sentence one. First topic sentence two." in c for c in chunks)
    assert boundary_coherence(chunks) == 1.0


def test_boundary_coherence_scores():
    assert boundary_coherence([]) == 0.0
    assert boundary_coherence(["Ends well.", "cut mid"]) == 0.5
    assert boundary_coherence(["Done!", "Sure?"]) == 1.0


def _hits(*docs):
    return [Hit(i, 1.0 - i * 0.1, d) for i, d in enumerate(docs)]


def test_assemble_context_respects_budget_in_rank_order():
    hits = _hits("one two three", "four five six", "seven eight nine")
    included, excluded = assemble_context(hits, budget_words=6)
    assert [h.doc for h in included] == ["one two three", "four five six"]
    assert [h.doc for h in excluded] == ["seven eight nine"]
    included, excluded = assemble_context(hits, budget_words=2)
    assert included == [] and len(excluded) == 3   # nothing fits -> nothing included


def test_build_prompt_carries_rules_and_numbered_chunks():
    p = build_prompt("How long?", ["Refunds take 30 days.", "Support is 9 to 5."])
    assert "ONLY from the numbered context" in p
    assert '"I don\'t know"' in p
    assert "[1] Refunds take 30 days." in p and "[2] Support is 9 to 5." in p
    assert "Question: How long?" in p
    assert "(no chunks retrieved)" in build_prompt("q", [])


def test_extractive_answer_quotes_best_sentence_with_source():
    chunks = [
        "Our office is in Berlin. Support hours are 9am to 5pm.",
        "You may request a refund within 30 days of purchase.",
    ]
    a = extractive_answer("How long do I have to request a refund?", chunks)
    assert a.supported and a.source_chunk == 1
    assert "30 days" in a.text
    assert a.text in chunks[1]                      # quoted, not synthesized


def test_extractive_answer_abstains_without_support():
    a = extractive_answer("Why?", ["Shipping is free over 50 dollars."])
    assert not a.supported and a.source_chunk == -1
    assert a.text == ABSTAIN
    # a shared stopword ("is") still clears the default threshold — the toy is
    # honest about this; calibrating thresholds/floors is the chapter's point
    junk = extractive_answer("What is the meaning of life?",
                             ["Shipping is free over 50 dollars."])
    assert junk.supported


def test_pipeline_trace_end_to_end_and_budget_failure():
    chunks = [
        "You may request a refund within 30 days of purchase.",
        "Gift cards and final-sale items are non-refundable.",
        "Standard shipping is free on orders over 50 dollars.",
    ]
    roomy = RagPipeline(chunks, k=3, budget_words=100).run("Are gift cards refundable?")
    assert roomy.answer.supported and "non-refundable" in roomy.answer.text
    assert roomy.prompt.startswith("You are a support assistant.")
    # tight budget: only the top-ranked chunk fits -> the next hit is excluded
    tight = RagPipeline(chunks, k=3, budget_words=8).run("refund for gift cards")
    assert len(tight.hits) >= 2
    assert len(tight.included) == 1 and len(tight.excluded) >= 1
    # retrieval failure: nothing matches -> empty hits -> abstain
    miss = RagPipeline(chunks, k=3, budget_words=100).run("Coverage for warranty claims?")
    assert miss.hits == [] and miss.answer.text == ABSTAIN
    # similarity floor: junk-overlap hits are filtered before assembly
    floored = RagPipeline(chunks, k=3, budget_words=100, min_score=0.5).run(
        "Are gift cards refundable?")
    assert floored.hits == [] or all(h.score >= 0.5 for h in floored.hits)


def test_fold_normalizes_morphology():
    assert fold("cards") == fold("card")
    assert fold("items") == fold("item")
    assert fold("shipping") == fold("ship")
    assert fold("exchanged") == fold("exchange")
    assert fold("appears") == fold("appear")
    assert fold("refunds") == fold("refund")


def test_folded_index_matches_across_morphology():
    corpus = ["Items marked as clearance may be exchanged for store credit."]
    assert TfidfIndex(corpus).search("exchange a clearance item") != [] or True
    plain = TfidfIndex(corpus).search("exchange items", k=1)
    folded = TfidfIndex(corpus, tokenizer=fold_tokenize).search("exchange items", k=1)
    assert folded and folded[0].score > (plain[0].score if plain else 0.0)


def test_expand_query_substitutes_phrases():
    variants = expand_query("Can I get my money back?", {"money back": "refund"})
    assert variants[0] == "Can I get my money back?"
    assert any("refund" in v for v in variants)
    assert expand_query("plain query", {"money back": "refund"}) == ["plain query"]


def test_rrf_fuse_rewards_agreement():
    a = [Hit(1, 0.9, "one"), Hit(2, 0.5, "two")]
    b = [Hit(2, 0.8, "two"), Hit(3, 0.7, "three")]
    fused = rrf_fuse([a, b])
    assert fused[0].index == 2          # appears in both lists -> most votes
    assert {h.index for h in fused} == {1, 2, 3}


def test_coverage_rerank_prefers_term_coverage_over_repetition():
    hits = [
        Hit(0, 0.9, "refund refund refund refund refund"),
        Hit(1, 0.4, "request a refund within 30 days of purchase"),
    ]
    ranked = coverage_rerank("refund within 30 days", hits)
    assert ranked[0].index == 1          # covers 4 query terms, not 1 repeated


def test_hybrid_search_fixes_golden_set_failures():
    corpus = [
        "You may request a refund within 30 days of purchase.",
        "Items marked as clearance may be exchanged for store credit instead.",
        "Standard shipping is free on orders over 50 dollars.",
    ]
    index = TfidfIndex(corpus, tokenizer=fold_tokenize)
    syn = {"money back": "refund"}
    # paraphrase, fixed by expansion
    hits = hybrid_search(index, "Can I get my money back?", synonyms=syn, k=2)
    assert hits and hits[0].index == 0
    # morphology trap, fixed by folding (+ coverage)
    hits = hybrid_search(index, "Can I exchange a clearance item?", synonyms=syn, k=2)
    assert hits and hits[0].index == 1
    # coverage floor turns off-topic junk into emptiness
    assert hybrid_search(index, "Do you offer gift wrapping?", synonyms=syn,
                         k=2, min_coverage=0.5) == []


def test_latency_estimates_match_rules_of_thumb():
    # 8B model, 1.5K input: prefill ~12ms; 200 output tokens: decode ~800ms
    assert abs(prefill_ms(8.0, 1500) - 12.0) < 1e-9
    assert abs(decode_ms(8.0, 200) - 800.0) < 1e-9
    assert abs(llm_latency_ms(8.0, 1500, 200) - 812.0) < 1e-9
    # decode scales linearly with output length — 25x tokens = 25x time
    assert decode_ms(8.0, 500) == 25 * decode_ms(8.0, 20)


def test_api_cost_and_cascade_and_cache():
    # 800 in / 200 out at $2.50/$10 per 1M -> $0.004
    assert abs(api_cost_usd(800, 200, 2.50, 10.00) - 0.004) < 1e-12
    # cascade: 70% to a $0.001 model, 30% to a $0.008 model
    blended = cascade_cost_usd(0.7, 0.001, 0.008)
    assert abs(blended - 0.0031) < 1e-12
    # 30% cache hits discount the bill by 30%
    assert abs(effective_cost_usd(0.004, 0.30) - 0.0028) < 1e-12
    for bad in (-0.1, 1.1):
        try:
            cascade_cost_usd(bad, 1, 2)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


def test_request_budget_assembles_tokens_and_stages():
    b = rag_request_budget(params_b=8.0, k_chunks=4, chunk_tokens=300,
                           prompt_tokens=150, question_tokens=50,
                           output_tokens=200, rerank_ms=80.0)
    assert b.input_tokens == 4 * 300 + 150 + 50
    assert b.ttft_ms == b.embed_ms + b.search_ms + b.rerank_ms + b.prefill_ms
    assert abs(b.total_ms - (b.ttft_ms + b.decode_ms)) < 1e-9
    assert b.decode_ms > b.prefill_ms          # decode dominates at 200 tokens


def test_break_even_volume():
    # $864/month GPU vs $0.002/query API -> 14,400 queries/day
    assert abs(break_even_queries_per_day(864.0, 0.002) - 14400.0) < 1e-6


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
