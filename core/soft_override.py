# AMI-ENGINE — Phase 4.5 Soft Override & Safety Envelope (07_PHASE_45)
# 3-level escalation (0 normal, 1 soft-safe, 2 hard fail-safe) + action-space restriction.

from typing import Any, Dict, List, Optional, Tuple

import config as _config
from .moral_evaluator import MoralScores

# Action: [severity, compassion, intervention, delay] (01_STATE_SPACE)
_IDX_SEVERITY = 0
_IDX_INTERVENTION = 2
_IDX_DELAY = 3


def compute_escalation_level(
    confidence: float,
    constraint_margin: float,
    H: float,
    h_crit: float,
    config: Optional[Dict[str, Any]] = None,
    *,
    as_norm: Optional[float] = None,
    divergence: Optional[float] = None,
    previous_escalation: Optional[int] = None,
) -> int:
    """
    Returns 0 (normal), 1 (soft-safe), or 2 (hard fail-safe).
    Optional: AS_norm / divergence thresholds; hysteresis when downgrading.
    """
    co = config or {}
    force = co.get(
        "CONFIDENCE_ESCALATION_FORCE",
        getattr(_config, "CONFIDENCE_ESCALATION_FORCE", 0.20),
    )
    hyst = co.get(
        "ESCALATION_HYSTERESIS",
        getattr(_config, "ESCALATION_HYSTERESIS", 0.02),
    )
    as_threshold = co.get(
        "AS_SOFT_THRESHOLD",
        getattr(_config, "AS_SOFT_THRESHOLD", 0.3),
    )
    div_threshold = co.get(
        "DIVERGENCE_HARD_THRESHOLD",
        getattr(_config, "DIVERGENCE_HARD_THRESHOLD", 0.5),
    )

    # Level 2: force confidence or H critical, or divergence trigger
    if confidence < force or H > h_crit:
        level = 2
    elif divergence is not None and divergence > div_threshold:
        level = 2
    elif constraint_margin < 0:
        level = 1
    elif as_norm is not None and as_norm < as_threshold:
        level = 1
    else:
        level = 0

    # Hysteresis: downgrade only when margin/confidence better by hyst
    if previous_escalation is not None and level < previous_escalation:
        if previous_escalation == 2:
            if level == 1:
                if not (confidence >= force + hyst and H <= h_crit):
                    level = 2
            elif level == 0:
                if not (confidence >= force + hyst and H <= h_crit and constraint_margin >= hyst):
                    level = 2 if confidence < force or H > h_crit else 1
        elif previous_escalation == 1 and level == 0:
            if constraint_margin < hyst:
                level = 1

    return level


def restrict_action_space(
    candidates: List[Tuple[List[float], MoralScores]],
    severity_max: float,
    intervention_max: float,
    delay_min: float,
) -> List[Tuple[List[float], MoralScores]]:
    """
    Fail-soft filter: severity <= max, intervention <= max, delay >= min.
    Action = [severity, compassion, intervention, delay].
    """
    out = []
    for a, s in candidates:
        if (
            a[_IDX_SEVERITY] <= severity_max
            and a[_IDX_INTERVENTION] <= intervention_max
            and a[_IDX_DELAY] >= delay_min
        ):
            out.append((a, s))
    return out
