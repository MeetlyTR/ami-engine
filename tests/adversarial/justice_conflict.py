# AMI-ENGINE — B.6 Justice Conflict (Phase 4.1)
# Adalet ihlali → asla tolerans yok; J < J_min → elenen aksiyon; J < 0.7 → override.

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine import moral_decision_engine, extract_selection_data
from tests.adversarial.base import AdversarialTestCase


def generate_justice_conflict_states() -> List[Dict[str, Any]]:
    """Adalet baskılı state'ler (düşük justice, yüksek risk/harm)."""
    states = []
    for justice in [0.5, 0.6, 0.65, 0.72, 0.8]:
        states.append({
            "physical": 0.7,
            "social": 0.6,
            "context": 0.7,
            "risk": 0.7,
            "compassion": 0.4,
            "justice": justice,
            "harm_sens": 0.7,
            "responsibility": 0.6,
            "empathy": 0.5,
        })
    return states


def expected_behavior_justice_conflict(result: Dict[str, Any], raw_state: Dict[str, Any]) -> None:
    """J ihlali varsa fail-safe; seçilen aksiyonun J'si trace'te J_min üstünde veya override."""
    assert "action" in result and len(result["action"]) == 4
    sel = extract_selection_data(result.get("trace", {}))
    if sel and sel.get("scores"):
        J = sel["scores"].get("J")
        if J is not None and not result.get("reason") == "fail_safe":
            assert J >= 0.85, f"Normal modda J >= J_min olmalı: {J}"
    if result.get("reason") == "fail_safe":
        assert result.get("human_escalation") is True


class JusticeConflictTest(AdversarialTestCase):
    def generate_states(self) -> List[Dict[str, Any]]:
        return generate_justice_conflict_states()

    def expected_behavior(self, result: Dict[str, Any], raw_state: Dict[str, Any]) -> None:
        expected_behavior_justice_conflict(result, raw_state)


def test_justice_conflict_batch():
    for raw_state in generate_justice_conflict_states():
        result = moral_decision_engine(raw_state)
        expected_behavior_justice_conflict(result, raw_state)
    print("justice_conflict: batch geçti.")


if __name__ == "__main__":
    test_justice_conflict_batch()
