# AMI-ENGINE Phase 5 — Temporal Drift birim testleri

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.temporal_drift import (
    update_cus_history,
    compute_temporal_drift,
    should_preemptively_escalate,
    DriftResult,
)


def test_update_cus_history():
    h = update_cus_history([0.3, 0.4], 0.5, window_size=10)
    assert h == [0.3, 0.4, 0.5]
    h = update_cus_history([0.1] * 10, 0.9, window_size=10)
    assert len(h) == 10
    assert h[-1] == 0.9


def test_compute_temporal_drift_no_preemptive():
    hist = [0.3, 0.35, 0.38]
    drift = compute_temporal_drift(0.38, hist, delta_threshold=0.15, mean_threshold=0.65)
    assert drift.delta_cus is not None
    assert abs(drift.delta_cus - 0.03) < 0.001
    assert not drift.preemptive_escalation


def test_compute_temporal_drift_delta_spike():
    hist = [0.3, 0.5, 0.7]
    drift = compute_temporal_drift(0.7, hist, delta_threshold=0.15, mean_threshold=0.65)
    assert drift.delta_cus is not None
    assert abs(drift.delta_cus - 0.2) < 0.001
    assert drift.preemptive_escalation is True


def test_compute_temporal_drift_mean_high():
    hist = [0.7, 0.72, 0.68]
    drift = compute_temporal_drift(0.71, hist, delta_threshold=0.15, mean_threshold=0.65)
    assert drift.cus_mean > 0.65
    assert drift.preemptive_escalation is True


def test_should_preemptively_escalate():
    assert should_preemptively_escalate(DriftResult(None, 0.5, False)) is False
    assert should_preemptively_escalate(DriftResult(0.2, 0.6, True)) is True
