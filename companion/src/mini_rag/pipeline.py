"""The RAG pipeline — retrieve, assemble, ground, answer.

RAG is not a model; it's a pipeline you own: retrieve chunks (Ch 2) cut by your
chunker (Ch 3), assemble the survivors into a context, wrap them in a grounded
prompt (Ch 1's spec, applied), and hand that to a generator. Every stage is a
place to fail, so every stage here returns its intermediate state — the
``RagTrace`` keeps what was retrieved, what fit the budget, what got excluded,
the exact prompt, and the answer with its citation.

The generator is deliberately **extractive**: it builds a TF-IDF index over the
*sentences* of the assembled context and quotes the best-matching one, with its
chunk citation — retrieval again, one level down. That makes it faithful **by
construction**: it cannot say anything the context doesn't. A real LLM can —
it will happily synthesize, paraphrase, and fabricate — which is exactly why
grounded prompts carry "answer ONLY from the context" rules and why
faithfulness is measured rather than assumed (Ch 5).

Stdlib-only, **for learning, not production** — bridge to LangChain / LlamaIndex
pipelines and to real generation with structured grounding instructions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .chunk import split_sentences
from .search import Hit, TfidfIndex

ABSTAIN = "I don't know — the retrieved context doesn't answer this."


@dataclass(frozen=True)
class Answer:
    """The generator's output: the quoted sentence (or the abstain message),
    whether it found support, which included-chunk it came from (0-based rank
    in the assembled context; -1 when abstaining), and its match score."""

    text: str
    supported: bool
    source_chunk: int
    score: float


@dataclass(frozen=True)
class RagTrace:
    """Every intermediate of one pipeline run — the debugging surface. When a
    RAG answer is wrong, the trace tells you *which stage* to blame: empty
    ``hits`` = retrieval failure; the needed chunk in ``excluded`` = context-
    window failure; everything present but the answer wrong = generation."""

    question: str
    hits: list[Hit]
    included: list[Hit]
    excluded: list[Hit]
    prompt: str
    answer: Answer


def assemble_context(hits: list[Hit], budget_words: int) -> tuple[list[Hit], list[Hit]]:
    """Greedily include hits in rank order while they fit the word budget;
    the rest are excluded. This is the context-window decision made visible:
    rank #4 being excluded is how a retrieved fact still never reaches the
    model. Returns (included, excluded)."""
    included: list[Hit] = []
    excluded: list[Hit] = []
    used = 0
    for h in hits:
        n = len(h.doc.split())
        if used + n <= budget_words:
            included.append(h)
            used += n
        else:
            excluded.append(h)
    return included, excluded


def build_prompt(question: str, context_chunks: list[str]) -> str:
    """The grounded prompt — Chapter 1's spec applied to RAG: role, the
    answer-ONLY-from-context rule, the missing-context rule, numbered chunks
    for citation, and an output format. Each clause removes a degree of
    freedom the generator would otherwise improvise."""
    numbered = "\n".join(f"[{i + 1}] {c}" for i, c in enumerate(context_chunks))
    return (
        "You are a support assistant. Answer ONLY from the numbered context "
        "chunks below; if the answer isn't there, say \"I don't know\". "
        "Cite the chunk you used, like [2].\n\n"
        f"Context:\n{numbered if numbered else '(no chunks retrieved)'}\n\n"
        f"Question: {question}\n\n"
        "Answer (one or two sentences, with citation):"
    )


def extractive_answer(question: str, context_chunks: list[str],
                      threshold: float = 0.05) -> Answer:
    """A no-model generator: index the context's *sentences*, retrieve the one
    that best matches the question, and quote it with its chunk citation.
    Abstains when nothing scores above ``threshold`` — the missing-context
    rule as code, not as a hope."""
    sentences: list[tuple[int, str]] = []
    for ci, chunk in enumerate(context_chunks):
        for s in split_sentences(chunk):
            sentences.append((ci, s))
    if not sentences:
        return Answer(ABSTAIN, False, -1, 0.0)

    hits = TfidfIndex([s for _, s in sentences]).search(question, k=1)
    if not hits or hits[0].score < threshold:
        return Answer(ABSTAIN, False, -1, hits[0].score if hits else 0.0)
    chunk_idx, sentence = sentences[hits[0].index]
    return Answer(sentence, True, chunk_idx, hits[0].score)


class RagPipeline:
    """Retrieve -> assemble -> ground -> answer over a chunked corpus, keeping
    the full trace. ``k`` bounds retrieval; ``budget_words`` bounds assembly;
    ``min_score`` is the similarity floor — shared stopwords give junk chunks
    real nonzero scores, and without a floor the pipeline will confidently
    build a context out of them. Production systems calibrate this floor
    against a golden set; it is a measured choice, not a default."""

    def __init__(self, chunks: list[str], k: int = 4, budget_words: int = 120,
                 min_score: float = 0.0) -> None:
        self.chunks = list(chunks)
        self.index = TfidfIndex(self.chunks)
        self.k = k
        self.budget_words = budget_words
        self.min_score = min_score

    def run(self, question: str) -> RagTrace:
        hits = [h for h in self.index.search(question, k=self.k)
                if h.score >= self.min_score]
        included, excluded = assemble_context(hits, self.budget_words)
        context = [h.doc for h in included]
        prompt = build_prompt(question, context)
        answer = extractive_answer(question, context)
        return RagTrace(question, hits, included, excluded, prompt, answer)
