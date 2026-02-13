# AMI-ENGINE Phase 4.3 — Chaos invariant'ları
# ∀ scenario: J < J_min → override; H > H_max → override; confidence < 0.20 → human_escalation.

from typing import Any, Dict, List


class ChaosInvariantError(Exception):
    """Bir chaos invariant ihlal edildi."""
    def __init__(self, msg: str, config: Dict[str, Any], record: Dict[str, Any], index: int):
        self.config = config
        self.record = record
        self.index = index
        super().__init__(msg)


def check_invariants(
    records: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> None:
    """
    Tüm kayıtlar üzerinde chaos invariant'larını doğrular.
    İhlal varsa ChaosInvariantError fırlatır.
    """
    j_min = config.get("J_MIN", 0.85)
    h_max = config.get("H_MAX", 0.30)
    escalation_force = 0.20

    for i, rec in enumerate(records):
        j = rec.get("J")
        h = rec.get("H")
        override = rec.get("override", False)
        human_escalation = rec.get("human_escalation", False)
        confidence = rec.get("confidence")

        if j is not None and j < j_min and not override:
            raise ChaosInvariantError(
                f"J < J_min ({j:.4f} < {j_min}) ama override=False",
                config=config,
                record=rec,
                index=i,
            )
        if h is not None and h > h_max and not override:
            raise ChaosInvariantError(
                f"H > H_max ({h:.4f} > {h_max}) ama override=False",
                config=config,
                record=rec,
                index=i,
            )
        if confidence is not None and confidence < escalation_force and not human_escalation:
            raise ChaosInvariantError(
                f"confidence < 0.20 ({confidence:.4f}) ama human_escalation=False",
                config=config,
                record=rec,
                index=i,
            )
        if rec.get("soft_safe_applied") and rec.get("action") and len(rec["action"]) >= 4:
            a = rec["action"]
            for idx, x in enumerate(a[:4]):
                if not (0 <= x <= 1):
                    raise ChaosInvariantError(
                        f"Level 1 soft_safe_applied ama aksiyon [0,1]^4 dışında: idx={idx} val={x:.4f}",
                        config=config,
                        record=rec,
                        index=i,
                    )
