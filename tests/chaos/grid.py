# AMI-ENGINE Phase 4.3 — Chaos parametre grid'i
# Her kombinasyon için invariant'lar doğrulanır.

import itertools
from typing import Any, Dict, Iterator, List

# Küçük grid: 2×2×2×2×2×2 = 64 config (hızlı doğrulama)
CHAOS_GRID: Dict[str, List[Any]] = {
    "J_MIN": [0.75, 0.85],
    "H_MAX": [0.25, 0.30],
    "C_MIN": [0.30, 0.35],
    "C_MAX": [0.70, 0.75],
    "J_CRITICAL": [0.65, 0.70],
    "H_CRITICAL": [0.55, 0.60],
}


def iter_configs(grid: Dict[str, List[Any]] | None = None) -> Iterator[Dict[str, Any]]:
    """Grid'deki her parametre kombinasyonunu yield eder."""
    g = grid or CHAOS_GRID
    keys = list(g.keys())
    if not keys:
        yield {}
        return
    values = [g[k] for k in keys]
    for combo in itertools.product(*values):
        yield dict(zip(keys, combo))
