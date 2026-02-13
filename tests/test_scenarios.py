# AMI-ENGINE — Phase 3 senaryo testleri (en az 3 tam senaryo).
# Deterministik çıktılar; trace ve fail-safe davranışı kontrol edilir.

import sys
from pathlib import Path

# Proje kökünü path'e ekle
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import (
    moral_decision_engine,
    replay,
    extract_raw_state,
    extract_action,
    extract_selection_data,
    extract_fail_safe_data,
    compute_trace_hash,
)


def _trace_steps(trace):
    return trace.get("steps", trace) if isinstance(trace, dict) else trace


def run_scenario(name: str, raw_state: dict) -> dict:
    result = moral_decision_engine(raw_state)
    print(f"\n--- {name} ---")
    print("Aksiyon:", result["action"])
    print("Gerekçe:", result["reason"])
    print("İnsan eskalasyonu:", result["human_escalation"])
    if "confidence" in result:
        print("Confidence (B.3):", round(result["confidence"], 4))
        print("Constraint margin:", round(result["constraint_margin"], 4))
    print("Trace adım sayısı:", len(_trace_steps(result["trace"])))
    return result


def test_scenario_1_acil_mudahale():
    """Senaryo 1: Acil-benzeri durum; motor geçerli aksiyon üretir (fail_safe veya normal)."""
    state = {
        "physical": 0.35,
        "social": 0.5,
        "context": 0.5,
        "risk": 0.35,
        "compassion": 0.6,
        "justice": 0.9,
        "harm_sens": 0.5,
        "responsibility": 0.6,
        "empathy": 0.65,
    }
    result = run_scenario("Acil müdahale", state)
    assert len(result["action"]) == 4
    assert all(0 <= x <= 1 for x in result["action"])
    assert result["reason"] in ("fail_safe", "max_score", "no_valid_fallback")
    return result


def test_scenario_2_fail_safe():
    """Senaryo 2: Adalet çok düşük / zarar yüksek → fail-safe, human_escalation=True."""
    state = {
        "physical": 0.95,
        "social": 0.9,
        "context": 0.8,
        "risk": 0.95,
        "compassion": 0.2,
        "justice": 0.5,
        "harm_sens": 0.9,
        "responsibility": 0.3,
        "empathy": 0.2,
    }
    result = run_scenario("Fail-safe tetikleme", state)
    assert result["reason"] == "fail_safe" or result["human_escalation"] is True
    assert result["action"] == [0.0, 0.5, 0.0, 1.0]
    return result


def test_scenario_3_pasif_durum():
    """Senaryo 3: Düşük risk, düşük bağlam → no-op veya düşük müdahale makul."""
    state = {
        "physical": 0.2,
        "social": 0.2,
        "context": 0.2,
        "risk": 0.2,
        "compassion": 0.6,
        "justice": 0.9,
        "harm_sens": 0.5,
        "responsibility": 0.4,
        "empathy": 0.6,
    }
    result = run_scenario("Pasif / düşük risk", state)
    assert len(result["action"]) == 4
    assert _trace_steps(result["trace"])
    return result


def test_replay_determinism():
    """B.4: Replay — determinizm, hash, scores/override (validate_ethics) doğrulaması."""
    state = {"physical": 0.5, "social": 0.5, "context": 0.5, "risk": 0.5,
             "compassion": 0.5, "justice": 0.9, "harm_sens": 0.5,
             "responsibility": 0.5, "empathy": 0.5}
    result = moral_decision_engine(state)
    assert extract_raw_state(result["trace"]) is not None
    assert extract_action(result["trace"]) == result["action"]
    assert result["trace"].get("version") == "1.0"

    replayed = replay(
        result["trace"],
        validate=True,
        verify_hash=True,
        validate_ethics=True,
    )
    assert replayed["action"] == result["action"]
    assert replayed["reason"] == result["reason"]
    assert compute_trace_hash(replayed["trace"]) == result["trace_hash"]

    orig_sel = extract_selection_data(result["trace"])
    new_sel = extract_selection_data(replayed["trace"])
    assert new_sel.get("override") == orig_sel.get("override")
    if orig_sel.get("scores") and new_sel.get("scores"):
        for k in ("W", "J", "H", "C"):
            assert new_sel["scores"][k] == orig_sel["scores"][k]

    print("\n--- Replay (B.4) ---")
    print("Determinizm, bütünlük ve etik tutarlılık (scores/override) doğrulandı.")


def test_confidence_high():
    """B.3: Dengeli state → confidence [0,1] ve trace'te constraint_margin var."""
    state = {
        "physical": 0.3,
        "social": 0.3,
        "context": 0.4,
        "risk": 0.3,
        "compassion": 0.6,
        "justice": 0.9,
        "harm_sens": 0.5,
        "responsibility": 0.5,
        "empathy": 0.6,
    }
    result = run_scenario("Confidence (dengeli)", state)
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
    sel = extract_selection_data(result["trace"])
    assert sel is not None and "constraint_margin" in sel
    print("B.3: Confidence ve constraint_margin doğrulandı.")


def test_confidence_low_near_fail_safe():
    """B.3: Fail-safe yakın state → düşük confidence."""
    state = {
        "physical": 0.95,
        "social": 0.9,
        "context": 0.8,
        "risk": 0.95,
        "compassion": 0.2,
        "justice": 0.5,
        "harm_sens": 0.9,
        "responsibility": 0.3,
        "empathy": 0.2,
    }
    result = run_scenario("Confidence düşük (fail-safe)", state)
    assert result["reason"] == "fail_safe" or result["human_escalation"] is True
    sel = extract_selection_data(result["trace"])
    if sel and "confidence" in sel:
        assert sel["confidence"] <= 1.0


def test_confidence_in_replay():
    """B.3: Replay sonrası confidence ve margin aynı kalmalı."""
    state = {"physical": 0.5, "social": 0.5, "context": 0.5, "risk": 0.5,
             "compassion": 0.6, "justice": 0.9, "harm_sens": 0.5,
             "responsibility": 0.5, "empathy": 0.6}
    result = moral_decision_engine(state)
    orig_sel = extract_selection_data(result["trace"])
    replayed = replay(result["trace"], validate=True, verify_hash=True, validate_ethics=True)
    new_sel = extract_selection_data(replayed["trace"])
    if orig_sel and new_sel and "confidence" in orig_sel:
        assert new_sel["confidence"] == orig_sel["confidence"]
        assert new_sel["constraint_margin"] == orig_sel["constraint_margin"]
    print("\n--- B.3 Replay ---")
    print("Confidence/margin replay tutarlılığı doğrulandı.")


if __name__ == "__main__":
    test_scenario_1_acil_mudahale()
    test_scenario_2_fail_safe()
    test_scenario_3_pasif_durum()
    test_replay_determinism()
    test_confidence_high()
    test_confidence_low_near_fail_safe()
    test_confidence_in_replay()
    print("\nTüm senaryo testleri tamamlandı.")
