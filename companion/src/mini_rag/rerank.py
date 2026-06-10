"""Advanced retrieval — the upgrades that attack ranking quality itself.

Chapter 5's golden set localized three failures to one cause: brittle lexical
ranking. This module is the upgrade kit, each piece the honest minimal version
of a production pattern:

- ``fold`` / ``fold_tokenize`` — a ten-line stemmer (strip s/ed/ing, doubled
  consonants, trailing e) so "items" matches "item" and "exchanged" matches
  "exchange". It will mangle real text in fun ways ("pure" -> "pur"); the
  point is that folding is a **vectorizer swap** — production reaches for
  Porter/Snowball stemming or skips the problem entirely with dense embeddings.
- ``expand_query`` — query rewriting via a phrase map ("money back" ->
  "refund"). Production generates the variants with an LLM (multi-query,
  HyDE, step-back); the *mechanism* — search every variant, fuse the
  rankings — is identical and lives here.
- ``rrf_fuse`` — Reciprocal Rank Fusion, the real algorithm hybrid search
  uses to merge ranked lists without comparing incomparable scores:
  RRF(d) = sum over lists of 1 / (k + rank_i(d)), k = 60.
- ``coverage_rerank`` — a second-stage scorer that reads each (query, doc)
  *pair* more carefully than the first stage could: what fraction of the
  query's terms does the document actually cover? Same interface as a
  cross-encoder reranker — score pairs, re-sort — with a transparent scoring
  function where production uses a learned one.
- ``hybrid_search`` — the assembled two-stage pipeline: expand -> search each
  variant -> RRF-fuse -> coverage-rerank -> top k.

Stdlib-only, **for learning, not production** — bridge to BM25+dense hybrid
with RRF (built into Qdrant/Weaviate/pgvector recipes), cross-encoder
rerankers (Cohere Rerank, bge-reranker), and LLM query rewriting.
"""

from __future__ import annotations

from .search import Hit, TfidfIndex, tokenize

_VOWELS = set("aeiou")


def fold(token: str) -> str:
    """Crudely normalize a token toward its stem: strip one plural/tense
    suffix (s/ed/ing), collapse a doubled final consonant, drop a trailing e.
    cards->card, shipping->ship, exchanged/exchange->exchang, appears->appear."""
    t = token
    if len(t) > 5 and t.endswith("ing"):
        t = t[:-3]
    elif len(t) > 4 and t.endswith("ed"):
        t = t[:-2]
    elif len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        t = t[:-1]
    if len(t) > 3 and t[-1] == t[-2] and t[-1] not in _VOWELS:
        t = t[:-1]
    if len(t) > 3 and t.endswith("e"):
        t = t[:-1]
    return t


def fold_tokenize(text: str) -> list[str]:
    """``tokenize`` with folding — drop-in for ``TfidfIndex(tokenizer=...)``."""
    return [fold(t) for t in tokenize(text)]


def expand_query(query: str, synonyms: dict[str, str] | None = None) -> list[str]:
    """The original query plus one variant per matching phrase-map entry.
    The map is hand-authored here; production asks an LLM for paraphrases
    (multi-query) or a hypothetical answer to embed (HyDE) — same fusion
    mechanism downstream, smarter variant generator."""
    variants = [query]
    low = query.lower()
    for phrase, replacement in (synonyms or {}).items():
        if phrase in low:
            variants.append(low.replace(phrase, replacement))
    return variants


def rrf_fuse(rankings: list[list[Hit]], k: int = 60) -> list[Hit]:
    """Reciprocal Rank Fusion: each list votes 1/(k + rank) for its documents;
    sum the votes. Rank-based, so it never has to compare a cosine score with
    a BM25 score — which is exactly why hybrid search uses it. Returns fused
    Hits (score = RRF score), deterministic tie-break by document index."""
    scores: dict[int, float] = {}
    docs: dict[int, str] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            scores[hit.index] = scores.get(hit.index, 0.0) + 1.0 / (k + rank)
            docs.setdefault(hit.index, hit.doc)
    fused = [Hit(i, s, docs[i]) for i, s in scores.items()]
    fused.sort(key=lambda h: (-h.score, h.index))
    return fused


# The second stage can afford linguistics the first stage skipped: a tiny
# stopword list keeps "the"/"is"/"can" from counting as coverage. Classic IR;
# production rerankers learn this weighting instead of hard-coding it.
STOPWORDS = frozenset(
    "a an and are can do does for get how i in is it my of on or our than that "
    "the to until we what when where you your".split()
)


def _informative(text: str) -> set[str]:
    return {t for t in fold_tokenize(text) if t not in STOPWORDS}


def coverage_score(query: str, doc: str) -> float:
    """Second-stage pair score: the fraction of the query's informative folded
    terms that appear in the document (folded). Reads the *pair*, not the
    corpus — no IDF, no length normalization — so a document that covers 3 of
    4 query terms beats one that repeats a single term five times."""
    q_terms = _informative(query)
    if not q_terms:
        return 0.0
    d_terms = set(fold_tokenize(doc))
    return len(q_terms & d_terms) / len(q_terms)


def coverage_rerank(query: str, hits: list[Hit]) -> list[Hit]:
    """Re-score the candidates by coverage and re-sort (first-stage score as
    tie-break via stable sort). Same shape as a cross-encoder reranker: take
    the cheap stage's candidates, pay a closer look per pair, return a better
    ordering. Never run a reranker over the whole corpus — only over the
    candidates the cheap stage already found."""
    rescored = [Hit(h.index, coverage_score(query, h.doc), h.doc) for h in hits]
    rescored.sort(key=lambda h: -h.score)
    return rescored


def hybrid_search(index: TfidfIndex, query: str,
                  synonyms: dict[str, str] | None = None,
                  k: int = 5, pool: int = 8,
                  min_coverage: float = 0.0) -> list[Hit]:
    """The assembled upgrade: expand the query, search every variant, fuse the
    rankings with RRF, rerank the fused pool by the *best* coverage across
    variants (a doc that fully covers one phrasing of the question shouldn't
    be punished for the phrasing it didn't match), keep the top k above
    ``min_coverage`` — the abstain floor, now in units a human can read:
    "the doc must cover at least this fraction of the question"."""
    variants = expand_query(query, synonyms)
    rankings = [index.search(v, k=pool) for v in variants]
    fused = rrf_fuse(rankings)[:pool]
    rescored = [Hit(h.index, max(coverage_score(v, h.doc) for v in variants), h.doc)
                for h in fused]
    rescored.sort(key=lambda h: -h.score)
    return [h for h in rescored[:k] if h.score >= min_coverage]
