# Phase 4.7.1 — Trace Collector unit + integration tests

import json
import tempfile
import time
from pathlib import Path

from core.trace_collector import TraceCollector, build_decision_trace


def test_build_decision_trace_minimal():
    """Engine çıktısı minimal (uncertainty/temporal yok) olsa da trace üretilir."""
    engine_result = {
        "action": [0.5, 0.3, 0.2, 0.6],
        "raw_action": [0.6, 0.4, 0.1, 0.7],
        "escalation": 0,
        "soft_safe_applied": True,
        "confidence": 0.85,
        "human_escalation": False,
    }
    entry = build_decision_trace(engine_result, t=12345.0)
    assert entry["t"] == 12345.0
    assert entry["cus"] == 0.0
    assert entry["raw_action"] == [0.6, 0.4, 0.1, 0.7]
    assert entry["final_action"] == [0.5, 0.3, 0.2, 0.6]
    assert entry["soft_clamp"] is True
    assert entry["level"] == 0
    assert entry["confidence"] == 0.85
    assert entry["human_escalation"] is False
    assert "chaos" in entry
    assert entry["chaos"] is False


def test_build_decision_trace_full():
    """Uncertainty, temporal_drift, self_regulation ile tam trace."""
    engine_result = {
        "action": [0.4, 0.3, 0.3, 0.5],
        "raw_action": [0.5, 0.4, 0.2, 0.6],
        "escalation": 1,
        "soft_safe_applied": True,
        "confidence": 0.72,
        "human_escalation": False,
        "uncertainty": {"cus": 0.35, "hi": 0.2, "de": 0.1},
        "temporal_drift": {"delta_cus": 0.08, "cus_mean": 0.32},
        "self_regulation": {"delta_confidence": 0.05},
    }
    entry = build_decision_trace(engine_result, t=1000.0, chaos=True)
    assert entry["t"] == 1000.0
    assert entry["cus"] == 0.35
    assert entry["delta_cus"] == 0.08
    assert entry["cus_mean"] == 0.32
    assert entry["delta_confidence"] == 0.05
    assert entry["level"] == 1
    assert entry["uncertainty"] == 0.35
    assert entry["chaos"] is True


def test_build_decision_trace_default_t():
    """t verilmezse time.time() kullanılır."""
    engine_result = {"action": [0.5, 0.5, 0.5, 0.5], "escalation": 0}
    before = time.time()
    entry = build_decision_trace(engine_result)
    after = time.time()
    assert before <= entry["t"] <= after


def test_trace_collector_ring_buffer():
    """Ring buffer: max 3, 5 push → son 3 kalır."""
    c = TraceCollector(max_buffer_size=3, jsonl_path=None)
    for i in range(5):
        c.push({"t": float(i), "cus": i})
    assert len(c) == 3
    recent = c.get_recent(2)
    assert len(recent) == 2
    assert recent[-1]["t"] == 4.0
    assert recent[-2]["t"] == 3.0
    all_ = c.get_all()
    assert len(all_) == 3
    assert [x["t"] for x in all_] == [2.0, 3.0, 4.0]


def test_trace_collector_get_recent_zero():
    """get_recent(0) boş liste."""
    c = TraceCollector(max_buffer_size=10)
    c.push({"t": 1.0})
    assert c.get_recent(0) == []


def test_trace_collector_jsonl_append():
    """jsonl_path verilirse her push'ta dosyaya append."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        c = TraceCollector(max_buffer_size=10, jsonl_path=path)
        c.push({"t": 1.0, "cus": 0.2})
        c.push({"t": 2.0, "cus": 0.3})
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 2
        row = json.loads(lines[0])
        assert row["t"] == 1.0 and row["cus"] == 0.2
    finally:
        Path(path).unlink(missing_ok=True)


def test_trace_collector_with_engine():
    """Gerçek engine çıktısı ile build_decision_trace + push."""
    from engine import moral_decision_engine

    state = {
        "physical": 0.5, "social": 0.5, "context": 0.5, "risk": 0.5,
        "compassion": 0.6, "justice": 0.7, "harm_sens": 0.4,
        "responsibility": 0.5, "empathy": 0.5,
    }
    result = moral_decision_engine(state)
    entry = build_decision_trace(result)
    assert "t" in entry
    assert "cus" in entry
    assert len(entry["raw_action"]) == 4
    assert len(entry["final_action"]) == 4
    assert entry["level"] in (0, 1, 2)
    collector = TraceCollector(max_buffer_size=10)
    collector.push(entry)
    assert len(collector) == 1
    assert collector.get_recent(1)[0]["cus"] == entry["cus"]
