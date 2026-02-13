# AMI-ENGINE — B.6 Adversarial test base (04_QUALITY_AND_PHASE4_SPEC)
# Her test: zorlayıcı raw_state üretir, expected_behavior ile doğrular.

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine import moral_decision_engine


class AdversarialTestCase(ABC):
    """Phase 4.1 adversarial test temel sınıfı."""

    @abstractmethod
    def generate_states(self) -> List[Dict[str, Any]]:
        """Zorlayıcı raw_state listesi (10–50 arası önerilir)."""
        pass

    @abstractmethod
    def expected_behavior(self, result: Dict[str, Any], raw_state: Dict[str, Any]) -> None:
        """result üzerinde assert'ler; başarısızsa test fail."""
        pass

    def run(self) -> None:
        """Tüm state'leri çalıştırır ve expected_behavior ile doğrular."""
        states = self.generate_states()
        for i, raw_state in enumerate(states):
            result = moral_decision_engine(raw_state)
            self.expected_behavior(result, raw_state)
