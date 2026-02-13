# AMI-ENGINE — State Encoder (Phase 2 spec §1.1)
# Ham durumu standart state vektörüne dönüştürür; deterministik, [0,1] clamp.

from dataclasses import dataclass
from typing import Any, Dict

from config import DEFAULT_UNKNOWN


@dataclass(frozen=True)
class State:
    """Kodlanmış state: x_ext (dış), x_moral (iç)."""
    x_ext: tuple
    x_moral: tuple

    def __post_init__(self):
        assert len(self.x_ext) == 4 and len(self.x_moral) == 5


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _get_float(data: Dict[str, Any], key: str, default: float = DEFAULT_UNKNOWN) -> float:
    v = data.get(key)
    if v is None:
        return default
    try:
        return _clamp(float(v))
    except (TypeError, ValueError):
        return default


def encode_state(raw_state: Dict[str, Any]) -> State:
    """
    Ham durum sözlüğünü Phase 1 state vektörüne çevirir.
    Eksik/geçersiz alanlar DEFAULT_UNKNOWN (0.5) ile doldurulur.
    """
    x_ext = (
        _get_float(raw_state, "physical"),
        _get_float(raw_state, "social"),
        _get_float(raw_state, "context"),
        _get_float(raw_state, "risk"),
    )
    x_moral = (
        _get_float(raw_state, "compassion"),
        _get_float(raw_state, "justice"),
        _get_float(raw_state, "harm_sens"),
        _get_float(raw_state, "responsibility"),
        _get_float(raw_state, "empathy"),
    )
    return State(x_ext=x_ext, x_moral=x_moral)
