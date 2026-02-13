#!/usr/bin/env python
# AMI-ENGINE Phase 4.6 — Chaos-driven threshold tuning.
# Hedef escalation dağılımına (L0 ~70-90%, L1 ~5-25%, L2 ~0.5-3%) en yakın config'i arar.

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config_profiles import get_config
from tests.monte_carlo.runner import run_monte_carlo
from tests.monte_carlo.report import compute_report


def loss_escalation(
    p0: float, p1: float, p2: float,
    t0: float, t1: float, t2: float,
    weight_l2: float = 3.0,
) -> float:
    """L = (p0-t0)^2 + (p1-t1)^2 + weight_l2*(p2-t2)^2. Level 2 sapmasına daha yüksek ceza."""
    return (p0 - t0) ** 2 + (p1 - t1) ** 2 + weight_l2 * (p2 - t2) ** 2


def grid_search(
    profile_name: str,
    mc_n: int,
    seed: int,
    target_l0: float,
    target_l1: float,
    target_l2: float,
    grid_steps: int,
    center_cfg: dict | None = None,
    narrow_radius: float = 0.08,
) -> tuple:
    """
    center_cfg None ise: profile'dan base alır, geniş aralıkta tara.
    center_cfg verilirse: dar aralık (center ± narrow_radius) ile ince grid (adaptive narrowing).
    """
    base = get_config(profile_name) if center_cfg is None else center_cfg

    if center_cfg is None:
        j_min_vals = _linspace(0.50, 0.82, grid_steps)
        h_max_vals = _linspace(0.38, 0.55, grid_steps)
        as_vals = _linspace(0.25, 0.40, grid_steps)
        div_vals = _linspace(0.42, 0.58, grid_steps)
    else:
        j0, h0, a0, d0 = base.get("J_MIN", 0.65), base.get("H_MAX", 0.45), base.get("AS_SOFT_THRESHOLD", 0.32), base.get("DIVERGENCE_HARD_THRESHOLD", 0.50)
        j_min_vals = _linspace(max(0.40, j0 - narrow_radius), min(0.88, j0 + narrow_radius), grid_steps)
        h_max_vals = _linspace(max(0.30, h0 - narrow_radius), min(0.65, h0 + narrow_radius), grid_steps)
        as_vals = _linspace(max(0.18, a0 - 0.06), min(0.48, a0 + 0.06), grid_steps)
        div_vals = _linspace(max(0.35, d0 - 0.06), min(0.65, d0 + 0.06), grid_steps)

    best_loss = float("inf")
    best_cfg = None
    best_report = None
    total = len(j_min_vals) * len(h_max_vals) * len(as_vals) * len(div_vals)
    done = 0

    for j_min in j_min_vals:
        for h_max in h_max_vals:
            for as_t in as_vals:
                for div_t in div_vals:
                    cfg = {
                        **base,
                        "J_MIN": round(j_min, 3),
                        "H_MAX": round(h_max, 3),
                        "AS_SOFT_THRESHOLD": round(as_t, 3),
                        "DIVERGENCE_HARD_THRESHOLD": round(div_t, 3),
                    }
                    records = run_monte_carlo(n=mc_n, seed=seed, config_override=cfg)
                    report = compute_report(records)
                    p0 = report.get("escalation_ratio_0", 0.0)
                    p1 = report.get("escalation_ratio_1", 0.0)
                    p2 = report.get("escalation_ratio_2", 0.0)
                    L = loss_escalation(p0, p1, p2, target_l0, target_l1, target_l2)
                    done += 1
                    if total <= 30 or done % max(1, total // 10) == 0:
                        print("  [%d/%d] L=%.4f  L0=%.2f L1=%.2f L2=%.2f" % (done, total, L, p0, p1, p2))
                    if L < best_loss:
                        best_loss = L
                        best_cfg = cfg
                        best_report = report

    return best_cfg, best_report, best_loss


def _linspace(lo: float, hi: float, steps: int):
    if steps <= 1:
        return [(lo + hi) / 2]
    return [lo + (hi - lo) * i / (steps - 1) for i in range(steps)]


def main():
    ap = argparse.ArgumentParser(description="Phase 4.6 — Escalation target tuning via Monte Carlo.")
    ap.add_argument("--profile", default="production_safe", help="Base profile (base, production_safe, high_critical)")
    ap.add_argument("--mc-n", type=int, default=300, help="Monte Carlo senaryo sayısı per candidate")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--target", nargs=3, type=float, default=[0.80, 0.15, 0.03],
                    metavar=("L0", "L1", "L2"),
                    help="Hedef oranlar: Level0 Level1 Level2 (default: 0.80 0.15 0.03)")
    ap.add_argument("--grid", type=int, default=2,
                    help="Grid adım sayısı per parametre (2 = hızlı, 3+ = daha ince)")
    ap.add_argument("--adaptive", action="store_true",
                    help="Önce kaba grid, sonra en iyi config etrafında dar grid (ince ayar)")
    ap.add_argument("--no-adaptive", action="store_false", dest="adaptive",
                    help="Sadece tek grid (adaptive yok)")
    ap.set_defaults(adaptive=False)
    args = ap.parse_args()

    t0, t1, t2 = args.target[0], args.target[1], args.target[2]
    print("Phase 4.6 — Tune thresholds (profile=%s, mc_n=%d, target L0=%.2f L1=%.2f L2=%.2f)" % (
        args.profile, args.mc_n, t0, t1, t2))
    print("Grid steps per param: %d  adaptive=%s" % (args.grid, args.adaptive))

    print("\n--- Phase 1: Coarse grid ---")
    best_cfg, best_report, best_loss = grid_search(
        args.profile, args.mc_n, args.seed, t0, t1, t2, args.grid,
    )

    if args.adaptive and best_cfg:
        print("\n--- Phase 2: Narrow grid around best ---")
        best_cfg2, best_report2, best_loss2 = grid_search(
            args.profile, args.mc_n, args.seed + 1, t0, t1, t2, grid_steps=3, center_cfg=best_cfg, narrow_radius=0.07,
        )
        if best_loss2 < best_loss:
            best_cfg, best_report, best_loss = best_cfg2, best_report2, best_loss2
            print("  Refined: new best loss=%.4f" % best_loss)

    print("\n" + "=" * 60)
    print("Best config (loss=%.4f):" % best_loss)
    print("=" * 60)
    for k in sorted(best_cfg.keys()):
        print("  %s = %s" % (k, best_cfg[k]))
    ec = best_report.get("escalation_counts", {})
    print("-" * 40)
    print("Observed escalation: L0=%.2f  L1=%.2f  L2=%.2f" % (
        best_report.get("escalation_ratio_0", 0),
        best_report.get("escalation_ratio_1", 0),
        best_report.get("escalation_ratio_2", 0),
    ))
    print("Counts: %s" % ec)
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
