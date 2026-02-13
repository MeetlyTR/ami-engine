# AMI-ENGINE Phase 4.2 — Monte Carlo state jeneratörü
# U(0,1) veya seçilmiş dağılımla raw_state üretir.

import random
from typing import Dict, Any, List, Optional


STATE_KEYS = [
    "physical",
    "social",
    "context",
    "risk",
    "compassion",
    "justice",
    "harm_sens",
    "responsibility",
    "empathy",
]


def generate_random_state(seed: Optional[int] = None) -> Dict[str, float]:
    """
    Tek bir raw_state üretir; tüm bileşenler [0, 1] uniform.
    seed verilirse tekrarlanabilir.
    """
    if seed is not None:
        random.seed(seed)
    return {k: random.random() for k in STATE_KEYS}


def generate_batch(
    n: int,
    seed: Optional[int] = None,
) -> List[Dict[str, float]]:
    """
    n adet bağımsız raw_state üretir.
    seed verilirse ilk state için kullanılır; sonrakiler rng ile.
    """
    states = []
    for i in range(n):
        s = seed + i if seed is not None else None
        states.append(generate_random_state(s))
    return states
