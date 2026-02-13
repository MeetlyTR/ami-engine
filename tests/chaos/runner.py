# AMI-ENGINE Phase 4.3 — Chaos runner
# Her config için Monte Carlo batch çalıştırır, invariant doğrular.

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tests.monte_carlo.runner import run_monte_carlo
from tests.chaos.grid import CHAOS_GRID, iter_configs
from tests.chaos.invariants import check_invariants


def run_chaos(
    n_per_config: int = 200,
    seed: int = 42,
    grid: Optional[Dict[str, List[Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Her chaos config için n_per_config senaryo çalıştırır, invariant'ları doğrular.
    Dönen liste: her config için {"config": {...}, "records": [...], "report_summary": {...}, "invariants_ok": True}.
    """
    results = []
    for config in iter_configs(grid):
        records = run_monte_carlo(
            n=n_per_config,
            seed=seed,
            deterministic_engine=True,
            config_override=config,
        )
        check_invariants(records, config)
        override_ratio = sum(1 for r in records if r.get("override")) / len(records) if records else 0
        results.append({
            "config": config,
            "records": records,
            "invariants_ok": True,
            "override_ratio": override_ratio,
            "n": len(records),
        })
    return results


def run_chaos_simple(n_per_config: int = 100, seed: int = 42) -> None:
    """Tüm grid'i çalıştırır; invariant ihlali olursa exception."""
    results = run_chaos(n_per_config=n_per_config, seed=seed)
    print(f"Phase 4.3 Chaos: {len(results)} config geçti, invariants OK.")
    for r in results:
        print(f"  {r['config']} -> override_ratio={r['override_ratio']:.3f}")


if __name__ == "__main__":
    run_chaos_simple(n_per_config=100)
