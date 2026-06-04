"""mini_eval — the build-your-own evaluation companion for the Evaluation guide.

Deliberately minimal, stdlib-only, **for learning, not production**. You build it
chapter-by-chapter to see the mechanism, then bridge to scikit-learn / RAGAS /
`eval-toolkit`. Module map:

- ``mini_eval.metrics`` — classification metrics + the threshold sweep (Ch 2).
- ``mini_eval.judge``   — a mock-model LLM-as-judge harness + bias diagnostics (Ch 7).
"""

from .metrics import (
    Counts,
    confusion_counts,
    precision,
    recall,
    f1,
    accuracy,
    fpr,
    metrics_at,
    threshold_sweep,
    average_precision,
)
from .judge import (
    Response,
    PairwiseJudge,
    position_flip_rate,
    judge_accuracy,
)

__all__ = [
    "Counts",
    "confusion_counts",
    "precision",
    "recall",
    "f1",
    "accuracy",
    "fpr",
    "metrics_at",
    "threshold_sweep",
    "average_precision",
    "Response",
    "PairwiseJudge",
    "position_flip_rate",
    "judge_accuracy",
]

__version__ = "0.1.0"
