# Veri incelemesi: Dashboard senaryolarindan uretilen trace'ler dogru mu?
# Calistir: python tests/inspect_dashboard_data.py

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STATE_PROFILES = ["balanced", "safe", "critical", "chaos", "easy", "medium", "hard"]
CONFIG_PROFILES = ["", "scenario_test", "clamp_test", "production_safe"]


def run_demo(n: int, profile: str, config_profile: str, seed: int) -> list:
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


def inspect_traces(traces: list, scenario_name: str) -> dict:
    """Trace listesinden ozet ve tutarlilik kontrolu."""
    n = len(traces)
    if not n:
        return {"ok": False, "error": "bos liste"}
    issues = []
    # Level dagilimi
    l0 = sum(1 for t in traces if t.get("level") == 0)
    l1 = sum(1 for t in traces if t.get("level") == 1)
    l2 = sum(1 for t in traces if t.get("level") == 2)
    if l0 + l1 + l2 != n:
        issues.append("level_toplam_uyusmuyor")
    # CUS [0,1]
    cus_vals = []
    for t in traces:
        c = t.get("cus")
        if c is None:
            issues.append("cus_yok")
            break
        if not (0 <= c <= 1):
            issues.append(f"cus_disiarda_{c}")
        cus_vals.append(float(c))
    mean_cus = sum(cus_vals) / len(cus_vals) if cus_vals else None
    # raw vs final
    for t in traces:
        raw = t.get("raw_action") or []
        final = t.get("final_action") or t.get("raw_action") or []
        if len(raw) < 4 or len(final) < 4:
            issues.append("action_4_eleman_degil")
            break
        raw = list(raw)[:4]
        final = list(final)[:4]
        for v in raw + final:
            if not (0 <= v <= 1):
                issues.append("action_elemani_01_disiarda")
                break
    # soft_clamp: true ise raw != final olabilir; false ise genelde ayni
    clamp_count = sum(1 for t in traces if t.get("soft_clamp"))
    # J, H varsa [0,1]
    for t in traces:
        if "J" in t and (t["J"] < 0 or t["J"] > 1):
            issues.append("J_01_disiarda")
            break
        if "H" in t and (t["H"] < 0 or t["H"] > 1):
            issues.append("H_01_disiarda")
            break
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "n": n,
        "L0": l0, "L1": l1, "L2": l2,
        "mean_cus": round(mean_cus, 4) if mean_cus is not None else None,
        "clamp_count": clamp_count,
        "clamp_pct": round(100 * clamp_count / n, 1) if n else 0,
    }


def main():
    seed = 42
    steps = 15
    print("Veri incelemesi: her (state_profil x config) icin trace ozeti ve tutarlilik.")
    print("=" * 70)
    all_ok = True
    results = []
    for state_prof in STATE_PROFILES:
        for config_prof in CONFIG_PROFILES:
            config_label = config_prof or "varsayilan"
            name = f"{state_prof} x {config_label}"
            traces = run_demo(steps, state_prof, config_prof, seed=seed)
            r = inspect_traces(traces, name)
            r["scenario"] = name
            results.append(r)
            if not r["ok"]:
                all_ok = False
            status = "OK" if r["ok"] else "HATA"
            L0, L1, L2 = r["L0"], r["L1"], r["L2"]
            cus = r["mean_cus"] if r["mean_cus"] is not None else "-"
            clamp = r["clamp_pct"]
            issues = f"  [{', '.join(r['issues'])}]" if r["issues"] else ""
            print(f"  {name:45} {status:4}  L0={L0:2} L1={L1:2} L2={L2:2}  CUS={cus}  clamp%={clamp}{issues}")
    print("=" * 70)
    if all_ok:
        print("Sonuc: Tum veriler tutarli (level, cus, action araliklari, J/H varsa [0,1]).")
    else:
        print("Sonuc: Bazı senaryolarda tutarsizlik var (yukarida HATA ve issues).")
    # Beklenti kontrolu: varsayilan config ile cogunlukla L2; scenario_test ile L0/L1 de olmali
    varsayilan_l2 = [r for r in results if "varsayilan" in r["scenario"] and r["L2"] == r["n"]]
    scenario_test_degisik = [r for r in results if "scenario_test" in r["scenario"] and (r["L0"] + r["L1"]) > 0]
    print("")
    print("Beklenti kontrolu:")
    print(f"  - Varsayilan config ile tumu L2: {len(varsayilan_l2)}/7 senaryo (beklenen: 7, guvenli tasarim).")
    print(f"  - scenario_test ile en az bir L0/L1: {len(scenario_test_degisik)}/7 senaryo (beklenen: 7).")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
