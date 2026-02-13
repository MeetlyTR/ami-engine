# AMI-ENGINE — Ana karar motoru pipeline (Phase 2 spec §5).
# B.4: Trace raw_state + Replay + regülasyon-grade sertleştirmeler (04_QUALITY_AND_PHASE4_SPEC).

import copy
import hashlib
import json
import random
from typing import Any, Dict, List, Optional, Union

from ami_engine import config as _config
from ami_engine.config import DEFAULT_WEIGHTS

# Import from parent core package (relative import)
# Note: core/ is at repo root, not in ami_engine package
import sys
from pathlib import Path

_core_parent = Path(__file__).resolve().parent.parent.parent / "core"
if str(_core_parent.parent) not in sys.path:
    sys.path.insert(0, str(_core_parent.parent))

from core import (
    encode_state,
    generate_actions,
    evaluate_moral,
    validate_constraints,
    fail_safe,
    select_action,
    TraceLogger,
    MoralScores,
    compute_confidence,
    compute_uncertainty,
)
from core.fail_safe import FailSafeResult
from core.soft_override import compute_escalation_level
from core.soft_clamp import soft_clamp_action
from core.temporal_drift import (
    update_cus_history,
    compute_temporal_drift,
    should_preemptively_escalate,
)

TRACE_VERSION = "1.0"

