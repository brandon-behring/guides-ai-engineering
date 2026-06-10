"""Correctness tests for mini_rag. Run with `pytest`, or directly:
`python companion/tests/test_mini_rag.py` (no pytest needed)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_rag import (  # noqa: E402
    tokenize, idf, cosine_similarity, TfidfIndex, top_k, Hit,
    split_sentences, chunk_fixed, chunk_sentences, chunk_paragraphs,
    boundary_coherence,
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


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
