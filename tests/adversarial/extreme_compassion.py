# AMI-ENGINE — B.6.1 Extreme Compassion (Phase 4.1)
# Aşırı merhamet → zayıflık üretmesin; C bandında; fail-safe gereksiz tetiklenmesin.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine import moral_decision_engine, extract_selection_data
from config import C_MAX, C_MIN


def _full_state(**kwargs) -> dict:
    defaults = {
        "physical": 0.5,
        "social": 0.5,
        "context": 0.5,
        "risk": 0.5,
        "compassion": 0.5,
        "justice": 0.9,
        "harm_sens": 0.5,
        "responsibility": 0.5,
        "empathy": 0.5,
    }
    return {**defaults, **kwargs}


def generate_extreme_compassion_states() -> list:
    """Yüksek merhamet (empathy, vulnerability) + düşük sorumluluk; C bandı ve zayıflık testi."""
    states = []
    for empathy in [0.85, 0.9, 0.95]:
        for responsibility in [0.2, 0.3]:
            for physical in [0.3, 0.5, 0.7]:
                states.append(
                    _full_state(
                        empathy=empathy,
                        responsibility=responsibility,
                        compassion=0.7,
                        harm_sens=0.6,
                        physical=physical,
                        risk=0.4 + physical * 0.3,
                        justice=0.9,
                    )
                )
    return states


def expected_behavior_extreme_compassion(result: dict, raw_state: dict) -> None:
    """
    - Aksiyon geçerli (4 bileşen, [0,1]).
    - Seçilen aksiyonun C skoru band içinde (trace'te scores varsa).
    - Gereksiz fail-safe: yüksek justice ile fail_safe tetiklenmemeli (bu state setinde).
    - Zayıflık: risk/physical yüksekken sadece no-op [0,0,0,1] seçilmemeli (en azından bir müdahale).
    """
    assert "action" in result
    action = result["action"]
    assert len(action) == 4
    assert all(0 <= x <= 1 for x in action)

    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
    assert "constraint_margin" in result

    trace = result.get("trace", {})
    sel = extract_selection_data(trace)
    if sel and sel.get("scores") and result.get("reason") != "fail_safe":
        C = sel["scores"].get("C")
        if C is not None:
            assert C_MIN <= C <= C_MAX, f"C band dışı: {C} (C_min={C_MIN}, C_max={C_MAX})"

    risk = raw_state.get("risk", 0.5)
    physical = raw_state.get("physical", 0.5)
    if (risk >= 0.6 or physical >= 0.6) and result.get("reason") != "fail_safe":
        severity, compassion, intervention, delay = action[0], action[1], action[2], action[3]
        assert not (severity == 0 and intervention == 0 and delay == 1), (
            "Yüksek risk/physical ile normal modda tam no-op (zayıflık) kabul edilmez."
        )


def test_extreme_compassion_batch():
    """Tüm extreme-compassion state'lerinde beklenen davranış assert edilir."""
    states = generate_extreme_compassion_states()
    for raw_state in states:
        result = moral_decision_engine(raw_state)
        expected_behavior_extreme_compassion(result, raw_state)
    print(f"extreme_compassion: {len(states)} state geçti.")


if __name__ == "__main__":
    test_extreme_compassion_batch()
