# AMI-ENGINE — B.6 Moral Drift Simulation (Phase 4.1)
# Aynı state tekrarda aynı karar (replay); parametre değişmeden drift yok.

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine import moral_decision_engine, replay
from tests.adversarial.base import AdversarialTestCase


def generate_moral_drift_states() -> List[Dict[str, Any]]:
    """Sabit state'ler; replay ile aynı çıktı beklenir."""
    return [
        {"physical": 0.5, "social": 0.5, "context": 0.5, "risk": 0.5,
         "compassion": 0.6, "justice": 0.9, "harm_sens": 0.5,
         "responsibility": 0.5, "empathy": 0.6},
        {"physical": 0.2, "social": 0.8, "context": 0.6, "risk": 0.3,
         "compassion": 0.7, "justice": 0.88, "harm_sens": 0.4,
         "responsibility": 0.6, "empathy": 0.7},
    ]


def expected_behavior_moral_drift(result: Dict[str, Any], raw_state: Dict[str, Any]) -> None:
    """Replay aynı action ve aynı trace hash üretmeli."""
    replayed = replay(result["trace"], validate=True, verify_hash=True, validate_ethics=True)
    assert replayed["action"] == result["action"]
    assert replayed.get("trace_hash") == result.get("trace_hash")


class MoralDriftTest(AdversarialTestCase):
    def generate_states(self) -> List[Dict[str, Any]]:
        return generate_moral_drift_states()

    def expected_behavior(self, result: Dict[str, Any], raw_state: Dict[str, Any]) -> None:
        expected_behavior_moral_drift(result, raw_state)


def test_moral_drift_batch():
    for raw_state in generate_moral_drift_states():
        result = moral_decision_engine(raw_state)
        expected_behavior_moral_drift(result, raw_state)
    print("moral_drift_simulation: batch geçti.")


if __name__ == "__main__":
    test_moral_drift_batch()
