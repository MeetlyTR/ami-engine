# AMI-ENGINE — Action Generator (Phase 2 spec §1.2)
# Verilen state için aday aksiyon kümesi üretir; kural tabanlı, deterministik.

from typing import List

from config import ACTION_GRID_RESOLUTION
from .state_encoder import State


def generate_actions(
    x_t: State,
    resolution: List[float] | None = None,
) -> List[List[float]]:
    """
    Grid tabanlı aday aksiyon listesi. Her a = [severity, compassion, intervention, delay] ∈ [0,1]^4.
    'Hiçbir şey yapma' [0,0,0,1] her zaman dahil.
    """
    grid = resolution or ACTION_GRID_RESOLUTION
    A: List[List[float]] = []
    for severity in grid:
        for compassion in grid:
            for intervention in grid:
                for delay in grid:
                    A.append([float(severity), float(compassion), float(intervention), float(delay)])
    A.append([0.0, 0.0, 0.0, 1.0])
    return A