# Regülasyon-grade: key order + whitespace yok + Unicode stabil (hash tutarlılığı)
def _trace_to_canonical(trace: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bytes:
    return json.dumps(
        trace,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _get_steps(trace: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Trace versioned (dict) veya legacy (list) olsun, steps listesini döndürür."""
    if isinstance(trace, dict) and "steps" in trace:
        return trace["steps"]
    if isinstance(trace, list):
        return trace
    return []


def moral_decision_engine(
    raw_state: Dict[str, Any],
    resolution: List[float] | None = None,
    deterministic: bool = True,
    config_override: Optional[Union[Dict[str, Any], str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Tek adımda etik karar: ham durum → seçilen aksiyon + tam trace + human_escalation.
    config_override: dict (J_MIN, H_MAX, ...) veya profile adı (base, production_safe, high_critical).
    context: opsiyonel; "cus_history" (List[float]) ile Phase 5 temporal drift kullanılır (in-place güncellenir).
    """
    if deterministic:
        random.seed(0)

    if isinstance(config_override, str):
        try:
            from ami_engine.config_profiles import get_config
            config_override = get_config(config_override)
        except Exception:
            config_override = {}
    co = config_override or {}
    j_min = co.get("J_MIN", _config.J_MIN)
    h_max = co.get("H_MAX", _config.H_MAX)
    c_min = co.get("C_MIN", _config.C_MIN)
    c_max = co.get("C_MAX", _config.C_MAX)
    j_crit = co.get("J_CRITICAL", _config.J_CRITICAL)
    h_crit = co.get("H_CRITICAL", _config.H_CRITICAL)

    logger = TraceLogger()

    logger.log(0, "raw_state", copy.deepcopy(raw_state))

    x_t = encode_state(raw_state)
    logger.log(1, "state_encoded", {"x_ext": list(x_t.x_ext), "x_moral": list(x_t.x_moral)})

    A = generate_actions(x_t, resolution)
    logger.log(2, "actions_generated", {"count": len(A), "actions": A})

    scored: List[tuple] = []
    for a in A:
        scores = evaluate_moral(x_t, a)
        scored.append((a, scores))
    logger.log(3, "moral_scores", [{"a": a, "W": s.W, "J": s.J, "H": s.H, "C": s.C} for a, s in scored])

    candidates: List[tuple] = []
    for a, scores in scored:
        cv = validate_constraints(scores, j_min=j_min, h_max=h_max, c_min=c_min, c_max=c_max)
        if cv.valid:
            candidates.append((a, scores))
        logger.log(4, "constraint", {"a": a, "valid": cv.valid, "violations": cv.violations})

    worst_J = min(s.J for _, s in scored)
    worst_H = max(s.H for _, s in scored)
    fs = fail_safe(MoralScores(W=0, J=worst_J, H=worst_H, C=0), j_crit=j_crit, h_crit=h_crit)
    logger.log(5, "fail_safe", {"override": fs.override, "human_escalation": fs.human_escalation})

    candidate_scores = [
        DEFAULT_WEIGHTS.alpha * s.W + DEFAULT_WEIGHTS.beta * s.J
        - DEFAULT_WEIGHTS.gamma * s.H + DEFAULT_WEIGHTS.delta * s.C
        for _, s in candidates
    ]

    sel = select_action(candidates, fs, DEFAULT_WEIGHTS)

    if sel.reason in ("fail_safe", "no_valid_fallback") and fs.safe_action is not None:
        selected_scores = evaluate_moral(x_t, fs.safe_action)
    else:
        selected_scores = next((s for a, s in candidates if a == sel.action), None)

    selection_data = {
        "action": sel.action,
        "reason": sel.reason,
        "score": sel.score,
        "override": fs.override,
    }
    if selected_scores is not None:
        selection_data["scores"] = {
            "W": selected_scores.W,
            "J": selected_scores.J,
            "H": selected_scores.H,
            "C": selected_scores.C,
        }
        conf = compute_confidence(
            selected_scores,
            j_min=j_min,
            h_max=h_max,
            c_min=c_min,
            c_max=c_max,
        )
        selection_data["confidence"] = conf.confidence
        selection_data["constraint_margin"] = conf.constraint_margin
        selection_data["base_confidence"] = conf.base_confidence
        selection_data["margin_factor"] = conf.margin_factor
        selection_data["confidence_gradient"] = conf.confidence_gradient
        selection_data["suggest_escalation"] = conf.suggest_escalation
        selection_data["force_escalation"] = conf.force_escalation
        human_escalation = fs.human_escalation or conf.force_escalation
        uncertainty = compute_uncertainty(
            conf.confidence,
            conf.constraint_margin,
            candidate_scores,
            config=co,
        )
        selection_data["uncertainty"] = uncertainty.to_dict()
    else:
        conf = None
        uncertainty = None
        human_escalation = fs.human_escalation

    if conf is not None:
        escalation = compute_escalation_level(
            conf.confidence,
            conf.constraint_margin,
            worst_H,
            h_crit,
            config=co,
            as_norm=uncertainty.as_norm if uncertainty else None,
            divergence=uncertainty.divergence if uncertainty else None,
        )
    else:
        escalation = 2 if fs.override else 0

    temporal_drift_data: Optional[Dict[str, Any]] = None
    if context is not None and uncertainty is not None:
        window = co.get("CUS_MEAN_WINDOW", _config.CUS_MEAN_WINDOW)
        delta_thresh = co.get("DELTA_CUS_THRESHOLD", _config.DELTA_CUS_THRESHOLD)
        mean_thresh = co.get("CUS_MEAN_THRESHOLD", _config.CUS_MEAN_THRESHOLD)
        hist = context.get("cus_history", [])
        hist = update_cus_history(hist, uncertainty.cus, window)
        context["cus_history"] = hist
        drift = compute_temporal_drift(uncertainty.cus, hist, delta_thresh, mean_thresh)
        temporal_drift_data = {
            "delta_cus": drift.delta_cus,
            "cus_mean": drift.cus_mean,
            "preemptive_escalation": drift.preemptive_escalation,
        }
        if should_preemptively_escalate(drift):
            escalation = max(escalation, 1)

    soft_safe_applied = False
    raw_action = list(sel.action)
    final_action = sel.action
    self_regulation_data: Optional[Dict[str, Any]] = None
    if escalation == 1 and not fs.override and uncertainty is not None:
        confidence_before = conf.confidence
        alpha = co.get("SOFT_CLAMP_ALPHA", _config.SOFT_CLAMP_ALPHA)
        beta = co.get("SOFT_CLAMP_BETA", _config.SOFT_CLAMP_BETA)
        gamma = co.get("SOFT_CLAMP_GAMMA", _config.SOFT_CLAMP_GAMMA)
        clamped = soft_clamp_action(sel.action, uncertainty.cus, alpha, beta, gamma)
        final_action = clamped
        selected_scores = evaluate_moral(x_t, clamped)
        conf = compute_confidence(
            selected_scores,
            j_min=j_min,
            h_max=h_max,
            c_min=c_min,
            c_max=c_max,
        )
        uncertainty = compute_uncertainty(
            conf.confidence,
            conf.constraint_margin,
            candidate_scores,
            config=co,
        )
        human_escalation = False
        delta_confidence = conf.confidence - confidence_before
        self_regulation_data = {"delta_confidence": delta_confidence}
        selection_data = {
            "action": clamped,
            "reason": sel.reason,
            "score": sel.score,
            "override": False,
            "scores": {
                "W": selected_scores.W,
                "J": selected_scores.J,
                "H": selected_scores.H,
                "C": selected_scores.C,
            },
            "confidence": conf.confidence,
            "constraint_margin": conf.constraint_margin,
            "base_confidence": conf.base_confidence,
            "margin_factor": conf.margin_factor,
            "confidence_gradient": conf.confidence_gradient,
            "suggest_escalation": conf.suggest_escalation,
            "force_escalation": conf.force_escalation,
            "uncertainty": uncertainty.to_dict(),
            "self_regulation": self_regulation_data,
        }
        soft_safe_applied = True

    selection_data["escalation"] = escalation
    selection_data["soft_safe_applied"] = soft_safe_applied
    if temporal_drift_data is not None:
        selection_data["temporal_drift"] = temporal_drift_data

    logger.log(6, "selection", selection_data)

    trace_list = [{"step": e.step, "event_type": e.event_type, "data": e.data} for e in logger.trace]
    trace_output: Dict[str, Any] = {"version": TRACE_VERSION, "steps": trace_list}
    out = {
        "action": final_action,
        "raw_action": raw_action,
        "trace": trace_output,
        "human_escalation": human_escalation,
        "reason": sel.reason,
        "trace_hash": compute_trace_hash(trace_output),
    }
    if conf is not None:
        out["confidence"] = conf.confidence
        out["constraint_margin"] = conf.constraint_margin
        out["confidence_gradient"] = conf.confidence_gradient
    if uncertainty is not None:
        out["uncertainty"] = uncertainty.to_dict()
    out["escalation"] = escalation
    out["soft_safe_applied"] = soft_safe_applied
    if temporal_drift_data is not None:
        out["temporal_drift"] = temporal_drift_data
    if self_regulation_data is not None:
        out["self_regulation"] = self_regulation_data
    if selected_scores is not None:
        out["J"] = selected_scores.J
        out["H"] = selected_scores.H
    return out


def extract_raw_state(trace: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any] | None:
    """Trace'ten replay girdisi olan raw_state'i çıkarır (step 0, event_type='raw_state')."""
    steps = _get_steps(trace)
    for event in steps:
        if event.get("step") == 0 and event.get("event_type") == "raw_state":
            return event.get("data")
    return None


def extract_action(trace: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[float] | None:
    """Trace'ten orijinal seçilen aksiyonu çıkarır (step 6, event_type='selection')."""
    steps = _get_steps(trace)
    for event in steps:
        if event.get("step") == 6 and event.get("event_type") == "selection":
            data = event.get("data")
            return data.get("action") if isinstance(data, dict) else None
    return None


def extract_selection_data(trace: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any] | None:
    """Trace'ten step 6 selection data (action, reason, score, scores, override) döndürür."""
    steps = _get_steps(trace)
    for event in steps:
        if event.get("step") == 6 and event.get("event_type") == "selection":
            return event.get("data") if isinstance(event.get("data"), dict) else None
    return None


def extract_fail_safe_data(trace: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any] | None:
    """Trace'ten step 5 fail_safe data (override, human_escalation) döndürür."""
    steps = _get_steps(trace)
    for event in steps:
        if event.get("step") == 5 and event.get("event_type") == "fail_safe":
            return event.get("data") if isinstance(event.get("data"), dict) else None
    return None


def compute_trace_hash(trace: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
    """Trace'in deterministik SHA256 hash'i; sort_keys+separators ile regülasyon-grade."""
    return hashlib.sha256(_trace_to_canonical(trace)).hexdigest()


def replay(
    trace: Union[Dict[str, Any], List[Dict[str, Any]]],
    validate: bool = True,
    verify_hash: bool = False,
    validate_ethics: bool = False,
) -> Dict[str, Any]:
    """
    Kayıtlı trace'ten raw_state alıp motoru tekrar çalıştırır (deterministic=True ile).
    validate=True: yeni action == trace'teki action.
    verify_hash=True: yeni trace hash == orijinal trace hash.
    validate_ethics=True: yeni selection/fail_safe data (scores, override) == orijinal.
    """
    raw_state = extract_raw_state(trace)
    if raw_state is None:
        raise ValueError("Trace'te raw_state yok (step 0, event_type='raw_state' gerekli)")

    result = moral_decision_engine(raw_state, deterministic=True)

    if validate:
        orig_action = extract_action(trace)
        if orig_action is not None:
            new_action = result["action"]
            assert new_action == orig_action, (
                "Replay determinizm ihlali: yeni action trace'teki action ile aynı değil."
            )

    if verify_hash:
        orig_hash = compute_trace_hash(trace)
        new_hash = result.get("trace_hash") or compute_trace_hash(result["trace"])
        assert new_hash == orig_hash, (
            "Replay bütünlük ihlali: yeni trace hash'i orijinal ile aynı değil."
        )

    if validate_ethics:
        orig_sel = extract_selection_data(trace)
        new_sel = extract_selection_data(result["trace"])
        orig_fs = extract_fail_safe_data(trace)
        new_fs = extract_fail_safe_data(result["trace"])
        if orig_sel and new_sel:
            assert new_sel.get("action") == orig_sel.get("action")
            assert new_sel.get("override") == orig_sel.get("override")
            if "scores" in orig_sel and "scores" in new_sel:
                for k in ("W", "J", "H", "C"):
                    assert new_sel["scores"][k] == orig_sel["scores"][k]
            if "confidence" in orig_sel and "confidence" in new_sel:
                assert new_sel["confidence"] == orig_sel["confidence"]
            if "constraint_margin" in orig_sel and "constraint_margin" in new_sel:
                assert new_sel["constraint_margin"] == orig_sel["constraint_margin"]
            if "confidence_gradient" in orig_sel and "confidence_gradient" in new_sel:
                assert new_sel["confidence_gradient"] == orig_sel["confidence_gradient"]
            if "uncertainty" in orig_sel and "uncertainty" in new_sel:
                tol = 1e-9
                for key in ("hi", "de", "de_norm", "as_", "as_norm", "cus", "divergence"):
                    if key in orig_sel["uncertainty"] and key in new_sel["uncertainty"]:
                        assert abs(new_sel["uncertainty"][key] - orig_sel["uncertainty"][key]) <= tol, (
                            f"Replay uncertainty ihlali: {key}"
                        )
            if "escalation" in orig_sel and "escalation" in new_sel:
                assert new_sel["escalation"] == orig_sel["escalation"], "Replay escalation ihlali"
            if "soft_safe_applied" in orig_sel and "soft_safe_applied" in new_sel:
                assert new_sel["soft_safe_applied"] == orig_sel["soft_safe_applied"], "Replay soft_safe_applied ihlali"
        if orig_fs and new_fs:
            assert new_fs.get("override") == orig_fs.get("override")

    return result


if __name__ == "__main__":
    state = {
        "physical": 0.8,
        "social": 0.7,
        "context": 0.6,
        "risk": 0.75,
        "compassion": 0.6,
        "justice": 0.9,
        "harm_sens": 0.7,
        "responsibility": 0.8,
        "empathy": 0.65,
    }
    result = moral_decision_engine(state)
    print("Seçilen aksiyon:", result["action"])
    print("Gerekçe:", result["reason"])
    print("Trace hash:", result["trace_hash"][:16], "...")

    replayed = replay(result["trace"], validate=True, verify_hash=True)
    print("Replay OK — determinizm ve bütünlük doğrulandı.")
    assert replayed["action"] == result["action"]
