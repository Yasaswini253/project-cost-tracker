"""Risk badges, budget health, project ranking, and savings analysis."""

from __future__ import annotations

import pandas as pd


def get_risk_from_cpi(cpi: float | None) -> tuple[str, str]:
    """Return (risk_label, emoji_badge) from CPI."""
    if cpi is None:
        return "Unknown", "⚪"
    if cpi > 1.0:
        return "Low", "🟢"
    if cpi >= 0.9:
        return "Medium", "🟡"
    return "High", "🔴"


def enrich_project_risk(project_summary: pd.DataFrame, health: pd.DataFrame) -> pd.DataFrame:
    """Add risk badge, budget health %, and expected loss per project."""
    merged = project_summary.merge(
        health[["project_id", "health_score"]], on="project_id", how="left"
    )
    rows = []
    for _, row in merged.iterrows():
        cpi = row["cpi"]
        risk, badge = get_risk_from_cpi(cpi)
        budget_health = row.get("health_score", min(100, (cpi or 1) * 100))
        predicted_final = row["actual_amount"] + row["etc_amount"]
        expected_loss = max(0, predicted_final - row["planned_cost"])

        rows.append({
            **row.to_dict(),
            "risk_level": risk,
            "risk_badge": badge,
            "budget_health_pct": round(budget_health, 0),
            "expected_loss": round(expected_loss, 2),
            "predicted_final_cost": round(predicted_final, 2),
        })
    return pd.DataFrame(rows)


def rank_projects(project_risk: pd.DataFrame) -> pd.DataFrame:
    """Rank projects from best to worst by CPI."""
    ranked = project_risk.copy()
    ranked = ranked.sort_values("cpi", ascending=False, na_position="last")
    ranked["rank"] = range(1, len(ranked) + 1)
    ranked["status"] = ranked["budget_status"].fillna("On Budget")
    return ranked[["rank", "project_name", "cpi", "budget_status", "risk_badge", "risk_level", "budget_health_pct", "expected_loss"]]


def calculate_potential_savings(
    project_summary: pd.DataFrame,
    duplicates: pd.DataFrame,
    vendors: pd.DataFrame,
) -> dict:
    """Estimate potential savings opportunities."""
    overtime_saving = project_summary.loc[
        project_summary["budget_status"] == "Over Budget", "actual_amount"
    ].sum() * 0.08

    supplier_saving = 0.0
    if not vendors.empty and "cost_increase" in vendors.columns:
        supplier_saving = vendors["cost_increase"].sum() * 0.15

    duplicate_saving = duplicates["potential_loss"].sum() if not duplicates.empty else 0

    total = overtime_saving + supplier_saving + duplicate_saving
    return {
        "total_potential_savings": round(total, 2),
        "overtime_saving": round(overtime_saving, 2),
        "supplier_saving": round(supplier_saving, 2),
        "duplicate_saving": round(duplicate_saving, 2),
    }


def get_department_costs(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Department/phase-wise cost breakdown ranked by spending."""
    dept_col = "department" if "department" in metrics_df.columns else "cost_element"
    grouped = (
        metrics_df.groupby(dept_col, as_index=False)
        .agg(actual_amount=("actual_amount", "sum"), planned_cost=("planned_cost", "sum"))
        .sort_values("actual_amount", ascending=False)
    )
    grouped = grouped.rename(columns={dept_col: "department"})
    grouped["variance"] = grouped["planned_cost"] - grouped["actual_amount"]
    grouped["rank"] = range(1, len(grouped) + 1)
    return grouped


def get_cost_distribution(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Cost distribution by department/phase for pie chart."""
    dept = get_department_costs(metrics_df)
    total = dept["actual_amount"].sum()
    dept["percentage"] = (dept["actual_amount"] / total * 100).round(1) if total > 0 else 0
    return dept
