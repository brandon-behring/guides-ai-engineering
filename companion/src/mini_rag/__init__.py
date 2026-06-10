"""mini_rag — the build-your-own retrieval companion for the LLM App Engineering guide.

Deliberately minimal, stdlib-only, **for learning, not production**. You build it
chapter-by-chapter to see the mechanism behind RAG, then bridge to scikit-learn /
FAISS / a managed vector DB and RAGAS. Module map:

- ``mini_rag.search``   — TF-IDF vectors + cosine similarity + top-k retrieval (Ch 2).
- ``mini_rag.chunk``    — fixed / sentence / paragraph chunking + boundary_coherence (Ch 3).
- ``mini_rag.pipeline`` — retrieve -> assemble -> grounded prompt -> extractive answer,
  with a full per-stage trace (Ch 4).

More modules land as the guide grows (reranking). Retrieval *quality* is graded
separately in ``mini_eval.retrieval`` from the Evaluation guide: mini_rag is the
mechanism, mini_eval is the measurement.
"""

from .search import (
    tokenize,
    idf,
    tfidf_vector,
    cosine_similarity,
    Hit,
    TfidfIndex,
    top_k,
)
from .chunk import (
    split_sentences,
    chunk_fixed,
    chunk_sentences,
    chunk_paragraphs,
    boundary_coherence,
)
from .pipeline import (
    ABSTAIN,
    Answer,
    RagTrace,
    assemble_context,
    build_prompt,
    extractive_answer,
    RagPipeline,
)

__all__ = [
    "tokenize",
    "idf",
    "tfidf_vector",
    "cosine_similarity",
    "Hit",
    "TfidfIndex",
    "top_k",
    "split_sentences",
    "chunk_fixed",
    "chunk_sentences",
    "chunk_paragraphs",
    "boundary_coherence",
    "ABSTAIN",
    "Answer",
    "RagTrace",
    "assemble_context",
    "build_prompt",
    "extractive_answer",
    "RagPipeline",
]

__version__ = "0.1.0"
