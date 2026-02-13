# AMI-ENGINE

**Ethical Decision Engine with L0/L1/L2 Escalation, Soft Clamp, and Auditability**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> **Decision support kernel** for ethical AI systems. Provides deterministic, auditable moral reasoning with automatic escalation to human oversight.

---

## Quick Start

```bash
pip install ami-engine
```

```python
from ami_engine import decide

result = decide({
    "risk": 0.7, "severity": 0.8, "physical": 0.6, "social": 0.5,
    "context": 0.4, "compassion": 0.5, "justice": 0.9,
    "harm_sens": 0.5, "responsibility": 0.7, "empathy": 0.6
}, profile="scenario_test")

print(f"Action: {result['action']}, Level: L{result['escalation']}")
# Action: [0.0, 1.0, 0.58, 0.29], Level: L1
```

**CLI:**
```bash
ami-engine dashboard    # Start visualization dashboard
ami-engine realtime      # Run live test
ami-engine tests         # Run test suite
```

---

## What It Does

AMI-ENGINE is a **regulation-grade** engine for **ethical decision-making**. It takes raw state as input, computes moral scores (Justice, Harm, Compassion), and produces safe actions through **three-level escalation** (L0/L1/L2).

### Core Features

- **L0/L1/L2 Escalation**: Automatic decision → Soft clamp → Human escalation
- **Soft Clamp**: Softly constrains raw outputs that exceed safety boundaries
- **Auditability**: Full trace (JSONL/CSV) for every decision + replay support
- **Temporal Drift**: Uncertainty tracking over time via CUS (Cumulative Uncertainty Score)
- **Config Profiles**: Scenario-based threshold settings (scenario_test, production_safe, etc.)

---

## What It Doesn't Do

- ❌ **Does not make domain-specific decisions**: This is a **decision regulator**; domain knowledge comes from the adapter layer
- ❌ **Does not process personal data**: Receives raw state from domain adapter; does not collect/surveil data
- ❌ **Does not apply automatic sanctions**: Human escalation is mandatory at L2
- ❌ **Does not perform surveillance/identification**: These uses are prohibited (see USAGE_POLICY.md)

---

## Installation

```bash
pip install ami-engine
```

## Quick Start

### Python API

**Simplified API (Recommended):**

```python
from ami_engine import decide

# Raw state (comes from domain adapter)
raw_state = {
    "risk": 0.7,
    "severity": 0.8,
    "physical": 0.6,
    "social": 0.5,
    "context": 0.4,
    "compassion": 0.5,
    "justice": 0.9,
    "harm_sens": 0.5,
    "responsibility": 0.7,
    "empathy": 0.6,
}

# Make decision
result = decide(raw_state, profile="scenario_test")

# Result
action = result["action"]  # [severity, intervention, compassion, delay]
level = result["escalation"]  # 0, 1, or 2
human_escalation = result["human_escalation"]  # True/False
```

**Full API (Advanced):**

```python
from ami_engine import moral_decision_engine, replay_trace

result = moral_decision_engine(
    raw_state,
    config_override="scenario_test",
    context={"cus_history": []}
)

# Replay trace
replayed = replay_trace(result["trace"], validate=True)
```

See `examples/` directory for more examples.

### CLI

```bash
# Start dashboard
ami-engine dashboard

# Live test (90 seconds)
ami-engine realtime --duration 90 --profile scenario_test

# Run test suite
ami-engine tests
```

---

## L0/L1/L2 Meaning

- **L0**: Automatic decision — engine produced a safe action
- **L1**: Soft clamp applied — raw output was constrained, but continues automatically
- **L2**: Human escalation — human decision required (fail-safe triggered)

Each level is marked in the trace via the `level` field.

---

## Trace and Auditability

Full trace is generated for every decision:

- **JSONL**: `traces_live.jsonl` (each line is a trace)
- **CSV**: `traces_live.csv` (raw vs final action comparison)
- **Dashboard**: Visualization via `ami-engine dashboard`

Trace schema: `TRACE_VERSION = "1.0"` (version increments on changes).

**Replay**: Reproduce the same decision with `replay(trace)`.

---

## Config Profiles

```python
from ami_engine import get_config, list_profiles

# Available profiles
print(list_profiles())  # ['base', 'scenario_test', 'production_safe', ...]

# Use profile
config = get_config("scenario_test")
result = moral_decision_engine(raw_state, config_override=config)
```

---

## Adapter Pattern

AMI-ENGINE is domain-agnostic. An **adapter** layer is required to connect to a domain:

```
Domain Input → Adapter → raw_state → AMI-ENGINE → action → Adapter → Domain Output
```

Example adapters:
- Chat messages → risk score → raw_state
- Sensor data → physical risk → raw_state
- Customer requests → urgency score → raw_state

---

## Examples

See the `examples/` directory for complete examples:

- **hello_world.py**: Simplest usage example
- **replay_example.py**: Trace replay demonstration
- **trace_collection.py**: Collecting multiple traces

Run examples:
```bash
python examples/hello_world.py
```

## Documentation

- **README.md** (this file): Overview
- **USAGE_POLICY.md**: Usage policy and prohibitions
- **SAFETY_LIMITATIONS.md**: Safety boundaries and warnings
- **AUDITABILITY.md**: Auditability and trace schema
- **CHANGELOG.md**: Version history
- **examples/README.md**: Example usage guide

---

## License

Apache-2.0 License — See LICENSE file for details.

---

## Contributing

See the GitHub repository to open issues and submit PRs.

**Contact**: mucahit.muzaffer@gmail.com

**Security**: Please use the private channel for security vulnerability reports (specified in USAGE_POLICY.md).

---

## Version

**1.0.0** — First stable release
