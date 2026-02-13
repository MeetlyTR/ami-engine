# AMI-ENGINE Phase 4.4 — Cognitive Uncertainty birim testleri (06_PHASE_44)

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.uncertainty import (
    hesitation_index,
    decision_entropy,
    action_spread,
    combined_uncertainty_score,
    confidence_uncertainty_divergence,
    compute_uncertainty,
    UncertaintyResult,
)


def test_hesitation_index_low():
    hi = hesitation_index(confidence=1.0, constraint_margin=0.5)
    assert 0 <= hi <= 0.1, "confidence=1 -> HI dusuk"


def test_hesitation_index_high():
    hi = hesitation_index(confidence=0.1, constraint_margin=-0.2, k=5.0)
    assert hi >= 0.4, "dusuk confidence + negatif margin -> HI yuksek"


def test_hesitation_index_bounds():
    for c, m in [(0.0, -1.0), (1.0, 1.0), (0.5, 0.0)]:
        hi = hesitation_index(c, m)
        assert 0 <= hi <= 1.0, f"HI [0,1]: c={c}, m={m} → {hi}"


def test_decision_entropy_single_candidate():
    de, de_norm = decision_entropy([0.9])
    assert de == 0.0 and de_norm == 0.0


def test_decision_entropy_equal_scores():
    scores = [0.5, 0.5, 0.5]
    de, de_norm = decision_entropy(scores)
    assert de_norm >= 0.99, "esit skorlar -> DE_norm ~ 1"
    assert abs(de - math.log(3)) < 0.01


def test_decision_entropy_dominant():
    scores = [10.0, 0.0, 0.0]
    de, de_norm = decision_entropy(scores)
    assert de_norm < 0.5, "net lider -> dusuk entropy"


def test_action_spread_high():
    as_raw, as_norm = action_spread([0.9, 0.1], lambda_norm=2.0)
    assert abs(as_raw - 0.8) < 0.001
    assert as_norm > 0.7


def test_action_spread_low():
    as_raw, as_norm = action_spread([0.51, 0.49], lambda_norm=2.0)
    assert abs(as_raw - 0.02) < 0.001
    assert as_norm < 0.1


def test_action_spread_single():
    as_raw, as_norm = action_spread([0.9])
    assert as_raw == 0.0 and as_norm == 0.0


def test_cus_bounds():
    cus = combined_uncertainty_score(0.5, 0.5, 0.5)
    assert 0 <= cus <= 1.0
    cus_high = combined_uncertainty_score(1.0, 1.0, 0.0)
    assert cus_high >= 0.9


def test_divergence_high():
    d = confidence_uncertainty_divergence(confidence=0.9, de_norm=0.8)
    assert abs(d - 0.7) < 0.01


def test_divergence_low():
    d = confidence_uncertainty_divergence(confidence=0.5, de_norm=0.5)
    assert abs(d - 0.0) < 0.01


def test_compute_uncertainty_full():
    u = compute_uncertainty(
        confidence=0.7,
        constraint_margin=0.1,
        candidate_scores=[0.8, 0.6, 0.4],
    )
    assert isinstance(u, UncertaintyResult)
    assert 0 <= u.hi <= 1 and 0 <= u.de_norm <= 1 and 0 <= u.as_norm <= 1
    assert 0 <= u.cus <= 1
    assert u.divergence >= 0
    d = u.to_dict()
    for key in ("hi", "de", "de_norm", "as_", "as_norm", "cus", "divergence"):
        assert key in d


def test_compute_uncertainty_single_candidate():
    u = compute_uncertainty(0.5, 0.0, [0.9])
    assert u.de == 0.0 and u.de_norm == 0.0
    assert u.as_ == 0.0 and u.as_norm == 0.0
