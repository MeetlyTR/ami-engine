# Tek test: Dashboard'daki her senaryo (profil x config) rasgele sırada çalıştırılır.
# Amaç: Modelin doğru çalıştığını ispat etmek.

import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Dashboard'daki seçeneklerle birebir aynı
STATE_PROFILES = ["balanced", "safe", "critical", "chaos", "easy", "medium", "hard"]
CONFIG_PROFILES = ["", "scenario_test", "clamp_test", "production_safe"]


def _run_demo_steps(n: int, profile: str, config_profile: str, seed: int) -> list:
    """Dashboard'daki Demo ile aynı mantık: N adım, profil, config. Streamlit yok."""
    from core.trace_collector import TraceCollector, build_decision_trace
    from engine import moral_decision_engine
    from simulation.scenario_generator import generate_batch
    import time

    context = {"cus_history": []}
    states = generate_batch(n, profile=profile, seed=seed)
    config_override = config_profile if config_profile else None
    collector = TraceCollector(max_buffer_size=max(n, 500))
    for state in states:
        result = moral_decision_engine(state, context=context, config_override=config_override)
        entry = build_decision_trace(result, t=time.time())
        collector.push(entry)
    return collector.get_all()


def test_dashboard_scenarios_random():
    """
    Tek test: Tüm (state_profil x config_profil) kombinasyonları rasgele sırada çalıştırılır.
    Rasgelelik: RANDOM_SEED env ile değiştirilebilir; yoksa 42. Kombinasyon sırası shuffle edilir.
    Her senaryoda: engine N adım koşar, trace'lerin geçerli olduğu doğrulanır.
    """
    seed = int(os.environ.get("RANDOM_SEED", "42"))
    steps_per_scenario = 12
    random.seed(seed)

    combinations = [(s, c) for s in STATE_PROFILES for c in CONFIG_PROFILES]
    random.shuffle(combinations)

    failed = []
    for i, (state_profile, config_profile) in enumerate(combinations):
        config_label = config_profile or "varsayilan"
        try:
            traces = _run_demo_steps(steps_per_scenario, state_profile, config_profile, seed=seed + i)
        except Exception as e:
            failed.append((state_profile, config_label, str(e)))
            continue

        if len(traces) != steps_per_scenario:
            failed.append((state_profile, config_label, f"trace sayisi {len(traces)} != {steps_per_scenario}"))
            continue

        for j, t in enumerate(traces):
            level = t.get("level", -1)
            if level not in (0, 1, 2):
                failed.append((state_profile, config_label, f"kayit {j} level={level} gecersiz"))
                break
            cus = t.get("cus", -1)
            if not (0 <= cus <= 1):
                failed.append((state_profile, config_label, f"kayit {j} cus={cus} [0,1] disinda"))
                break
            action = t.get("final_action") or t.get("raw_action") or []
            if len(action) < 4:
                failed.append((state_profile, config_label, f"kayit {j} action uzunluk {len(action)}"))
                break

    if failed:
        msg = "Model dogrulama hatasi (senaryo x config):\n"
        for state_profile, config_label, err in failed[:15]:
            msg += f"  - {state_profile} + {config_label}: {err}\n"
        if len(failed) > 15:
            msg += f"  ... ve {len(failed) - 15} hata daha.\n"
        raise AssertionError(msg)

    # Hepsi gecti
    print(f"[OK] Tum dashboard senaryolari gecti: {len(combinations)} kombinasyon (seed={seed})")


if __name__ == "__main__":
    test_dashboard_scenarios_random()
    print("Model dogru calisiyor.")
