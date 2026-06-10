"""Chunking — deciding what a vector can even represent.

Retrieval ranks *chunks*, not documents, so the chunker decides what a single
vector can possibly say. Cut a policy mid-sentence and no embedding model can
glue it back together: the fact is split across two vectors, and neither one
answers the question. Chunking happens before any embedding is computed —
which is exactly why it's the highest-leverage (and most under-tested) decision
in a RAG pipeline.

Three honest strategies, simplest first:

- ``chunk_fixed``      — every ``size`` words, optional overlap. Uniform and
                         deterministic; blind to sentences, so it splits facts.
- ``chunk_sentences``  — pack whole sentences up to ~``size`` words. Never
                         splits mid-sentence; chunk sizes vary.
- ``chunk_paragraphs`` — pack whole paragraphs (blank-line separated); an
                         oversized paragraph falls back to sentence packing.
                         Structure first, then size.

``boundary_coherence`` measures the difference: the fraction of chunks that end
at sentence-terminal punctuation (1.0 = no mid-sentence cuts anywhere).

Sizes here are in *words* for readability; production chunkers count tokens
(the model's unit). Stdlib-only, **for learning, not production** — bridge to
LangChain's RecursiveCharacterTextSplitter / semantic and document-aware
splitters, which add separator hierarchies, token counting, and format
awareness on top of exactly these moves.
"""

from __future__ import annotations

import re

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_TERMINAL = (".", "!", "?")


def split_sentences(text: str) -> list[str]:
    """Split prose into sentences on terminal punctuation followed by space.
    Deliberately crude (no abbreviation handling — "Dr. Smith" becomes two
    sentences); real splitters carry exception lists for exactly this reason."""
    flat = " ".join(text.split())  # collapse newlines/whitespace first
    return [s.strip() for s in _SENTENCE_END.split(flat) if s.strip()]


def chunk_fixed(text: str, size: int, overlap: int = 0) -> list[str]:
    """Every ``size`` words becomes a chunk; ``overlap`` words repeat at each
    boundary so a fact straddling the cut survives in at least one chunk.
    Stops once a chunk reaches the end of the text — never emits a trailing
    chunk that is pure overlap of the previous one."""
    if size <= 0:
        raise ValueError("size must be positive")
    if not 0 <= overlap < size:
        raise ValueError("overlap must satisfy 0 <= overlap < size")
    words = text.split()
    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(words), step):
        piece = words[start : start + size]
        if piece:
            chunks.append(" ".join(piece))
        if start + size >= len(words):
            break
    return chunks


def _pack(units: list[str], size: int, joiner: str) -> list[str]:
    """Greedy packing: add whole units until the next would exceed ``size``
    words. A single unit longer than ``size`` becomes its own oversized chunk —
    the contract is "never split a unit", not "never exceed size"."""
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for unit in units:
        n = len(unit.split())
        if current and current_words + n > size:
            chunks.append(joiner.join(current))
            current, current_words = [], 0
        current.append(unit)
        current_words += n
    if current:
        chunks.append(joiner.join(current))
    return chunks


def chunk_sentences(text: str, size: int) -> list[str]:
    """Pack whole sentences up to ~``size`` words per chunk. Boundaries always
    fall at sentence ends, so no fact is ever cut mid-sentence; the price is
    uneven chunk sizes (and one long sentence can exceed ``size``)."""
    if size <= 0:
        raise ValueError("size must be positive")
    return _pack(split_sentences(text), size, " ")


def chunk_paragraphs(text: str, size: int) -> list[str]:
    """Pack whole paragraphs (blank-line separated) up to ~``size`` words.
    Paragraphs are the author's own topic boundaries — the cheapest "semantic"
    signal a document carries. A paragraph longer than ``size`` falls back to
    sentence packing within that paragraph: structure first, then size."""
    if size <= 0:
        raise ValueError("size must be positive")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[str] = []
    for p in paragraphs:
        if len(p.split()) > size:
            units.extend(chunk_sentences(p, size))
        else:
            units.append(" ".join(p.split()))
    return _pack(units, size, "\n\n")


def boundary_coherence(chunks: list[str]) -> float:
    """Fraction of chunks ending at sentence-terminal punctuation. 1.0 means no
    chunk ends mid-sentence; fixed-size chunking typically scores far lower —
    this single number is the cheapest smoke test of a chunking config."""
    if not chunks:
        return 0.0
    coherent = sum(1 for c in chunks if c.rstrip().endswith(_TERMINAL))
    return coherent / len(chunks)
