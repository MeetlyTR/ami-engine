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

# Import from repo root packages via shim modules
# Note: These are backward compatibility shims that import from repo root
# The actual modules are at repo root, not in the package
try:
    # Try importing from repo root (when installed as package)
    import sys
    from pathlib import Path
    
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    
    from core.trace_collector import TraceCollector, build_decision_trace
    from config_profiles import get_config, list_profiles
except ImportError:
    # Fallback: if core/config_profiles not found, these won't be available
    # This should only happen in very unusual setups
    TraceCollector = None
    build_decision_trace = None
    get_config = None
    list_profiles = None

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
