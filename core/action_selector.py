# AMI-ENGINE — Action Selector (Phase 2 spec §1.6)
# Fail-safe varsa onu döndürür; yoksa Score = α*W + β*J - γ*H + δ*C ile argmax.

from dataclasses import dataclass
from typing import List, Tuple

from config import DEFAULT_WEIGHTS, ScoringWeights
from .fail_safe import FailSafeResult
from .moral_evaluator import MoralScores


@dataclass
class SelectionResult:
    action: List[float]
    score: float | None
    reason: str


def _score(s: MoralScores, w: ScoringWeights) -> float:
    return w.alpha * s.W + w.beta * s.J - w.gamma * s.H + w.delta * s.C


def select_action(
    candidates: List[Tuple[List[float], MoralScores]],
    fail_safe_result: FailSafeResult,
    weights: ScoringWeights | None = None,
) -> SelectionResult:
    """Fail-safe override ise safe_action; değilse kısıtları geçen adaylar arasında max skorlu aksiyon."""
    w = weights or DEFAULT_WEIGHTS
    if fail_safe_result.override and fail_safe_result.safe_action is not None:
        return SelectionResult(
            action=fail_safe_result.safe_action,
            score=None,
            reason="fail_safe",
        )
    if not candidates:
        fallback = fail_safe_result.safe_action if fail_safe_result.safe_action else [0.0, 0.5, 0.0, 1.0]
        return SelectionResult(action=fallback, score=None, reason="no_valid_fallback")
    best = max(candidates, key=lambda item: _score(item[1], w))
    return SelectionResult(
        action=best[0],
        score=_score(best[1], w),
        reason="max_score",
    )
