"""
AMI-ENGINE: Ethical Decision Engine

Public API - Stable interface for external use.
"""

# Version
__version__ = "1.0.0"
TRACE_VERSION = "1.0"

# Public API - Main engine
# Note: Import from parent directory (backward compatibility)
import sys
from pathlib import Path

# Add parent directory to path for imports
_parent = Path(__file__).resolve().parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

# Simplified API (recommended for new users)
from ami_engine.api import decide, replay_trace

# Full API (for advanced users)
from engine import moral_decision_engine, replay
from core.trace_collector import TraceCollector, build_decision_trace
from config_profiles import get_config, list_profiles

# Re-export for convenience
__all__ = [
    "__version__",
    "TRACE_VERSION",
    # Simplified API (recommended)
    "decide",
    "replay_trace",
    # Full API (advanced)
    "moral_decision_engine",
    "replay",
    "TraceCollector",
    "build_decision_trace",
    "get_config",
    "list_profiles",
]
