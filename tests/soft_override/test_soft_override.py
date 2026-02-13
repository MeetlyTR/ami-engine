# AMI-ENGINE Phase 4.5 — Soft Override birim testleri (07_PHASE_45)

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.soft_override import compute_escalation_level, restrict_action_space
from core.moral_evaluator import MoralScores


def test_escalation_level_2_low_confidence():
    level = compute_escalation_level(0.15, 0.1, 0.3, 0.6, config=None)
    assert level == 2


def test_escalation_level_2_high_harm():
    level = compute_escalation_level(0.8, 0.2, 0.7, 0.6, config=None)
    assert level == 2


def test_escalation_level_1_negative_margin():
    level = compute_escalation_level(0.5, -0.2, 0.2, 0.6, config=None)
    assert level == 1


def test_escalation_level_0_normal():
    level = compute_escalation_level(0.8, 0.2, 0.2, 0.6, config=None)
    assert level == 0


def test_restrict_action_space_filters():
    candidates = [
        ([0.7, 0.5, 0.3, 0.5], MoralScores(W=0.5, J=0.8, H=0.1, C=0.5)),
        ([0.5, 0.5, 0.4, 0.5], MoralScores(W=0.5, J=0.8, H=0.1, C=0.5)),
        ([0.0, 0.0, 0.0, 1.0], MoralScores(W=0.5, J=0.8, H=0.0, C=0.5)),
    ]
    restricted = restrict_action_space(candidates, severity_max=0.6, intervention_max=0.5, delay_min=0.3)
    assert len(restricted) == 2
    actions = [a for a, _ in restricted]
    assert [0.7, 0.5, 0.3, 0.5] not in actions
    assert [0.0, 0.0, 0.0, 1.0] in actions


def test_restrict_action_space_delay_min():
    candidates = [
        ([0.0, 0.5, 0.0, 0.2], MoralScores(W=0.5, J=0.8, H=0.0, C=0.5)),
        ([0.0, 0.0, 0.0, 1.0], MoralScores(W=0.5, J=0.8, H=0.0, C=0.5)),
    ]
    restricted = restrict_action_space(candidates, severity_max=0.6, intervention_max=0.5, delay_min=0.3)
    assert len(restricted) == 1
    assert restricted[0][0] == [0.0, 0.0, 0.0, 1.0]
