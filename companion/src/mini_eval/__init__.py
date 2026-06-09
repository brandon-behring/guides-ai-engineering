"""mini_eval — the build-your-own evaluation companion for the Evaluation guide.

Deliberately minimal, stdlib-only, **for learning, not production**. You build it
chapter-by-chapter to see the mechanism, then bridge to scikit-learn / RAGAS /
`eval-toolkit`. Module map:

- ``mini_eval.metrics``     — classification metrics + the threshold sweep (Ch 2).
- ``mini_eval.confidence``  — bootstrap CIs + a paired A/B model test (Ch 3).
- ``mini_eval.calibration`` — Brier, reliability curve, expected calibration error (Ch 4).
- ``mini_eval.retrieval``   — ranked-list retrieval metrics for RAG (Ch 9).
- ``mini_eval.agent``       — pass@k over stochastic attempts for agentic tasks (Ch 10).
- ``mini_eval.judge``       — a mock-model LLM-as-judge harness + bias diagnostics (Ch 7).
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
from .confidence import (
    bootstrap_ci,
    paired_diff_ci,
    permutation_test,
)
from .calibration import (
    brier_score,
    reliability_curve,
    expected_calibration_error,
)
from .retrieval import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    hit_at_k,
    dcg_at_k,
    ndcg_at_k,
)
from .agent import (
    pass_at_k,
    mean_pass_at_k,
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
    "bootstrap_ci",
    "paired_diff_ci",
    "permutation_test",
    "brier_score",
    "reliability_curve",
    "expected_calibration_error",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
    "hit_at_k",
    "dcg_at_k",
    "ndcg_at_k",
    "pass_at_k",
    "mean_pass_at_k",
    "Response",
    "PairwiseJudge",
    "position_flip_rate",
    "judge_accuracy",
]

__version__ = "0.1.0"
