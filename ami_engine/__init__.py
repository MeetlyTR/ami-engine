"""
AMI-ENGINE: Ethical Decision Engine

Public API - Stable interface for external use.
"""

# Version
__version__ = "1.0.0"

# Import trace version from trace_types
from ami_engine.trace_types import TRACE_VERSION

# Simplified API (recommended for new users)
from ami_engine.api import decide, replay_trace

# Full API (for advanced users)
from ami_engine.engine import moral_decision_engine, replay

# Import from repo root packages
# Note: core/ and config_profiles/ are at repo root for backward compatibility
# When installed as package, these are accessible via py-modules in pyproject.toml
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
