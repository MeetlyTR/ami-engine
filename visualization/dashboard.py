# AMI-ENGINE Phase 4.7.2 — Real-time Safety Dashboard (TR/EN)
# Streamlit + Plotly; veri: JSONL veya Demo (engine N adım).

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from visualization.i18n import TEXTS, t
from visualization.plots import (
    plot_cus_timeline,
    plot_soft_clamp_map,
    plot_action_drift,
    plot_drift_panel,
    plot_chaos_scatter,
    plot_decision_boundary_heatmap,
    plot_latency_timeline,
    plot_cus_vs_latency,
    plot_level_timeline,
    plot_loss_evolution,
    plot_metrics_evolution,
    plot_param_evolution,
    plot_param_sensitivity,
)
from learning.feedback_metrics import load_traces_from_jsonl
from tools.csv_export import CSV_COLUMNS, traces_to_csv_string


def run_demo_steps(n: int, profile: str = "chaos", config_profile: str = "") -> list:
    from core.trace_collector import TraceCollector, build_decision_trace
    from engine import moral_decision_engine
    from simulation.scenario_generator import generate_batch

    collector = TraceCollector(max_buffer_size=max(n, 500))
    context = {"cus_history": []}
    states = generate_batch(n, profile=profile, seed=42)
    config_override = config_profile if config_profile else None
    for state in states:
        result = moral_decision_engine(state, context=context, config_override=config_override)
        entry = build_decision_trace(result, t=time.time())
        collector.push(entry)
    return collector.get_all()


# Model testi için sabit senaryo seti (dashboard'da az seçenek)
TEST_STATE_PROFILES = ["balanced", "safe", "chaos"]
TEST_CONFIG_PROFILES = ["", "scenario_test", "production_safe"]


def run_model_test(steps_per_scenario: int = 10, seed: int = 42) -> tuple:
    """Tüm (state x config) kombinasyonlarını çalıştırır; sonuç listesi ve hata listesi döner."""
    from core.trace_collector import TraceCollector, build_decision_trace
    from engine import moral_decision_engine
    from simulation.scenario_generator import generate_batch

    results = []
    errors = []
    for state_prof in TEST_STATE_PROFILES:
        for config_prof in TEST_CONFIG_PROFILES:
            config_label = config_prof or "varsayilan"
            name = f"{state_prof} × {config_label}"
            try:
                context = {"cus_history": []}
                states = generate_batch(steps_per_scenario, profile=state_prof, seed=seed)
                config_override = config_prof if config_prof else None
                collector = TraceCollector(max_buffer_size=500)
                for state in states:
                    result = moral_decision_engine(state, context=context, config_override=config_override)
                    entry = build_decision_trace(result, t=time.time())
                    collector.push(entry)
                traces = collector.get_all()
            except Exception as e:
                errors.append((name, str(e)))
                results.append({"senaryo": name, "durum": "HATA", "L0": 0, "L1": 0, "L2": 0, "cus": 0, "clamp_pct": 0, "hata": str(e)[:80]})
                continue
            if len(traces) != steps_per_scenario:
                errors.append((name, f"Trace sayısı {len(traces)}"))
                results.append({"senaryo": name, "durum": "HATA", "L0": 0, "L1": 0, "L2": 0, "cus": 0, "clamp_pct": 0, "hata": "trace sayisi"})
                continue
            l0 = sum(1 for t in traces if t.get("level") == 0)
            l1 = sum(1 for t in traces if t.get("level") == 1)
            l2 = sum(1 for t in traces if t.get("level") == 2)
            cus_vals = [t.get("cus", 0) for t in traces]
            mean_cus = sum(cus_vals) / len(cus_vals) if cus_vals else 0
            clamp_n = sum(1 for t in traces if t.get("soft_clamp"))
            clamp_pct = round(100 * clamp_n / len(traces), 1)
            ok = (l0 + l1 + l2 == len(traces)) and all(0 <= t.get("cus", -1) <= 1 for t in traces)
            results.append({
                "senaryo": name,
                "durum": "OK" if ok else "HATA",
                "L0": l0, "L1": l1, "L2": l2,
                "cus": round(mean_cus, 3),
                "clamp_pct": clamp_pct,
                "hata": "",
            })
            if not ok:
                errors.append((name, "level veya CUS aralık dışı"))
    return results, errors


