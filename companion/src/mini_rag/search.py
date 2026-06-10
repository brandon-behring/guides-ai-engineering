"""Vector search — the retrieval mechanism a RAG system is built on.

Before a model can answer *from your documents*, you have to find the few that are
relevant. This is the simplest honest version of that: turn text into TF-IDF vectors
(term frequency x inverse document frequency), then rank documents by cosine similarity
to the query. It's sparse, lexical retrieval — no neural network — which is exactly why
you can read every line.

Chapter 2 contrasts this with dense / semantic embeddings (where "refund" and "money
back" land near each other even with no shared words); the *search* half — vectorize,
score by cosine, take the top-k — is identical, which is the point of building it here.

Stdlib-only, **for learning, not production** (bridge to scikit-learn's TfidfVectorizer,
FAISS, or a managed vector DB). Grading the retrieval is a different job — see
``mini_eval.retrieval`` (precision@k, recall@k, NDCG) in the Evaluation guide.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from math import log, sqrt

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase and split into alphanumeric tokens. Deliberately crude — no stemming,
    so "refund" and "refunds" are *different* terms. That limitation (lexical, not
    semantic, matching) is exactly what motivates dense embeddings in Chapter 2."""
    return _TOKEN.findall(text.lower())


def idf(corpus_tokens: list[list[str]]) -> dict[str, float]:
    """Inverse document frequency for every term, smoothed like scikit-learn:

        idf(t) = ln((1 + N) / (1 + df_t)) + 1

    The +1s avoid division by zero and keep every weight positive; the shape still
    down-weights terms that appear in many documents (a word in every doc carries no
    signal) and rewards the rare, discriminating ones."""
    n = len(corpus_tokens)
    df: dict[str, int] = {}
    for tokens in corpus_tokens:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1
    return {term: log((1 + n) / (1 + d)) + 1.0 for term, d in df.items()}


def tfidf_vector(tokens: list[str], idf_map: dict[str, float]) -> dict[str, float]:
    """A sparse TF-IDF vector: each term's count (TF) times its IDF weight. Terms not
    in the corpus vocabulary get no entry (their IDF is undefined), so an
    out-of-vocabulary query word simply contributes nothing."""
    tf: dict[str, float] = {}
    for term in tokens:
        tf[term] = tf.get(term, 0.0) + 1.0
    return {term: count * idf_map[term] for term, count in tf.items() if term in idf_map}


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine of the angle between two sparse vectors: dot product over the product of
    norms. Returns 0.0 when either vector is empty or they share no terms, and 1.0 for
    identical direction. For non-negative TF-IDF vectors the result lies in [0, 1]."""
    if not a or not b:
        return 0.0
    small, large = (a, b) if len(a) <= len(b) else (b, a)  # iterate the shorter one
    dot = sum(w * large.get(term, 0.0) for term, w in small.items())
    if dot == 0.0:
        return 0.0
    norm_a = sqrt(sum(w * w for w in a.values()))
    norm_b = sqrt(sum(w * w for w in b.values()))
    return dot / (norm_a * norm_b)


@dataclass(frozen=True)
class Hit:
    """One search result: the document's index in the corpus, its cosine score, and the
    document text itself (so callers don't have to index back into the corpus)."""

    index: int
    score: float
    doc: str


class TfidfIndex:
    """A tiny in-memory TF-IDF index — the "vector store" of a RAG system, minus the
    scale. Build it once over a corpus, then ``search`` it with any query.

    ``tokenizer`` is the swappable vectorizer seam (Chapter 2's lesson made
    literal): pass a folding tokenizer (Chapter 6) and "items" matches "item"
    with no other change to the search machinery."""

    def __init__(self, corpus: list[str], tokenizer=tokenize) -> None:
        self.docs = list(corpus)
        self.tokenizer = tokenizer
        corpus_tokens = [self.tokenizer(d) for d in self.docs]
        self.idf = idf(corpus_tokens)
        self._vectors = [tfidf_vector(t, self.idf) for t in corpus_tokens]

    def search(self, query: str, k: int = 5) -> list[Hit]:
        """Rank documents by cosine similarity to the query and return the top-k. Ties
        break by document order, so results are deterministic. Hits with score 0 (no
        shared terms) are dropped — a query that matches nothing returns fewer than k,
        never padding."""
        if k <= 0:
            return []
        qvec = tfidf_vector(self.tokenizer(query), self.idf)
        scored = [
            Hit(i, cosine_similarity(qvec, dvec), self.docs[i])
            for i, dvec in enumerate(self._vectors)
        ]
        scored = [h for h in scored if h.score > 0.0]
        scored.sort(key=lambda h: (-h.score, h.index))
        return scored[:k]


def top_k(query: str, corpus: list[str], k: int = 5) -> list[Hit]:
    """Convenience: build an index over ``corpus`` and return the top-k hits for
    ``query``. Rebuilds the index every call — fine for learning, wasteful in a loop
    (build one ``TfidfIndex`` and reuse it)."""
    return TfidfIndex(corpus).search(query, k)
