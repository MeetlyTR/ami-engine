# Backward compatibility shim for engine.py
# This file allows existing code to continue working:
#   from engine import moral_decision_engine
#
# New code should use:
#   from ami_engine import moral_decision_engine

from ami_engine.engine import *
from ami_engine.engine import (
    moral_decision_engine,
    replay,
    extract_raw_state,
    extract_action,
    extract_selection_data,
    extract_fail_safe_data,
    compute_trace_hash,
)

__all__ = [
    "moral_decision_engine",
    "replay",
    "extract_raw_state",
    "extract_action",
    "extract_selection_data",
    "extract_fail_safe_data",
    "compute_trace_hash",
]
