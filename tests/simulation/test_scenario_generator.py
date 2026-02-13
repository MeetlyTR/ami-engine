# Phase 6.2 — Scenario generator: profiller farklı dağılım üretmeli

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from simulation.scenario_generator import (
    generate_state,
    generate_batch,
    generate_curriculum_batch,
    PROFILE_BOUNDS,
    CURRICULUM_ORDER,
)


def test_safe_has_higher_justice_than_critical():
    """Safe profili ortalama justice > critical ortalama justice."""
    safe_states = generate_batch(200, profile="safe", seed=1)
    critical_states = generate_batch(200, profile="critical", seed=1)
    safe_j = sum(s["justice"] for s in safe_states) / len(safe_states)
    crit_j = sum(s["justice"] for s in critical_states) / len(critical_states)
    assert safe_j > crit_j, "safe justice ort. > critical justice ort. beklenir"


def test_critical_has_higher_harm_sens_than_safe():
    """Critical profili ortalama harm_sens > safe ortalama harm_sens."""
    safe_states = generate_batch(200, profile="safe", seed=2)
    critical_states = generate_batch(200, profile="critical", seed=2)
    safe_h = sum(s["harm_sens"] for s in safe_states) / len(safe_states)
    crit_h = sum(s["harm_sens"] for s in critical_states) / len(critical_states)
    assert crit_h > safe_h


def test_curriculum_order():
    assert CURRICULUM_ORDER == ("safe", "balanced", "critical", "chaos")


def test_curriculum_batch_shapes():
    batch = generate_curriculum_batch(n_per_stage=10, seed=3)
    assert len(batch) == 4 * 10
    for s in batch:
        assert "justice" in s and "harm_sens" in s
        assert 0 <= s["justice"] <= 1 and 0 <= s["harm_sens"] <= 1


def test_chaos_is_uniform_like():
    """Chaos profili geniş yayılım (min/max farkı büyük) üretir."""
    states = generate_batch(100, profile="chaos", seed=4)
    justices = [s["justice"] for s in states]
    assert min(justices) < 0.4 and max(justices) > 0.6


def test_scenario_test_profile_produces_l0_l1_l2_mix():
    """
    scenario_test config ile (fail_safe grid tetiklenmez) safe/balanced/chaos
    profilleri L2 dışında L0/L1 de üretmeli; en az bir profilde L2 < %100.
    """
    from engine import moral_decision_engine
    from core.trace_collector import build_decision_trace

    for profile in ("safe", "balanced", "chaos"):
        states = generate_batch(80, profile=profile, seed=123)
        context = {"cus_history": []}
        L0 = L1 = L2 = 0
        for s in states:
            r = moral_decision_engine(s, context=context, config_override="scenario_test")
            entry = build_decision_trace(r)
            lv = entry.get("level", 0)
            if lv == 0:
                L0 += 1
            elif lv == 1:
                L1 += 1
            else:
                L2 += 1
        n = len(states)
        # scenario_test ile safe/balanced/chaos en az birinde L2 < 100%
        assert L2 < n, "scenario_test + %s: L2=100%% (beklenen karisik L0/L1/L2)" % profile
    # Chaos'ta en az birkac L0 cikmali
    states = generate_batch(100, profile="chaos", seed=42)
    context = {"cus_history": []}
    L0 = sum(
        1
        for s in states
        if build_decision_trace(
            moral_decision_engine(s, context=context, config_override="scenario_test")
        ).get("level") == 0
    )
    assert L0 >= 5, "scenario_test + chaos: en az 5 L0 beklenir (L0=%d)" % L0
