# Phase 6.0 — feedback_metrics, loss, policy_optimizer unit testleri

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from learning.feedback_metrics import compute_metrics, load_traces_from_jsonl
from learning.loss import compute_loss, DEFAULT_WEIGHTS
from learning.policy_optimizer import PARAM_BOUNDS, clamp_param, suggest_candidates


def test_compute_metrics_empty():
    m = compute_metrics([])
    assert m["fail_safe_rate"] == 0.0 and m["mean_cus"] == 0.0 and m["clamp_distortion"] == 0.0 and m.get("non_fail_reward", 0) == 0.0


def test_compute_metrics_basic():
    traces = [
        {"level": 2, "cus": 0.8, "soft_clamp": False, "raw_action": [0.5, 0.5, 0.5, 0.5], "final_action": [0.5, 0.5, 0.5, 0.5]},
        {"level": 0, "cus": 0.2, "soft_clamp": True, "raw_action": [0.6, 0.4, 0.2, 0.6], "final_action": [0.4, 0.3, 0.3, 0.5]},
    ]
    m = compute_metrics(traces)
    assert m["fail_safe_rate"] == 0.5
    assert m["mean_cus"] == 0.5
    assert m["clamp_distortion"] >= 0
    assert "non_fail_reward" in m and 0.4 <= m["non_fail_reward"] <= 0.6  # L0→1, L2→0 → ortalama 0.5


def test_compute_loss():
    metrics = {"fail_safe_rate": 0.5, "mean_cus": 0.5, "clamp_distortion": 0.1, "non_fail_reward": 0.0}
    L = compute_loss(metrics)
    assert abs(L - (1.5 * 0.5 + 1.0 * 0.5 + 0.5 * 0.1)) < 1e-6
    assert L > 0
    # Phase 6.3: non_fail_reward L'yi düşürür
    metrics["non_fail_reward"] = 0.5
    L2 = compute_loss(metrics)
    assert L2 < L


def test_clamp_param():
    assert clamp_param(0.3, "J_MIN") == 0.50
    assert clamp_param(1.0, "J_MIN") == 0.95
    assert clamp_param(0.85, "J_MIN") == 0.85


def test_suggest_candidates():
    current = {"J_MIN": 0.85, "H_MAX": 0.30, "SOFT_CLAMP_ALPHA": 0.6, "SOFT_CLAMP_BETA": 0.5, "SOFT_CLAMP_GAMMA": 0.35, "DELTA_CUS_THRESHOLD": 0.15, "CUS_MEAN_THRESHOLD": 0.65}
    candidates = suggest_candidates(current, num_candidates=3, seed=123)
    assert len(candidates) == 3
    for c in candidates:
        for key, (lo, hi) in PARAM_BOUNDS.items():
            assert key in c
            assert lo <= c[key] <= hi
