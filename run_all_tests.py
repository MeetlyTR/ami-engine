#!/usr/bin/env python
# AMI-ENGINE — Tüm test aşamalarını sırayla çalıştırır.
# Kullanım: proje kökünde  python run_all_tests.py

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def stage(name: str, fn):
    print("\n" + "=" * 60)
    print(f"  {name}")
    print("=" * 60)
    try:
        fn()
        print("  OK")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def main():
    ok = 0
    total = 0

    # 1) Engine + Replay
    total += 1
    if stage("1. Engine + Replay (B.4)", lambda: _run_engine_replay()):
        ok += 1

    # 2) Senaryo testleri (Phase 3 + B.4 + B.3)
    total += 1
    if stage("2. Senaryo testleri (test_scenarios.py)", lambda: _run_scenarios()):
        ok += 1

    # 2b) Phase 4.4 Uncertainty
    total += 1
    if stage("2b. Phase 4.4 Uncertainty (test_uncertainty.py)", lambda: _run_uncertainty()):
        ok += 1

    total += 1
    if stage("2c. Phase 4.5 Soft Override (test_soft_override.py)", lambda: _run_soft_override()):
        ok += 1

    total += 1
    if stage("2d. Phase 4.6.1 Soft Clamp (test_soft_clamp.py)", lambda: _run_soft_clamp()):
        ok += 1

    total += 1
    if stage("2e. Phase 5 Temporal Drift (test_temporal_drift.py)", lambda: _run_temporal_drift()):
        ok += 1

    total += 1
    if stage("2f. Phase 4.7.1 Trace Collector (test_trace_collector.py)", lambda: _run_trace_collector()):
        ok += 1

    total += 1
    if stage("2g. Phase 6.0 Learning (test_learning.py)", lambda: _run_learning()):
        ok += 1

    total += 1
    if stage("2h. Phase 6.2 Scenario Generator (test_scenario_generator.py)", lambda: _run_scenario_generator()):
        ok += 1

    # 3) Adversarial
    total += 1
    if stage("3. Adversarial — extreme_compassion", lambda: _run_adversarial_extreme()):
        ok += 1
    total += 1
    if stage("4. Adversarial — justice_conflict", lambda: _run_adversarial_justice()):
        ok += 1
    total += 1
    if stage("5. Adversarial — harm_explosion", lambda: _run_adversarial_harm()):
        ok += 1
    total += 1
    if stage("6. Adversarial — moral_drift", lambda: _run_adversarial_drift()):
        ok += 1

    # 4) Monte Carlo (küçük batch)
    total += 1
    if stage("7. Monte Carlo (n=500)", lambda: _run_monte_carlo()):
        ok += 1

    # 5) Chaos
    total += 1
    if stage("8. Chaos (Phase 4.3)", lambda: _run_chaos()):
        ok += 1

    # 6) Phase 4.6 profile
    total += 1
    if stage("9. Phase 4.6 Config profile (profile name)", lambda: _run_profile()):
        ok += 1

    print("\n" + "=" * 60)
    print(f"  Sonuç: {ok}/{total} aşama geçti")
    print("=" * 60)
    return 0 if ok == total else 1


def _run_engine_replay():
    from engine import moral_decision_engine, replay
    state = {"physical": 0.8, "social": 0.7, "context": 0.6, "risk": 0.75,
             "compassion": 0.6, "justice": 0.9, "harm_sens": 0.7,
             "responsibility": 0.8, "empathy": 0.65}
    result = moral_decision_engine(state)
    replayed = replay(result["trace"], validate=True, verify_hash=True, validate_ethics=True)
    assert replayed["action"] == result["action"]


def _run_scenarios():
    import tests.test_scenarios as ts
    ts.test_scenario_1_acil_mudahale()
    ts.test_scenario_2_fail_safe()
    ts.test_scenario_3_pasif_durum()
    ts.test_replay_determinism()
    ts.test_confidence_high()
    ts.test_confidence_low_near_fail_safe()
    ts.test_confidence_in_replay()


