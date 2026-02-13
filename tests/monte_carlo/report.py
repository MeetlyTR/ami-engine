# AMI-ENGINE Phase 4.2 — Monte Carlo raporlama
# mean(J), std(J), override_ratio, confidence/gradient dağılımı, özet tablo.

import math
from typing import Any, Dict, List, Optional, Tuple


def _mean_std(values: List[float]) -> Tuple[float, float]:
    if not values:
        return float("nan"), float("nan")
    n = len(values)
    m = sum(values) / n
    var = sum((x - m) ** 2 for x in values) / n
    return m, math.sqrt(max(0, var))


def _histogram(values: List[float], bins: int = 10, low: float = 0.0, high: float = 1.0) -> List[int]:
    if not values or bins <= 0:
        return []
    counts = [0] * bins
    step = (high - low) / bins
    for v in values:
        if low <= v <= high:
            idx = min(int((v - low) / step), bins - 1)
            counts[idx] += 1
    return counts


def compute_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Toplu kayıtlardan etik istatistik raporu.
    mean(J), std(J), mean(H), std(H), override_ratio, confidence/gradient dağılımı.
    """
    n = len(records)
    override_count = sum(1 for r in records if r.get("override"))
    override_ratio = override_count / n if n else 0.0

    j_vals = [r["J"] for r in records if r.get("J") is not None]
    h_vals = [r["H"] for r in records if r.get("H") is not None]
    w_vals = [r["W"] for r in records if r.get("W") is not None]
    c_vals = [r["C"] for r in records if r.get("C") is not None]

    mean_j, std_j = _mean_std(j_vals)
    mean_h, std_h = _mean_std(h_vals)
    mean_w, std_w = _mean_std(w_vals)
    mean_c, std_c = _mean_std(c_vals)

    conf_vals = [r["confidence"] for r in records if r.get("confidence") is not None]
    mean_conf, std_conf = _mean_std(conf_vals)
    grad_vals = [r["confidence_gradient"] for r in records if r.get("confidence_gradient") is not None]
    mean_grad, std_grad = _mean_std(grad_vals)

    u_records = [r for r in records if r.get("uncertainty")]
    hi_vals = [r["uncertainty"]["hi"] for r in u_records]
    de_norm_vals = [r["uncertainty"]["de_norm"] for r in u_records]
    as_norm_vals = [r["uncertainty"]["as_norm"] for r in u_records]
    cus_vals = [r["uncertainty"]["cus"] for r in u_records]
    div_vals = [r["uncertainty"]["divergence"] for r in u_records]
    mean_hi, std_hi = _mean_std(hi_vals)
    mean_de, std_de = _mean_std(de_norm_vals)
    mean_as, std_as = _mean_std(as_norm_vals)
    mean_cus, std_cus = _mean_std(cus_vals)
    mean_div, std_div = _mean_std(div_vals)

    esc_vals = [r["escalation"] for r in records if r.get("escalation") is not None]
    escalation_counts = {0: 0, 1: 0, 2: 0}
    for e in esc_vals:
        if e in (0, 1, 2):
            escalation_counts[e] = escalation_counts.get(e, 0) + 1
    soft_safe_count = sum(1 for r in records if r.get("soft_safe_applied"))
    delta_conf_vals = [r["delta_confidence"] for r in records if r.get("delta_confidence") is not None]
    mean_dc, std_dc = _mean_std(delta_conf_vals)

    return {
        "n": n,
        "override_count": override_count,
        "override_ratio": override_ratio,
        "J": {"mean": mean_j, "std": std_j, "count": len(j_vals)},
        "H": {"mean": mean_h, "std": std_h, "count": len(h_vals)},
        "W": {"mean": mean_w, "std": std_w, "count": len(w_vals)},
        "C": {"mean": mean_c, "std": std_c, "count": len(c_vals)},
        "confidence": {"mean": mean_conf, "std": std_conf, "count": len(conf_vals)},
        "confidence_gradient": {"mean": mean_grad, "std": std_grad, "count": len(grad_vals)},
        "confidence_histogram": _histogram(conf_vals, bins=10),
        "gradient_histogram": _histogram(grad_vals, bins=10, low=0, high=2.0),
        "uncertainty_count": len(u_records),
        "HI": {"mean": mean_hi, "std": std_hi, "count": len(hi_vals), "histogram": _histogram(hi_vals, bins=10)},
        "DE_norm": {"mean": mean_de, "std": std_de, "count": len(de_norm_vals), "histogram": _histogram(de_norm_vals, bins=10)},
        "AS_norm": {"mean": mean_as, "std": std_as, "count": len(as_norm_vals), "histogram": _histogram(as_norm_vals, bins=10)},
        "CUS": {"mean": mean_cus, "std": std_cus, "count": len(cus_vals), "histogram": _histogram(cus_vals, bins=10)},
        "divergence": {"mean": mean_div, "std": std_div, "count": len(div_vals), "histogram": _histogram(div_vals, bins=10, low=0, high=1.0)},
        "escalation_counts": escalation_counts,
        "escalation_ratio_0": escalation_counts[0] / n if n else 0.0,
        "escalation_ratio_1": escalation_counts[1] / n if n else 0.0,
        "escalation_ratio_2": escalation_counts[2] / n if n else 0.0,
        "soft_safe_applied_count": soft_safe_count,
        "delta_confidence": {"mean": mean_dc, "std": std_dc, "count": len(delta_conf_vals), "histogram": _histogram(delta_conf_vals, bins=10, low=-0.5, high=0.5)},
    }


def print_report(report: Dict[str, Any]) -> None:
    """Raporu konsola yazdırır."""
    print("\n" + "=" * 60)
    print("Phase 4.2 — Monte Carlo Etik İstatistik Raporu")
    print("=" * 60)
    print(f"Toplam senaryo: {report['n']}")
    print(f"Fail-safe (override) oranı: {report['override_ratio']:.4f} ({report['override_count']}/{report['n']})")
    print("-" * 40)
    for key in ("J", "H", "W", "C"):
        r = report[key]
        print(f"  {key}: mean={r['mean']:.4f}, std={r['std']:.4f} (n={r['count']})")
    print("-" * 40)
    print(f"  confidence: mean={report['confidence']['mean']:.4f}, std={report['confidence']['std']:.4f}")
    print(f"  confidence_gradient: mean={report['confidence_gradient']['mean']:.4f}, std={report['confidence_gradient']['std']:.4f}")
    print("-" * 40)
    print("Confidence histogram (10 bin [0,1]):")
    print("  " + str(report["confidence_histogram"]))
    if report.get("uncertainty_count", 0) > 0:
        print("-" * 40)
        print("Phase 4.4 — Uncertainty (n=%d):" % report["uncertainty_count"])
        print("  HI:      mean=%.4f, std=%.4f" % (report["HI"]["mean"], report["HI"]["std"]))
        print("  DE_norm: mean=%.4f, std=%.4f" % (report["DE_norm"]["mean"], report["DE_norm"]["std"]))
        print("  AS_norm: mean=%.4f, std=%.4f" % (report["AS_norm"]["mean"], report["AS_norm"]["std"]))
        print("  CUS:     mean=%.4f, std=%.4f" % (report["CUS"]["mean"], report["CUS"]["std"]))
        print("  divergence: mean=%.4f, std=%.4f" % (report["divergence"]["mean"], report["divergence"]["std"]))
        print("  CUS histogram: " + str(report["CUS"]["histogram"]))
    if "escalation_counts" in report:
        ec = report["escalation_counts"]
        print("-" * 40)
        print("Phase 4.5 — Escalation:")
        print("  Level 0: %d (%.2f%%)" % (ec.get(0, 0), report.get("escalation_ratio_0", 0) * 100))
        print("  Level 1: %d (%.2f%%)" % (ec.get(1, 0), report.get("escalation_ratio_1", 0) * 100))
        print("  Level 2: %d (%.2f%%)" % (ec.get(2, 0), report.get("escalation_ratio_2", 0) * 100))
        print("  soft_safe_applied: %d" % report.get("soft_safe_applied_count", 0))
    if report.get("delta_confidence", {}).get("count", 0) > 0:
        dc = report["delta_confidence"]
        print("-" * 40)
        print("Phase 5.1 — Self-regulation (delta_confidence, n=%d):" % dc["count"])
        print("  mean=%.4f, std=%.4f" % (dc["mean"], dc["std"]))
        print("  histogram: " + str(dc.get("histogram", [])))
    print("=" * 60)
