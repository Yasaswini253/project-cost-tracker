"""Generate live budget alerts and notifications."""

from __future__ import annotations

import pandas as pd


def generate_alerts(
    project_summary: pd.DataFrame,
    health: pd.DataFrame,
    predictions: pd.DataFrame,
    burn_rate: pd.DataFrame,
    duplicates: pd.DataFrame,
    fraud: pd.DataFrame,
    vendors: pd.DataFrame,
    kpis: dict,
) -> list[dict]:
    """Build dynamic alert list from uploaded data."""
    alerts: list[dict] = []

    for _, row in project_summary.iterrows():
        cpi = row.get("cpi")
        if cpi is not None and cpi < 0.9:
            pct = abs(row.get("variance_pct", 0))
            alerts.append({
                "badge": "🔴",
                "level": "critical",
                "message": f"Budget exceeded by {pct:.0f}% on {row['project_name']} (CPI {cpi:.2f})",
            })

    for _, row in vendors.iterrows():
        if row.get("rating", 5) <= 2:
            alerts.append({
                "badge": "🟠",
                "level": "warning",
                "message": f"Vendor {row['vendor']} delayed – delivery {row['delivery_pct']:.0f}%",
            })

    if kpis.get("overall_cpi", 1) < 0.9:
        alerts.append({
            "badge": "🟡",
            "level": "warning",
            "message": f"CPI dropped below 0.90 – current CPI {kpis['overall_cpi']:.2f}",
        })

    if not duplicates.empty:
        loss = duplicates["potential_loss"].sum()
        alerts.append({
            "badge": "🟢",
            "level": "info",
            "message": f"Duplicate invoice detected – potential recovery ₹{loss:,.0f}",
        })

    if not burn_rate.empty and "alert" in burn_rate.columns:
        for _, row in burn_rate[burn_rate["alert"].str.contains("High risk", na=False)].iterrows():
            alerts.append({
                "badge": "🟡",
                "level": "warning",
                "message": f"Burn rate increased {row['burn_rate_change_pct']:.0f}% in {row['period']}",
            })

    for _, row in fraud.iterrows():
        alerts.append({
            "badge": "🔴",
            "level": "critical",
            "message": f"Suspicious spending on {row['project_name']} – ₹{row['actual_amount']:,.0f}",
        })

    for _, row in predictions[predictions["overrun_probability_pct"] > 75].head(3).iterrows():
        alerts.append({
            "badge": "🟠",
            "level": "warning",
            "message": f"{row['project_name']}: {row['overrun_probability_pct']:.0f}% overrun risk",
        })

    for _, row in health[health["overall_status"] == "Critical"].iterrows():
        alerts.append({
            "badge": "🔴",
            "level": "critical",
            "message": f"{row['project_name']} health score {row['health_score']}/100 – needs management review",
        })

    return alerts[:25]
