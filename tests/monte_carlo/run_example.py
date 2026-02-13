# AMI-ENGINE Phase 4.2 — Örnek çalıştırma (küçük batch)
# 1000 senaryo → rapor (10k–100k için aynı API).
# Çalıştırma: proje kökünden  python -m tests.monte_carlo.run_example

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tests.monte_carlo.runner import run_monte_carlo
from tests.monte_carlo.report import compute_report, print_report


def main():
    n = 1000
    seed = 42
    print(f"Monte Carlo çalıştırılıyor: n={n}, seed={seed}")
    records = run_monte_carlo(n=n, seed=seed, deterministic_engine=True)
    report = compute_report(records)
    print_report(report)


if __name__ == "__main__":
    main()