def _run_uncertainty():
    import tests.uncertainty.test_uncertainty as tu
    tu.test_hesitation_index_low()
    tu.test_hesitation_index_high()
    tu.test_hesitation_index_bounds()
    tu.test_decision_entropy_single_candidate()
    tu.test_decision_entropy_equal_scores()
    tu.test_decision_entropy_dominant()
    tu.test_action_spread_high()
    tu.test_action_spread_low()
    tu.test_action_spread_single()
    tu.test_cus_bounds()
    tu.test_divergence_high()
    tu.test_divergence_low()
    tu.test_compute_uncertainty_full()
    tu.test_compute_uncertainty_single_candidate()


def _run_soft_override():
    import tests.soft_override.test_soft_override as tso
    tso.test_escalation_level_2_low_confidence()
    tso.test_escalation_level_2_high_harm()
    tso.test_escalation_level_1_negative_margin()
    tso.test_escalation_level_0_normal()
    tso.test_restrict_action_space_filters()
    tso.test_restrict_action_space_delay_min()


def _run_soft_clamp():
    import tests.soft_clamp.test_soft_clamp as tsc
    tsc.test_soft_clamp_cus_zero_unchanged()
    tsc.test_soft_clamp_cus_high_softens()
    tsc.test_soft_clamp_bounds()


def _run_temporal_drift():
    import tests.temporal_drift.test_temporal_drift as ttd
    ttd.test_update_cus_history()
    ttd.test_compute_temporal_drift_no_preemptive()
    ttd.test_compute_temporal_drift_delta_spike()
    ttd.test_compute_temporal_drift_mean_high()
    ttd.test_should_preemptively_escalate()


def _run_trace_collector():
    import tests.trace_collector.test_trace_collector as ttc
    ttc.test_build_decision_trace_minimal()
    ttc.test_build_decision_trace_full()
    ttc.test_build_decision_trace_default_t()
    ttc.test_trace_collector_ring_buffer()
    ttc.test_trace_collector_get_recent_zero()
    ttc.test_trace_collector_jsonl_append()
    ttc.test_trace_collector_with_engine()


def _run_learning():
    import tests.learning.test_learning as tl
    tl.test_compute_metrics_empty()
    tl.test_compute_metrics_basic()
    tl.test_compute_loss()
    tl.test_clamp_param()
    tl.test_suggest_candidates()


def _run_scenario_generator():
    import tests.simulation.test_scenario_generator as tsg
    tsg.test_safe_has_higher_justice_than_critical()
    tsg.test_critical_has_higher_harm_sens_than_safe()
    tsg.test_curriculum_order()
    tsg.test_curriculum_batch_shapes()
    tsg.test_chaos_is_uniform_like()
    tsg.test_scenario_test_profile_produces_l0_l1_l2_mix()


def _run_adversarial_extreme():
    from tests.adversarial.extreme_compassion import test_extreme_compassion_batch
    test_extreme_compassion_batch()


def _run_adversarial_justice():
    from tests.adversarial.justice_conflict import test_justice_conflict_batch
    test_justice_conflict_batch()


def _run_adversarial_harm():
    from tests.adversarial.harm_explosion import test_harm_explosion_batch
    test_harm_explosion_batch()


def _run_adversarial_drift():
    from tests.adversarial.moral_drift_simulation import test_moral_drift_batch
    test_moral_drift_batch()


def _run_monte_carlo():
    from tests.monte_carlo.runner import run_monte_carlo
    from tests.monte_carlo.report import compute_report, print_report
    records = run_monte_carlo(n=500, seed=42)
    report = compute_report(records)
    print_report(report)


def _run_chaos():
    from tests.chaos.runner import run_chaos
    results = run_chaos(n_per_config=50, seed=42)
    print(f"  {len(results)} config, tüm invariant'lar geçti.")


def _run_profile():
    from engine import moral_decision_engine
    from config_profiles import get_config, list_profiles
    assert "production_safe" in list_profiles()
    c = get_config("production_safe")
    assert c.get("J_MIN") == 0.65
    r = moral_decision_engine(
        {"physical": 0.5, "social": 0.5, "context": 0.5, "risk": 0.5,
         "compassion": 0.6, "justice": 0.9, "harm_sens": 0.3, "responsibility": 0.5, "empathy": 0.5},
        config_override="production_safe",
    )
    assert r.get("escalation") in (0, 1, 2)
    assert "action" in r


if __name__ == "__main__":
    sys.exit(main())
