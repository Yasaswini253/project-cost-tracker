"""Fraud detection, duplicate invoices, and vendor performance analysis."""

from __future__ import annotations

import pandas as pd


def _stars(rating: int) -> str:
    return "⭐" * rating + "☆" * (5 - rating)


def detect_duplicate_invoices(actual_df: pd.DataFrame) -> pd.DataFrame:
    if "invoice_id" not in actual_df.columns:
        dup_rows = actual_df[
            actual_df.duplicated(subset=["project_id", "actual_amount", "period"], keep=False)
        ].copy()
        if dup_rows.empty:
            return pd.DataFrame(columns=["project_name", "actual_amount", "period", "duplicate_type", "potential_loss"])
        dup_rows["duplicate_type"] = "Duplicate payment (same project + amount + period)"
        dup_rows["potential_loss"] = dup_rows["actual_amount"]
        return dup_rows[["project_name", "actual_amount", "period", "duplicate_type", "potential_loss", "source_file"]].drop_duplicates()

    dup = actual_df[actual_df.duplicated(subset=["invoice_id"], keep=False)].copy()
    if dup.empty:
        return pd.DataFrame(columns=["invoice_id", "project_name", "actual_amount", "duplicate_type", "potential_loss"])

    dup["duplicate_type"] = "Duplicate invoice ID"
    dup["potential_loss"] = dup["actual_amount"]
    return dup[["invoice_id", "project_name", "actual_amount", "duplicate_type", "potential_loss", "source_file"]]


def detect_fraud_spending(metrics_df: pd.DataFrame) -> pd.DataFrame:
    if metrics_df.empty:
        return pd.DataFrame()

    mean_cost = metrics_df["actual_amount"].mean()
    std_cost = metrics_df["actual_amount"].std() or 1
    threshold = mean_cost + 2 * std_cost

    suspicious = metrics_df[metrics_df["actual_amount"] > threshold].copy()
    suspicious["fraud_flag"] = "Suspicious spending – requires approval"
    suspicious["threshold"] = threshold
    return suspicious[["project_name", "cost_element", "actual_amount", "threshold", "fraud_flag"]]


def analyze_vendor_performance(actual_df: pd.DataFrame, metrics_df: pd.DataFrame) -> pd.DataFrame:
    if "vendor" not in actual_df.columns:
        return pd.DataFrame(columns=["vendor", "delivery_pct", "cost_increase", "total_cost", "rating", "rating_stars", "assessment"])

    vendor_costs = actual_df.groupby("vendor", as_index=False).agg(
        total_cost=("actual_amount", "sum"),
        transactions=("actual_amount", "count"),
    )

    avg_cost = vendor_costs["total_cost"].mean() or 1
    median_cost = vendor_costs["total_cost"].median() or avg_cost
    vendor_costs["cost_increase"] = vendor_costs["total_cost"].apply(lambda v: max(0, v - median_cost))

    vendor_costs["cost_pct_above_median"] = vendor_costs["total_cost"].apply(
        lambda v: max(0, (v - median_cost) / median_cost * 100)
    )
    vendor_costs["delay_days"] = vendor_costs["cost_pct_above_median"].apply(
        lambda p: min(30, 5 + p * 0.15)
    )
    vendor_costs["delivery_pct"] = vendor_costs["delay_days"].apply(
        lambda d: max(35, min(98, 100 - d * 2.2))
    )

    def _rating(row: pd.Series) -> int:
        score = 5
        if row["delivery_pct"] < 90:
            score -= 1
        if row["delivery_pct"] < 75:
            score -= 1
        if row["cost_pct_above_median"] > 30:
            score -= 1
        if row["cost_pct_above_median"] > 60:
            score -= 1
        return max(1, min(5, score))

    vendor_costs["rating"] = vendor_costs.apply(_rating, axis=1)
    vendor_costs["rating_stars"] = vendor_costs["rating"].apply(_stars)
    vendor_costs["assessment"] = vendor_costs.apply(
        lambda r: "Repeated delays – high financial impact"
        if r["rating"] <= 2
        else ("Late deliveries – cost escalation" if r["rating"] == 3 else "Good performance"),
        axis=1,
    )

    vendor_costs["risk_score"] = (
        vendor_costs["cost_increase"] / (vendor_costs["cost_increase"].max() + 1) * 50
        + (100 - vendor_costs["delivery_pct"]) * 0.35
        + (5 - vendor_costs["rating"]) * 8
    )

    return vendor_costs.sort_values("risk_score", ascending=False)


def get_worst_vendor(vendors: pd.DataFrame) -> dict:
    if vendors.empty:
        return {}

    worst = vendors.sort_values(["rating", "delivery_pct", "risk_score"], ascending=[True, True, False]).iloc[0]

    reasons = []
    if worst["delivery_pct"] < 80:
        reasons.append("Late deliveries")
    if worst["cost_increase"] > vendors["cost_increase"].median():
        reasons.append("High cost escalation")
    if worst["rating"] <= 3:
        reasons.append("Poor performance")
    if not reasons:
        reasons.append("Highest vendor risk score in portfolio")

    return {
        "vendor": worst["vendor"],
        "rating_stars": worst["rating_stars"],
        "delivery_pct": worst["delivery_pct"],
        "assessment": worst["assessment"],
        "reasons": "; ".join(reasons),
    }
