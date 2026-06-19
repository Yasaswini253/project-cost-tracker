"""Calculate cost variance, CPI, and budget status."""

from __future__ import annotations

import pandas as pd


def calculate_metrics(consolidated_df: pd.DataFrame) -> pd.DataFrame:
    """Add cost variance, CPI, and budget status to consolidated data."""
    df = consolidated_df.copy()

    df["cost_variance"] = df["earned_value"] - df["actual_amount"]
    df["schedule_cost_variance"] = df["planned_cost"] - df["actual_amount"]

    df["cpi"] = df.apply(
        lambda row: row["earned_value"] / row["actual_amount"]
        if row["actual_amount"] > 0
        else None,
        axis=1,
    )

    df["etc_to_actual_ratio"] = df.apply(
        lambda row: row["etc_amount"] / row["actual_amount"]
        if row["actual_amount"] > 0
        else None,
        axis=1,
    )

    df["budget_status"] = df.apply(_budget_status, axis=1)
    df["performance_status"] = df["budget_status"]
    df["variance_pct"] = df.apply(
        lambda row: (row["cost_variance"] / row["earned_value"] * 100)
        if row["earned_value"] > 0
        else 0,
        axis=1,
    )

    return df


def _budget_status_row(cpi: float | None, variance: float, planned: float) -> str:
    if cpi is None and planned > 0 and variance >= 0:
        return "On Budget"
    if cpi is None:
        return "No Actuals"

    if cpi >= 1.0 or variance >= 0:
        if cpi >= 1.05:
            return "Under Budget"
        return "On Budget"
    if cpi >= 0.9:
        return "On Budget"
    return "Over Budget"


def _budget_status(row: pd.Series) -> str:
    return _budget_status_row(row.get("cpi"), row.get("cost_variance", 0), row.get("planned_cost", 0))


def summarize_by_project(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Roll up line-level metrics to project level."""
    grouped = (
        metrics_df.groupby(["project_id", "project_name"], as_index=False)
        .agg(
            etc_amount=("etc_amount", "sum"),
            actual_amount=("actual_amount", "sum"),
            planned_cost=("planned_cost", "sum"),
            earned_value=("earned_value", "sum"),
            cost_variance=("cost_variance", "sum"),
        )
    )

    grouped["cpi"] = grouped.apply(
        lambda row: row["earned_value"] / row["actual_amount"]
        if row["actual_amount"] > 0
        else None,
        axis=1,
    )
    grouped["budget_status"] = grouped.apply(
        lambda row: _budget_status_row(row["cpi"], row["cost_variance"], row["planned_cost"]),
        axis=1,
    )
    grouped["performance_status"] = grouped["budget_status"]
    grouped["variance_pct"] = grouped.apply(
        lambda row: (row["cost_variance"] / row["earned_value"] * 100)
        if row["earned_value"] > 0
        else 0,
        axis=1,
    )

    return grouped.sort_values("project_name").reset_index(drop=True)


def get_kpi_summary(metrics_df: pd.DataFrame) -> dict:
    """Return top-level KPI values for the dashboard."""
    total_etc = metrics_df["etc_amount"].sum()
    total_actual = metrics_df["actual_amount"].sum()
    total_ev = metrics_df["earned_value"].sum()
    total_variance = metrics_df["cost_variance"].sum()
    overall_cpi = total_ev / total_actual if total_actual > 0 else 0

    status_counts = metrics_df["budget_status"].value_counts().to_dict() if "budget_status" in metrics_df.columns else {}

    return {
        "total_etc": round(total_etc, 2),
        "total_actual": round(total_actual, 2),
        "total_earned_value": round(total_ev, 2),
        "total_cost_variance": round(total_variance, 2),
        "overall_cpi": round(overall_cpi, 3),
        "project_count": metrics_df["project_id"].nunique(),
        "line_count": len(metrics_df),
        "under_budget": status_counts.get("Under Budget", 0),
        "on_budget": status_counts.get("On Budget", 0),
        "over_budget": status_counts.get("Over Budget", 0),
    }
