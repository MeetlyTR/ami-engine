# AMI-ENGINE — Trace kayitlarini CSV olarak ekler (canli script'ler icin).
# Tek dosya: ilk cagrida header, sonra her trace icin bir satir append.

import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

CSV_COLUMNS = [
    "index", "t", "cus", "delta_cus", "cus_mean", "level", "soft_clamp",
    "human_escalation", "latency_ms", "phase",
    "run_id", "batch_id", "profile_state", "config_profile", "created_at",
    "J", "H", "confidence",
    "raw_severity", "raw_intervention", "raw_compassion", "raw_delay",
    "final_severity", "final_intervention", "final_compassion", "final_delay",
]


def _row_from_trace(trace: Dict[str, Any], index: int) -> list:
    raw = (trace.get("raw_action") or [0, 0, 0, 0])[:4]
    final = (trace.get("final_action") or trace.get("raw_action") or [0, 0, 0, 0])[:4]
    return [
        index,
        trace.get("t", ""),
        trace.get("cus", ""),
        trace.get("delta_cus") if trace.get("delta_cus") is not None else "",
        trace.get("cus_mean", ""),
        trace.get("level", ""),
        trace.get("soft_clamp", ""),
        trace.get("human_escalation", ""),
        trace.get("latency_ms") if trace.get("latency_ms") is not None else "",
        trace.get("phase", ""),
        trace.get("run_id") if trace.get("run_id") is not None else "",
        trace.get("batch_id") if trace.get("batch_id") is not None else "",
        trace.get("profile_state", ""),
        trace.get("config_profile", ""),
        trace.get("created_at") if trace.get("created_at") is not None else "",
        trace.get("J") if trace.get("J") is not None else "",
        trace.get("H") if trace.get("H") is not None else "",
        trace.get("confidence") if trace.get("confidence") is not None else "",
        raw[0] if len(raw) > 0 else "",
        raw[1] if len(raw) > 1 else "",
        raw[2] if len(raw) > 2 else "",
        raw[3] if len(raw) > 3 else "",
        final[0] if len(final) > 0 else "",
        final[1] if len(final) > 1 else "",
        final[2] if len(final) > 2 else "",
        final[3] if len(final) > 3 else "",
    ]


def append_trace_to_csv(csv_path: str, trace: Dict[str, Any], index: int) -> None:
    """Trace'i CSV dosyasina ekler; dosya yoksa header yazar (UTF-8)."""
    p = Path(csv_path)
    write_header = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=",")
        if write_header:
            w.writerow(CSV_COLUMNS)
        w.writerow(_row_from_trace(trace, index))


def traces_to_csv_string(traces: List[Dict[str, Any]]) -> str:
    """Mevcut trace listesini CSV metni olarak dondurur (dashboard indirme icin)."""
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=",")
    w.writerow(CSV_COLUMNS)
    for i, trace in enumerate(traces):
        w.writerow(_row_from_trace(trace, i))
    return buf.getvalue()
