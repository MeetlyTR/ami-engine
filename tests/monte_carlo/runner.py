# AMI-ENGINE Phase 4.2 — Monte Carlo runner
# N senaryo çalıştırır; action, override, confidence, scores toplar.

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine import moral_decision_engine, extract_selection_data
from .generator import generate_batch


def _extract_scores(trace: Dict[str, Any]) -> Optional[Dict[str, float]]:
    sel = extract_selection_data(trace)
    return sel.get("scores") if sel else None


def run_monte_carlo(
    n: int,
    seed: Optional[int] = None,
    deterministic_engine: bool = True,
    config_override: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    n rastgele state üretir, her biri için motoru çalıştırır.
    config_override: Phase 4.3 chaos için J_MIN, H_MAX, C_MIN, C_MAX, J_CRITICAL, H_CRITICAL.
    Her kayıt: action, reason, override, human_escalation, confidence, scores (W,J,H,C).
    """
    states = generate_batch(n, seed)
    records = []
    for raw_state in states:
        result = moral_decision_engine(
            raw_state,
            deterministic=deterministic_engine,
            config_override=config_override,
        )
        scores = _extract_scores(result.get("trace", {}))
        rec = {
            "action": result["action"],
            "reason": result["reason"],
            "override": result.get("reason") == "fail_safe",
            "human_escalation": result.get("human_escalation", False),
            "confidence": result.get("confidence"),
            "constraint_margin": result.get("constraint_margin"),
            "confidence_gradient": result.get("confidence_gradient"),
            "W": scores.get("W") if scores else None,
            "J": scores.get("J") if scores else None,
            "H": scores.get("H") if scores else None,
            "C": scores.get("C") if scores else None,
        }
        if "uncertainty" in result:
            rec["uncertainty"] = result["uncertainty"]
        if "escalation" in result:
            rec["escalation"] = result["escalation"]
        if "soft_safe_applied" in result:
            rec["soft_safe_applied"] = result["soft_safe_applied"]
        if "self_regulation" in result:
            rec["delta_confidence"] = result["self_regulation"].get("delta_confidence")
        records.append(rec)
    return records
