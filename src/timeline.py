"""Project timeline and Gantt chart generation."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.forecasting import period_sort_key, sort_by_period


def infer_task_status(row: pd.Series) -> str:
    if "status" in row.index and pd.notna(row.get("status")) and str(row["status"]).strip():
        s = str(row["status"]).strip().lower()
        if "complete" in s:
            return "Completed"
        if "delay" in s or "late" in s:
            return "Delayed"
        if "run" in s or "progress" in s or "active" in s:
            return "Running"
        if "pend" in s:
            return "Pending"
        return str(row["status"]).title()

    actual = row.get("actual_amount", 0)
    planned = row.get("planned_cost", 0)
    etc = row.get("etc_amount", 0)
    cpi = row.get("cpi")

    if actual == 0 and etc > 0:
        return "Pending"
    if planned > 0 and actual >= planned * 0.95 and etc <= planned * 0.1:
        return "Completed"
    if cpi is not None and cpi < 0.9:
        return "Delayed"
    if actual > 0:
        return "Running"
    return "Pending"


def build_task_timeline(metrics_df: pd.DataFrame) -> pd.DataFrame:
    timeline = metrics_df.copy()
    timeline["task_status"] = timeline.apply(infer_task_status, axis=1)
    return timeline[["project_name", "cost_element", "period", "task_status", "actual_amount", "planned_cost", "cpi"]]


def build_gantt_chart(timeline_df: pd.DataFrame) -> go.Figure:
    """Gantt-style chart: tasks progressing across ordered time periods."""
    gantt = timeline_df.copy()
    periods = sorted(gantt["period"].unique(), key=period_sort_key)
    period_index = {p: i for i, p in enumerate(periods)}

    rows = []
    for (task, phase), group in gantt.groupby(["project_name", "cost_element"]):
        task_periods = [p for p in group["period"].unique() if p in period_index]
        if not task_periods:
            continue
        start = min(period_index[p] for p in task_periods)
        end = max(period_index[p] for p in task_periods) + 1
        latest = sort_by_period(group, "period").iloc[-1]
        rows.append({
            "task_label": f"{task} – {phase}",
            "start": start,
            "duration": end - start,
            "task_status": latest["task_status"],
        })

    if not rows:
        return go.Figure().update_layout(title="Project Timeline (Gantt)", height=400)

    bars = pd.DataFrame(rows)
    color_map = {
        "Completed": "#2ecc71",
        "Running": "#3498db",
        "Delayed": "#e74c3c",
        "Pending": "#95a5a6",
    }

    fig = go.Figure()
    for status, color in color_map.items():
        subset = bars[bars["task_status"] == status]
        if subset.empty:
            continue
        fig.add_trace(go.Bar(
            name=status,
            y=subset["task_label"],
            x=subset["duration"],
            base=subset["start"],
            orientation="h",
            marker_color=color,
        ))

    fig.update_layout(
        barmode="overlay",
        title="Project Timeline (Gantt View – tasks over weeks)",
        xaxis=dict(
            title="Timeline",
            tickmode="array",
            tickvals=list(range(len(periods))),
            ticktext=periods,
        ),
        yaxis_title="Task / Phase",
        height=max(450, len(bars) * 26),
        legend_title="Status",
    )
    return fig
