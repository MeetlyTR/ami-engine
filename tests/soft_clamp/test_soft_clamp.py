# AMI-ENGINE Phase 4.6.1 — Adaptive Soft Clamp birim testleri

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.soft_clamp import soft_clamp_action


def test_soft_clamp_cus_zero_unchanged():
    a = [0.8, 0.5, 0.6, 0.2]
    out = soft_clamp_action(a, cus=0.0, alpha=0.6, beta=0.5, gamma=0.35)
    assert out[0] == 0.8 and out[1] == 0.5 and out[2] == 0.6 and out[3] == 0.2


def test_soft_clamp_cus_high_softens():
    a = [1.0, 0.5, 1.0, 0.0]
    out = soft_clamp_action(a, cus=0.9, alpha=0.6, beta=0.5, gamma=0.35)
    assert out[0] < 0.5
    assert out[2] < 0.6
    assert out[3] >= 0.3
    assert out[1] == 0.5


def test_soft_clamp_bounds():
    a = [1.0, 1.0, 1.0, 0.0]
    out = soft_clamp_action(a, cus=1.0, alpha=0.6, beta=0.5, gamma=0.35)
    for x in out:
        assert 0 <= x <= 1.0
