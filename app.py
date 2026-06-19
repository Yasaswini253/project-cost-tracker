"""
AI-Powered Predictive Project Cost Intelligence System
Run: streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.anomaly_detector import detect_anomalies
from src.chat_assistant import answer_question
from src.column_mapper import STANDARD_FIELDS, get_raw_columns, suggest_column_mapping
from src.dashboard import (
    render_alerts,
    render_budget_status_badges,
    render_chat_assistant,
    render_charts,
    render_executive_summary_card,
    render_header,
    render_health_gauge,
    render_intelligence_sections,
    render_kpi_cards,
    render_potential_savings,
    render_project_ranking,
    render_project_risk_cards,
    render_timeline,
)
from src.data_loader import SUPPORTED_COLUMN_NAMES, SUPPORTED_FILE_TYPES, consolidate_cost_data, load_cost_file, load_multiple_cost_files
from src.forecasting import build_cost_trend_forecast, build_weekly_trend_chart
from src.fraud_analysis import analyze_vendor_performance, detect_duplicate_invoices, detect_fraud_spending, get_worst_vendor
from src.intelligence import (
    analyze_root_causes,
    calculate_burn_rate,
    calculate_health_scores,
    forecast_completion_cost,
    generate_recommendations,
    generate_weekly_report,
    get_executive_summary,
    predict_cost_overruns,
)
from src.metrics import calculate_metrics, get_kpi_summary, summarize_by_project
from src.notifications import generate_alerts
from src.risk import calculate_potential_savings, enrich_project_risk, get_cost_distribution, get_department_costs, rank_projects
from src.timeline import build_gantt_chart, build_task_timeline

SAMPLE_ETC = ROOT / "sample_data" / "etc_tasks.csv"
SAMPLE_ACTUAL = ROOT / "sample_data" / "actual_tasks.csv"


def _build_manual_mapping(raw_columns: list[str], file_type: str, prefix: str) -> dict[str, str]:
    suggestions = suggest_column_mapping(raw_columns, file_type)
    mapping: dict[str, str] = {}
    st.caption(f"Map your columns ({file_type.upper()}):")
    for raw_col in raw_columns:
        default = suggestions.get(raw_col, "(skip)")
        options = ["(skip)"] + list(STANDARD_FIELDS.keys())
        idx = options.index(default) if default in options else 0
        selected = st.selectbox(f"{prefix}: `{raw_col}` →", options, index=idx, key=f"{prefix}_{raw_col}_{file_type}")
        if selected != "(skip)":
            mapping[raw_col] = selected
    return mapping


def main() -> None:
    st.set_page_config(page_title="AI Project Cost Intelligence", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
    render_header()

    with st.sidebar:
        st.header("Upload Cost Files")
        st.markdown("**Supported:** CSV, TSV, Excel | **Multiple files** allowed")

        etc_files = st.file_uploader("ETC Files", type=SUPPORTED_FILE_TYPES, accept_multiple_files=True)
        actual_files = st.file_uploader("Actual Cost Files", type=SUPPORTED_FILE_TYPES, accept_multiple_files=True)
        use_samples = st.checkbox("Use sample Task_ID data", value=not (etc_files and actual_files))

        use_manual_mapping = st.checkbox("Manual Column Mapping", value=False, help="Use when your column names are different and auto-read fails.")

        etc_mapping = None
        actual_mapping = None
        if use_manual_mapping and etc_files:
            raw = get_raw_columns(etc_files[0])
            etc_mapping = _build_manual_mapping(raw, "etc", "ETC")
        if use_manual_mapping and actual_files:
            raw = get_raw_columns(actual_files[0])
            actual_mapping = _build_manual_mapping(raw, "actual", "Actual")

        with st.expander("Auto-read column names", expanded=False):
            st.markdown(
                f"**Task/Project:** `{SUPPORTED_COLUMN_NAMES['project']}`  \n"
                f"**ETC:** `{SUPPORTED_COLUMN_NAMES['etc_amount']}`  \n"
                f"**Actual:** `{SUPPORTED_COLUMN_NAMES['actual_amount']}`  \n"
                f"**Optional:** `{SUPPORTED_COLUMN_NAMES['optional']}`"
            )
            st.info("If auto-read fails, enable **Manual Column Mapping** above and map each column yourself.")

        st.download_button("Sample ETC", SAMPLE_ETC.read_bytes(), "etc_tasks.csv", "text/csv")
        st.download_button("Sample Actual", SAMPLE_ACTUAL.read_bytes(), "actual_tasks.csv", "text/csv")

    try:
        if use_samples:
            etc_df = load_cost_file(str(SAMPLE_ETC), "etc")
            actual_df = load_cost_file(str(SAMPLE_ACTUAL), "actual")
            st.info("Using sample Task_ID / Task_Nam / ETC_Cost data.")
        elif etc_files and actual_files:
            etc_df = load_multiple_cost_files(etc_files, "etc", etc_mapping)
            actual_df = load_multiple_cost_files(actual_files, "actual", actual_mapping)
            st.success(f"Loaded {len(etc_files)} ETC + {len(actual_files)} Actual file(s) — {len(etc_df)} + {len(actual_df)} rows")
        else:
            st.warning("Upload ETC and Actual files, or enable sample data.")
            st.stop()

        consolidated = consolidate_cost_data(etc_df, actual_df)
        metrics_df = calculate_metrics(consolidated)
        anomaly_df = detect_anomalies(metrics_df)
        project_summary = summarize_by_project(anomaly_df)
        kpis = get_kpi_summary(anomaly_df)

        health = calculate_health_scores(project_summary, anomaly_df)
        root_causes = analyze_root_causes(project_summary, anomaly_df)
        predictions = predict_cost_overruns(project_summary, anomaly_df, root_causes)
        burn_rate = calculate_burn_rate(anomaly_df)
        recommendations = generate_recommendations(project_summary, anomaly_df, root_causes, predictions)
        forecasts = forecast_completion_cost(anomaly_df, project_summary)
        duplicates = detect_duplicate_invoices(actual_df)
        fraud = detect_fraud_spending(anomaly_df)
        vendors = analyze_vendor_performance(actual_df, anomaly_df)
        worst_vendor = get_worst_vendor(vendors)
        savings = calculate_potential_savings(project_summary, duplicates, vendors)
        project_risk = enrich_project_risk(project_summary, health)
        rankings = rank_projects(project_risk)
        cost_dist = get_cost_distribution(anomaly_df)
        dept_costs = get_department_costs(anomaly_df)
        timeline_df = build_task_timeline(anomaly_df)
        gantt_fig = build_gantt_chart(timeline_df)
        trend_fig = build_weekly_trend_chart(actual_df, anomaly_df)
        forecast_fig = build_cost_trend_forecast(anomaly_df)
        weekly_report = generate_weekly_report(kpis, project_summary, health, recommendations)
        alerts = generate_alerts(project_summary, health, predictions, burn_rate, duplicates, fraud, vendors, kpis)
        exec_summary = get_executive_summary(project_summary, health, predictions, alerts, duplicates, vendors, savings, kpis)

        render_executive_summary_card(exec_summary)
        render_kpi_cards(kpis)
        render_budget_status_badges(kpis)

        c1, c2 = st.columns([1, 1])
        with c1:
            render_health_gauge(health)
        with c2:
            render_potential_savings(savings)

        render_alerts(alerts)
        render_project_risk_cards(project_risk)
        render_project_ranking(rankings)
        render_timeline(timeline_df, gantt_fig)
        render_charts(project_summary, anomaly_df, anomaly_df, forecast_fig, trend_fig, burn_rate, cost_dist, dept_costs)
        render_intelligence_sections(
            predictions, health, root_causes, recommendations, forecasts,
            duplicates, fraud, vendors, worst_vendor, weekly_report,
        )
        render_chat_assistant(lambda q: answer_question(
            q, project_summary, project_risk, health, root_causes, predictions,
            vendors, anomaly_df, rankings, kpis, worst_vendor,
        ))

        st.divider()
        st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
        st.download_button("Download Report", anomaly_df.to_csv(index=False).encode("utf-8"), "cost_intelligence_report.csv", "text/csv")

    except Exception as exc:
        st.error(f"Error: {exc}")
        st.exception(exc)
        st.info("Enable **Manual Column Mapping** in the sidebar to map your columns manually.")


if __name__ == "__main__":
    main()