def main():
    # Dil: URL ?lang=en ile kalıcı (refresh sonrası korunur); yoksa session, yoksa tr
    _url_lang = st.query_params.get("lang")
    if _url_lang in ("tr", "en"):
        st.session_state["lang"] = _url_lang
    lang = st.session_state.get("lang", "tr")
    st.set_page_config(page_title=t("page_title", lang), layout="wide")

    with st.sidebar:
        st.session_state["lang"] = st.radio(
            t("lang_sidebar", lang),
            ["tr", "en"],
            index=0 if st.session_state.get("lang", "tr") == "tr" else 1,
            format_func=lambda x: t("lang_tr", "tr") if x == "tr" else t("lang_en", "en"),
            key="lang_selector",
        )
        try:
            from engine import TRACE_VERSION
            st.caption(t("trace_version_label", lang) + ": **" + TRACE_VERSION + "**")
        except Exception:
            pass
    lang = st.session_state.get("lang", "tr")

    st.title(t("title", lang))
    st.caption(t("caption", lang))

    with st.expander("📖 " + t("how_to_read_title", lang)):
        st.markdown(t("how_to_read_body", lang))

    # --- 1) Veri kaynağı ve özet (açılır/kapanır) ---
    with st.expander("📥 " + t("section_data", lang), expanded=True):
        mode = st.radio(
            t("data_source_label", lang),
            [t("data_source_jsonl", lang), t("data_source_demo", lang)],
            horizontal=True,
            key="data_source",
        )
        traces = []
        if mode == t("data_source_jsonl", lang):
            path = st.text_input(t("jsonl_path_label", lang), value="traces.jsonl")
            # Canlı 10 dk testi: sadece traces_live.jsonl için
            if path and "traces_live" in path:
                with st.container():
                    st.caption("🔴 " + t("live_test_section", lang))
                    # Test süresi seçimi (90 sn = Deney 1, 10 dk = tam test)
                    duration_options = [(90, "90 sn"), (180, "3 dk"), (300, "5 dk"), (600, "10 dk")]
                    duration_sec = st.selectbox(
                        t("live_test_duration_label", lang),
                        options=[d[0] for d in duration_options],
                        format_func=lambda x: next(l for s, l in duration_options if s == x),
                        index=0,
                        key="live_duration",
                    )
                    proc = st.session_state.get("live_test_process")
                    running = proc is not None and proc.poll() is None
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if not running:
                            if st.button(t("live_test_start", lang), key="live_start"):
                                try:
                                    cmd = [sys.executable, "tools/realtime_10min.py", "--duration", str(duration_sec)]
                                    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                                    st.session_state["live_test_process"] = p
                                    st.session_state["live_test_start_ts"] = time.time()
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))
                        else:
                            if st.button(t("live_test_stop", lang), key="live_stop"):
                                try:
                                    p = st.session_state.get("live_test_process")
                                    if p and p.poll() is None:
                                        p.terminate()
                                    st.session_state.pop("live_test_process", None)
                                    st.session_state.pop("live_test_start_ts", None)
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))
                    with col_b:
                        if running:
                            start_ts = st.session_state.get("live_test_start_ts") or time.time()
                            elapsed = int(time.time() - start_ts)
                            st.caption(t("live_test_running", lang) + " — " + t("live_test_elapsed", lang) + f": {elapsed}s")
                    with col_c:
                        if not running:
                            if st.button("🗑️ " + t("live_test_reset", lang), key="live_reset", type="secondary"):
                                jsonl_path = ROOT / "traces_live.jsonl"
                                csv_path = ROOT / "traces_live.csv"
                                try:
                                    # Önce çalışan process varsa durdur
                                    p = st.session_state.get("live_test_process")
                                    if p is not None and p.poll() is None:
                                        p.terminate()
                                    st.session_state.pop("live_test_process", None)
                                    st.session_state.pop("live_test_start_ts", None)
                                    # run_id: dosyadan ilk satırdan al veya timestamp
                                    run_id = int(time.time() * 1000)
                                    if jsonl_path.exists():
                                        with open(jsonl_path, "r", encoding="utf-8") as f:
                                            for line in f:
                                                line = line.strip()
                                                if not line:
                                                    continue
                                                try:
                                                    obj = json.loads(line)
                                                    if obj.get("run_id") is not None:
                                                        run_id = obj["run_id"]
                                                    break
                                                except Exception:
                                                    break
                                    archive_dir = ROOT / "archive"
                                    archive_dir.mkdir(exist_ok=True)
                                    if jsonl_path.exists():
                                        jsonl_path.rename(archive_dir / f"traces_live_{run_id}.jsonl")
                                    if csv_path.exists():
                                        csv_path.rename(archive_dir / f"traces_live_{run_id}.csv")
                                    # Yeni boş dosyalar
                                    jsonl_path.touch()
                                    with open(csv_path, "w", newline="", encoding="utf-8") as f:
                                        import csv
                                        csv.writer(f, delimiter=",").writerow(CSV_COLUMNS)
                                    st.session_state.pop("display_traces", None)
                                    st.success(t("live_test_reset_success", lang))
                                    time.sleep(0.5)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Sıfırlama hatası: {e}")
                    if not running:
                        st.caption(t("live_test_reset_caption", lang))
            if path:
                traces = load_traces_from_jsonl(path)
        else:
            n_demo = st.number_input(t("demo_steps_label", lang), min_value=10, max_value=300, value=80, step=10)
            demo_profile = st.selectbox(
                t("demo_state_profile", lang),
                ["balanced", "safe", "critical", "chaos"],
                index=0,
                key="demo_profile",
            )
            _config_labels = {"": t("config_default", lang), "scenario_test": t("config_scenario_test", lang), "production_safe": t("config_production_safe", lang)}
            demo_config = st.selectbox(
                t("demo_config_profile", lang),
                ["", "scenario_test", "production_safe"],
                format_func=lambda x: _config_labels.get(x, x),
                key="demo_config",
            )
            if st.button(t("demo_run_btn", lang)):
                with st.spinner(t("demo_spinner", lang)):
                    traces = run_demo_steps(int(n_demo), profile=demo_profile, config_profile=demo_config)
                st.session_state["demo_traces"] = traces
                st.success(t("demo_success", lang).format(n=len(traces)))
            else:
                traces = st.session_state.get("demo_traces", [])

        auto_refresh = st.checkbox(t("auto_refresh", lang), value=False)

        if not traces:
            st.info(t("no_data_info", lang))
            if auto_refresh:
                # traces_live boşken kısa bekle (test başlatınca hemen veri görünsün)
                refresh_sleep = 5 if (path and "traces_live" in path) else 30
                time.sleep(refresh_sleep)
                st.rerun()
            # Sonraki bölümler veri olmadan gösterilmez
        else:
            filter_soft_clamp = st.checkbox(t("filter_soft_clamp_only", lang), value=False, key="filter_soft_clamp")
            display_traces = [e for e in traces if e.get("soft_clamp")] if filter_soft_clamp else traces
            st.session_state["display_traces"] = display_traces
            n = len(display_traces)
            clamp_count = sum(1 for e in display_traces if e.get("soft_clamp"))
            level_counts = {}
            for e in display_traces:
                lv = e.get("level", 0)
                level_counts[lv] = level_counts.get(lv, 0) + 1
            c1, c2, c3 = st.columns(3)
            c1.metric(t("metric_records", lang), n)
            c2.metric(t("metric_soft_clamp", lang), f"{100 * clamp_count / n:.1f}%" if n else "—")
            c3.metric(t("metric_escalation", lang), " L0:" + str(level_counts.get(0, 0)) + " L1:" + str(level_counts.get(1, 0)) + " L2:" + str(level_counts.get(2, 0)))
            # Canlı kanıt: son 1 dk (max_created_at - 60 ile stabil), tümü/filtreli, batch_id, run özeti
            with_ts = [e for e in traces if e.get("created_at") is not None]
            if with_ts:
                max_created = max(e.get("created_at") for e in with_ts)
                cutoff = max_created - 60
                son_1_dk_all = sum(1 for e in with_ts if (e.get("created_at") or 0) >= cutoff)
                with_ts_display = [e for e in display_traces if e.get("created_at") is not None]
                max_created_d = max((e.get("created_at") for e in with_ts_display), default=0)
                cutoff_d = max_created_d - 60
                son_1_dk_filtered = sum(1 for e in with_ts_display if (e.get("created_at") or 0) >= cutoff_d) if with_ts_display else 0
                last_batch = next((e.get("batch_id") for e in reversed(traces) if e.get("batch_id") is not None), None)
                run_id_val = next((e.get("run_id") for e in reversed(traces) if e.get("run_id") is not None), None)
                r1, r2, r3, r4 = st.columns(4)
                r1.metric(t("live_test_son_1_dk_all", lang), son_1_dk_all)
                r2.metric(t("live_test_son_1_dk_filtered", lang), son_1_dk_filtered if filter_soft_clamp else "—")
                r3.metric(t("live_test_son_batch", lang), last_batch if last_batch is not None else "—")
                if run_id_val is not None:
                    r4.metric(t("live_test_run_id", lang), run_id_val)
                # Batch rate: beklenen 10/10s = 60/60s, ölçülen son 60s
                st.caption(t("live_test_rate_expected", lang) + ": 10 trace / 10s  —  " + t("live_test_rate_measured", lang) + f": {son_1_dk_all} trace")
                # Run summary: run_id, başlangıç, geçen süre, toplam kayıt, son batch
                if run_id_val is not None and with_ts:
                    first_ts = min(e.get("created_at") for e in with_ts)
                    elapsed_run = int(max_created - first_ts) if max_created > first_ts else 0
                    st.caption(t("live_test_run_summary", lang) + f" — run_id={run_id_val} | toplam={len(traces)} kayıt | son batch={last_batch} | süre≈{elapsed_run}s")
            # Son 5 kayıt tablosu (index, level, cus, delta_cus, soft_clamp, latency_ms, batch_id)
            last5 = list(display_traces)[-5:] if len(display_traces) >= 5 else display_traces
            if last5:
                st.caption(t("live_test_last5_title", lang))
                st.dataframe(
                    [{"index": i, "level": e.get("level"), "cus": e.get("cus"), "delta_cus": e.get("delta_cus"), "soft_clamp": e.get("soft_clamp"), "latency_ms": e.get("latency_ms"), "batch_id": e.get("batch_id")} for i, e in enumerate(last5, start=len(display_traces)-len(last5))],
                    hide_index=True,
                    use_container_width=True,
                    column_config={"index": st.column_config.NumberColumn("index"), "level": st.column_config.NumberColumn("level"), "cus": st.column_config.NumberColumn("cus"), "delta_cus": st.column_config.NumberColumn("delta_cus"), "soft_clamp": st.column_config.CheckboxColumn("soft_clamp"), "latency_ms": st.column_config.NumberColumn("latency_ms"), "batch_id": st.column_config.NumberColumn("batch_id")},
                )
            # Anomali sayaçları: delta_cus > 0.2, latency > p99, soft_clamp sayısı
            if display_traces:
                latencies = [e.get("latency_ms") for e in display_traces if e.get("latency_ms") is not None]
                p99_val = None
                if len(latencies) >= 2:
                    s = sorted(latencies)
                    p99_val = s[min(int((len(s) - 1) * 0.99), len(s) - 1)]
                anomaly_delta = sum(1 for e in display_traces if (e.get("delta_cus") or 0) > 0.2)
                anomaly_latency = sum(1 for e in display_traces if p99_val is not None and (e.get("latency_ms") or 0) > p99_val)
                a1, a2, a3 = st.columns(3)
                a1.metric(t("live_test_anomaly_delta_cus", lang), anomaly_delta)
                a2.metric(t("live_test_anomaly_latency_p99", lang), anomaly_latency)
                a3.metric(t("metric_soft_clamp", lang) + " (n)", clamp_count)
                # Soft clamp kanıt: raw != final (L2 > 1e-9) sayısı ve oranı
                def _l2_diff(raw, final):
                    if not raw or not final or len(raw) != len(final):
                        return 0.0
                    return sum((float(a) - float(b)) ** 2 for a, b in zip(raw[:4], final[:4])) ** 0.5
                clamp_traces = [e for e in display_traces if e.get("soft_clamp")]
                clamp_changed = sum(1 for e in clamp_traces if _l2_diff(e.get("raw_action") or [], e.get("final_action") or []) > 1e-9)
                clamp_ratio = (clamp_changed / len(clamp_traces)) if clamp_traces else 0
                clamp_mean_l2 = sum(_l2_diff(e.get("raw_action") or [], e.get("final_action") or []) for e in clamp_traces) / len(clamp_traces) if clamp_traces else 0.0
                b1, b2, b3 = st.columns(3)
                b1.metric(t("live_test_clamp_changed_count", lang), clamp_changed)
                b2.metric(t("live_test_clamp_changed_ratio", lang), f"{100 * clamp_ratio:.1f}%" if clamp_traces else "—")
                b3.metric(t("live_test_clamp_mean_l2", lang), f"{clamp_mean_l2:.4f}" if clamp_traces else "—")
            # Latency percentiles (trace'de latency_ms varsa)
            latencies = [e.get("latency_ms") for e in display_traces if e.get("latency_ms") is not None]
            if latencies:
                s = sorted(latencies)
                nL = len(s)
                p50 = s[nL // 2]
                p95 = s[min(int((nL - 1) * 0.95), nL - 1)] if nL > 1 else s[0]
                p99 = s[min(int((nL - 1) * 0.99), nL - 1)] if nL > 1 else s[0]
                l1, l2, l3 = st.columns(3)
                l1.metric(t("metric_latency_p50", lang), f"{p50:.2f}")
                l2.metric(t("metric_latency_p95", lang), f"{p95:.2f}")
                l3.metric(t("metric_latency_p99", lang), f"{p99:.2f}")
            # Dashboard'dan CSV indir (dosya adı filtre durumunu yansıtır)
            csv_content = traces_to_csv_string(display_traces)
            csv_filename = "traces_export_softclamp_only.csv" if filter_soft_clamp else "traces_export.csv"
            st.download_button(
                label="\u2b07 " + t("download_csv", lang),
                data=csv_content,
                file_name=csv_filename,
                mime="text/csv",
                key="download_csv_btn",
            )

    if not traces:
        # Model testi ve Optimizasyon veri bağımsız; Gözlem panelleri için veri gerekli
        pass
    else:
        # --- 2) Gözlem panelleri (açılır/kapanır) ---
        chart_traces = st.session_state.get("display_traces", traces)
        with st.expander("📊 " + t("section_charts", lang), expanded=True):
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                fig_cus = plot_cus_timeline(chart_traces, lang=lang)
                if fig_cus:
                    st.plotly_chart(fig_cus, use_container_width=True)
            with row1_col2:
                fig_clamp = plot_soft_clamp_map(chart_traces, lang=lang)
                if fig_clamp:
                    st.plotly_chart(fig_clamp, use_container_width=True)

            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                fig_drift_act = plot_action_drift(chart_traces, lang=lang)
                if fig_drift_act:
                    st.plotly_chart(fig_drift_act, use_container_width=True)
            with row2_col2:
                fig_drift = plot_drift_panel(chart_traces, lang=lang)
                if fig_drift:
                    st.plotly_chart(fig_drift, use_container_width=True)

            fig_chaos = plot_chaos_scatter(chart_traces, lang=lang)
            if fig_chaos:
                st.plotly_chart(fig_chaos, use_container_width=True)

            fig_boundary = plot_decision_boundary_heatmap(chart_traces, lang=lang)
            if fig_boundary:
                st.plotly_chart(fig_boundary, use_container_width=True)
            else:
                st.caption(t("decision_boundary_caption", lang))

            fig_level = plot_level_timeline(chart_traces, lang=lang)
            if fig_level:
                st.plotly_chart(fig_level, use_container_width=True)

            fig_latency = plot_latency_timeline(chart_traces, lang=lang)
            fig_cus_lat = plot_cus_vs_latency(chart_traces, lang=lang)
            lat_col1, lat_col2 = st.columns(2)
            with lat_col1:
                if fig_latency:
                    st.plotly_chart(fig_latency, use_container_width=True)
            with lat_col2:
                if fig_cus_lat:
                    st.plotly_chart(fig_cus_lat, use_container_width=True)

    # --- 3) Model testi (açılır/kapanır) ---
    with st.expander("🧪 " + t("section_model_test", lang), expanded=False):
        st.caption(t("model_test_caption", lang))
        if st.button(t("model_test_run_btn", lang), key="run_model_test"):
            with st.spinner(t("model_test_spinner", lang)):
                test_results, test_errors = run_model_test(steps_per_scenario=10, seed=42)
            st.session_state["model_test_results"] = test_results
            st.session_state["model_test_errors"] = test_errors
        if "model_test_results" in st.session_state:
            res = st.session_state["model_test_results"]
            errs = st.session_state.get("model_test_errors", [])
            st.markdown(t("model_test_what_tested", lang))
            st.dataframe(
                res,
                column_config={
                    "senaryo": st.column_config.TextColumn(t("col_scenario", lang), width="medium"),
                    "durum": st.column_config.TextColumn(t("col_status", lang), width="small"),
                    "L0": st.column_config.NumberColumn("L0", format="%d"),
                    "L1": st.column_config.NumberColumn("L1", format="%d"),
                    "L2": st.column_config.NumberColumn("L2", format="%d"),
                    "cus": st.column_config.NumberColumn(t("col_cus_avg", lang), format="%.2f"),
                    "clamp_pct": st.column_config.NumberColumn(t("col_clamp_pct", lang), format="%.1f"),
                    "hata": st.column_config.TextColumn(t("col_error", lang), width="large"),
                },
                hide_index=True,
                use_container_width=True,
            )
            total = len(res)
            passed = sum(1 for r in res if r.get("durum") == "OK")
            if passed == total:
                st.success(t("model_test_success", lang).format(passed=passed, total=total))
            else:
                st.warning(t("model_test_warning", lang).format(passed=passed, total=total, errs=errs))
        else:
            st.info(t("model_test_info", lang))

    # --- 4) Optimizasyon (açılır/kapanır) ---
    with st.expander("📈 " + t("section_optimization", lang), expanded=False):
        st.caption(t("optimization_caption", lang))
        learning_mode = st.radio(
            t("optimization_data_label", lang),
            [t("optimization_load_jsonl", lang), t("optimization_run_now", lang)],
            key="learning_radio",
            horizontal=True,
        )
        opt_history = []

        if learning_mode == t("optimization_load_jsonl", lang):
            hist_path = st.text_input(t("optimization_hist_path", lang), value="optimization_history.jsonl", key="hist_path")
            if hist_path and Path(hist_path).exists():
                with open(hist_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                opt_history.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
                if opt_history:
                    st.success(t("optimization_load_success", lang).format(n=len(opt_history)))
        else:
            opt_profile = st.selectbox(
                t("optimization_state_profile", lang),
                ["balanced", "safe", "critical", "chaos"],
                index=0,
                key="opt_profile",
            )
            opt_config_base = st.selectbox(
                t("optimization_config_base", lang),
                ["varsayılan", "scenario_test"],
                index=1,
                format_func=lambda x: t("config_base_default", lang) if x == "varsayılan" else t("config_base_scenario_test", lang),
                key="opt_config_base",
            )
            if st.button(t("optimization_run_btn", lang), key="run_opt"):
                import config as _config
                from simulation.scenario_generator import generate_batch
                from learning.run_optimization_loop import run_optimization_loop
                from learning.policy_optimizer import PARAM_BOUNDS

                n_steps, n_states, n_cand = 4, 40, 3
                if opt_config_base == "scenario_test":
                    from config_profiles import get_config
                    initial = get_config("scenario_test")
                    base_config = {k: v for k, v in initial.items() if k not in PARAM_BOUNDS}
                else:
                    initial = {
                        "J_MIN": _config.J_MIN, "H_MAX": _config.H_MAX,
                        "SOFT_CLAMP_ALPHA": _config.SOFT_CLAMP_ALPHA,
                        "SOFT_CLAMP_BETA": _config.SOFT_CLAMP_BETA,
                        "SOFT_CLAMP_GAMMA": _config.SOFT_CLAMP_GAMMA,
                        "DELTA_CUS_THRESHOLD": _config.DELTA_CUS_THRESHOLD,
                        "CUS_MEAN_THRESHOLD": _config.CUS_MEAN_THRESHOLD,
                    }
                    base_config = None
                states = generate_batch(n_states, profile=opt_profile, seed=42)
                with st.spinner(t("optimization_spinner", lang)):
                    try:
                        opt_history = run_optimization_loop(
                            initial, states,
                            num_steps=n_steps,
                            num_candidates=n_cand,
                            history_path="optimization_history.jsonl",
                            base_config=base_config,
                            curriculum_schedule=None,
                            states_per_step=n_states,
                        )
                    except TypeError:
                        opt_history = run_optimization_loop(
                            initial, states,
                            num_steps=n_steps,
                            num_candidates=n_cand,
                            history_path="optimization_history.jsonl",
                        )
                st.session_state["opt_history"] = opt_history
                st.success(t("optimization_success", lang).format(n=len(opt_history), l0=opt_history[0]["L"], l1=opt_history[-1]["L"]))
            else:
                opt_history = st.session_state.get("opt_history", [])

        if opt_history:
            row_l1, row_l2 = st.columns(2)
            with row_l1:
                fig_loss = plot_loss_evolution(opt_history, lang=lang)
                if fig_loss:
                    st.plotly_chart(fig_loss, use_container_width=True)
            with row_l2:
                fig_met = plot_metrics_evolution(opt_history, lang=lang)
                if fig_met:
                    st.plotly_chart(fig_met, use_container_width=True)
            fig_param = plot_param_evolution(opt_history, lang=lang)
            if fig_param:
                st.plotly_chart(fig_param, use_container_width=True)
            fig_sens = plot_param_sensitivity(opt_history, lang=lang)
            if fig_sens:
                st.plotly_chart(fig_sens, use_container_width=True)

    # auto_refresh is set inside "Veri" expander; rerun when enabled (traces loaded)
    if traces and auto_refresh:
        time.sleep(30)
        st.rerun()


if __name__ == "__main__":
    main()
