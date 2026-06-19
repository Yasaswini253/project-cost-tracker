"""AI-powered project cost intelligence: ML predictions, health score, root cause, recommendations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "actual_ratio",
    "etc_ratio",
    "cpi",
    "variance_pct",
    "variance_ratio",
    "anomaly_count",
    "spend_velocity",
]

CAUSE_LABELS = {
    "actual_ratio": "Actual spend exceeds planned baseline",
    "etc_ratio": "Remaining ETC disproportionate to plan",
    "cpi": "Cost efficiency deterioration (low CPI)",
    "variance_pct": "Earned value vs actual mismatch",
    "variance_ratio": "Negative cost variance pressure",
    "anomaly_count": "Repeated AI-detected cost outliers",
    "spend_velocity": "Accelerating weekly spend pattern",
}

ACTION_MAP = {
    "actual_ratio": "Reduce overtime and freeze discretionary spend",
    "etc_ratio": "Re-baseline ETC with engineering leads",
    "cpi": "Review procurement contracts and material pricing",
    "variance_pct": "Investigate scope creep and rework drivers",
    "variance_ratio": "Reallocate budget from lower-priority tasks",
    "anomaly_count": "Audit flagged cost lines with finance team",
    "spend_velocity": "Slow burn rate on non-critical activities",
    "vendor": "Replace or renegotiate underperforming supplier",
    "duplicate": "Recover duplicate invoice payments immediately",
}


def _build_ml_features(project_summary: pd.DataFrame, metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Build per-project feature matrix for ML models."""
    anomaly_counts = (
        metrics_df.groupby("project_id")["is_anomaly"].sum()
        if "is_anomaly" in metrics_df.columns
        else pd.Series(0, index=project_summary["project_id"])
    )

    rows = []
    for _, row in project_summary.iterrows():
        pid = row["project_id"]
        planned = max(row["planned_cost"], 1)
        proj_metrics = metrics_df[metrics_df["project_id"] == pid]
        period_data = proj_metrics[proj_metrics["period"] != "Overall"].sort_values("period")

        velocity = 0.0
        if len(period_data) >= 2:
            spends = period_data["actual_amount"].values
            velocity = float(np.mean(np.diff(spends) / (spends[:-1] + 1)))

        rows.append({
            "project_id": pid,
            "project_name": row["project_name"],
            "actual_ratio": row["actual_amount"] / planned,
            "etc_ratio": row["etc_amount"] / planned,
            "cpi": row["cpi"] if row["cpi"] is not None else 1.0,
            "variance_pct": abs(row.get("variance_pct", 0)),
            "variance_ratio": row["cost_variance"] / planned,
            "anomaly_count": float(anomaly_counts.get(pid, 0)),
            "spend_velocity": velocity,
            "planned_cost": row["planned_cost"],
            "actual_amount": row["actual_amount"],
            "etc_amount": row["etc_amount"],
            "budget_status": row.get("budget_status", "On Budget"),
        })

    return pd.DataFrame(rows)


def _build_overrun_labels(features: pd.DataFrame) -> np.ndarray:
    """Build writable binary labels and ensure both classes exist."""
    mask = (
        (features["actual_amount"] + features["etc_amount"] > features["planned_cost"] * 1.02)
        | (features["cpi"] < 0.95)
        | (features["budget_status"].eq("Over Budget"))
        | (features["variance_ratio"] < -0.05)
    )
    y = np.array(mask.astype(int).tolist(), dtype=np.int64)

    if y.sum() == 0:
        idx = int(np.argmax(features["actual_ratio"].to_numpy()))
        y = y.copy()
        y[idx] = 1
    elif y.sum() == len(y):
        idx = int(np.argmin(features["actual_ratio"].to_numpy()))
        y = y.copy()
        y[idx] = 0

    return y


def _train_overrun_model(features: pd.DataFrame) -> tuple[RandomForestClassifier, StandardScaler]:
    """Train Random Forest classifier for budget overrun probability."""
    x = features[FEATURE_NAMES].fillna(0).replace([np.inf, -np.inf], 0).values
    y = _build_overrun_labels(features)

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(x_scaled, y)
    return model, scaler


def _feature_importance_causes(model: RandomForestClassifier, top_n: int = 3) -> list[tuple[str, float]]:
    imp = model.feature_importances_
    ranked = sorted(zip(FEATURE_NAMES, imp), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]


def _causes_for_project(model: RandomForestClassifier, scaler: StandardScaler, row: pd.Series, top_n: int = 3) -> tuple[str, str]:
    """Root cause from feature importance weighted by this project's deviation."""
    x = row[FEATURE_NAMES].fillna(0).replace([np.inf, -np.inf], 0).values.reshape(1, -1)
    x_scaled = scaler.transform(x)
    global_rank = _feature_importance_causes(model, top_n=len(FEATURE_NAMES))

    z = (x[0] - scaler.mean_) / (scaler.scale_ + 1e-9)
    weighted = []
    for fname, g_imp in global_rank:
        idx = FEATURE_NAMES.index(fname)
        weighted.append((fname, g_imp * abs(z[idx])))

    weighted.sort(key=lambda x: x[1], reverse=True)
    top = weighted[:top_n]

    root = "; ".join(CAUSE_LABELS.get(f, f) for f, _ in top)
    detail_parts = []
    for fname, _ in top:
        label = CAUSE_LABELS.get(fname, fname)
        val = row[fname]
        if fname == "cpi":
            detail_parts.append(f"{label} (CPI={val:.2f})")
        elif fname in {"actual_ratio", "etc_ratio", "variance_ratio"}:
            detail_parts.append(f"{label} (ratio={val:.2f})")
        elif fname == "spend_velocity":
            detail_parts.append(f"{label} (velocity={val:.2f})")
        else:
            detail_parts.append(f"{label} ({val:.1f})")

    return root, "; ".join(detail_parts)


def predict_cost_overruns(
    project_summary: pd.DataFrame,
    metrics_df: pd.DataFrame,
    root_causes: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Predict overrun probability using Random Forest on project cost features."""
    features = _build_ml_features(project_summary, metrics_df)
    model, scaler = _train_overrun_model(features)

    x = features[FEATURE_NAMES].fillna(0).replace([np.inf, -np.inf], 0).values
    x_scaled = scaler.transform(x)

    if len(model.classes_) < 2:
        probas = np.clip(features["actual_ratio"].values * 40 + (1 - features["cpi"].values) * 50, 5, 95)
        confidences = 100 - np.abs(probas - 50) * 0.6
    else:
        proba_matrix = model.predict_proba(x_scaled)
        pos_idx = list(model.classes_).index(1) if 1 in model.classes_ else -1
        probas = proba_matrix[:, pos_idx] * 100
        confidences = np.max(proba_matrix, axis=1) * 100

    rows = []
    for idx, (_, row) in enumerate(features.iterrows()):
        estimated_final = row["actual_amount"] + row["etc_amount"]
        _, ai_explanation = _causes_for_project(model, scaler, row)

        rows.append({
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "estimated_final_cost": round(estimated_final, 2),
            "planned_cost": round(row["planned_cost"], 2),
            "overrun_probability_pct": round(float(probas[idx]), 1),
            "model_confidence_pct": round(float(confidences[idx]), 1),
            "predicted_overrun": probas[idx] >= 50,
            "ai_explanation": ai_explanation,
            "model": "Random Forest Classifier",
        })

    return pd.DataFrame(rows).sort_values("overrun_probability_pct", ascending=False)


def calculate_health_scores(project_summary: pd.DataFrame, metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Compute health score using Random Forest regressor trained on cost performance signals."""
    features = _build_ml_features(project_summary, metrics_df)

    x = features[FEATURE_NAMES].fillna(0).replace([np.inf, -np.inf], 0).values
    y = np.clip(
        100
        - features["variance_pct"] * 0.8
        - (1 - features["cpi"].clip(0, 1.5)) * 35
        - features["anomaly_count"] * 8
        - features["spend_velocity"].clip(0, 2) * 15,
        0,
        100,
    ).values

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    reg = RandomForestRegressor(n_estimators=150, max_depth=5, random_state=42)
    reg.fit(x_scaled, y)
    predicted_health = reg.predict(x_scaled)

    rows = []
    for i, row in features.iterrows():
        health = round(float(predicted_health[i]), 0)
        budget_score = min(100, max(0, row["cpi"] * 100))
        variance_score = max(0, 100 - row["variance_pct"] * 2)

        overall = _health_status(health)

        rows.append({
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "health_score": health,
            "budget_risk": _risk_label(100 - budget_score),
            "schedule_risk": _risk_label(row["variance_pct"]),
            "resource_risk": _risk_label(row["anomaly_count"] * 15),
            "overall_status": overall,
            "budget_status": row.get("budget_status", "On Budget"),
            "model": "Random Forest Regressor",
        })

    return pd.DataFrame(rows).sort_values("health_score")


def _health_status(score: float) -> str:
    if score > 80:
        return "Healthy"
    if score >= 60:
        return "Needs Attention"
    if score >= 40:
        return "At Risk"
    return "Critical"


def _risk_label(value: float) -> str:
    if value < 20:
        return "Low"
    if value < 45:
        return "Medium"
    return "High"


def analyze_root_causes(project_summary: pd.DataFrame, metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Root cause analysis using Random Forest feature importance per project."""
    features = _build_ml_features(project_summary, metrics_df)
    model, scaler = _train_overrun_model(features)

    rows = []
    for _, row in features.iterrows():
        root, detail = _causes_for_project(model, scaler, row)
        rows.append({
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "root_causes": root,
            "possible_reasons": detail,
            "analysis_method": "Feature importance (Random Forest)",
        })

    return pd.DataFrame(rows)


def generate_recommendations(
    project_summary: pd.DataFrame,
    metrics_df: pd.DataFrame,
    root_causes: pd.DataFrame,
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Dynamic recommendations ranked by project-specific feature drivers."""
    features = _build_ml_features(project_summary, metrics_df)
    model, scaler = _train_overrun_model(features)

    rows = []
    for _, row in features.iterrows():
        x = row[FEATURE_NAMES].fillna(0).replace([np.inf, -np.inf], 0).values.reshape(1, -1)
        z = (x[0] - scaler.mean_) / (scaler.scale_ + 1e-9)
        global_rank = _feature_importance_causes(model, top_n=len(FEATURE_NAMES))

        scored_actions: list[tuple[float, str]] = []
        for fname, g_imp in global_rank:
            idx = FEATURE_NAMES.index(fname)
            score = g_imp * abs(z[idx])
            action = ACTION_MAP.get(fname)
            if action and score > 0.05:
                scored_actions.append((score, action))

        prob_row = predictions[predictions["project_id"] == row["project_id"]]
        if not prob_row.empty and prob_row.iloc[0]["overrun_probability_pct"] > 70:
            scored_actions.append((0.9, "Escalate to management for immediate cost review"))

        if row["budget_status"] == "Under Budget":
            scored_actions.append((0.2, "Maintain controls and document savings for reuse"))

        scored_actions.sort(key=lambda x: x[0], reverse=True)
        unique_actions = []
        seen = set()
        for _, action in scored_actions:
            if action not in seen:
                unique_actions.append(action)
                seen.add(action)
            if len(unique_actions) >= 5:
                break

        if not unique_actions:
            unique_actions = ["Continue monitoring weekly cost trends"]

        rows.append({
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "recommended_actions": unique_actions,
            "actions_text": "; ".join(unique_actions),
        })

    return pd.DataFrame(rows)


def calculate_burn_rate(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate week-over-week spend acceleration."""
    from src.forecasting import sort_by_period

    period_df = metrics_df[metrics_df["period"] != "Overall"].copy()
    if period_df.empty:
        return pd.DataFrame(columns=["period", "actual_amount", "burn_rate_change_pct", "alert"])

    burn = sort_by_period(
        period_df.groupby("period", as_index=False)["actual_amount"].sum(),
        "period",
    )
    burn["prev_spend"] = burn["actual_amount"].shift(1)
    burn["burn_rate_change_pct"] = burn.apply(
        lambda r: ((r["actual_amount"] - r["prev_spend"]) / r["prev_spend"] * 100)
        if pd.notna(r["prev_spend"]) and r["prev_spend"] > 0
        else 0,
        axis=1,
    )
    burn["alert"] = burn["burn_rate_change_pct"].apply(
        lambda v: "High risk – burn rate increased sharply" if v > 100 else (
            "Warning – burn rate increased" if v > 50 else "Normal"
        )
    )
    return burn


def forecast_completion_cost(metrics_df: pd.DataFrame, project_summary: pd.DataFrame) -> pd.DataFrame:
    """Predict expected final cost with variable confidence per project."""
    from src.forecasting import _forecast_series, sort_by_period

    rows = []
    for _, proj in project_summary.iterrows():
        pid = proj["project_id"]
        proj_data = metrics_df[metrics_df["project_id"] == pid]
        period_data = sort_by_period(proj_data[proj_data["period"] != "Overall"], "period")

        current_cost = proj["actual_amount"]
        etc = proj["etc_amount"]
        simple_forecast = current_cost + etc
        cpi = proj["cpi"] if proj["cpi"] is not None else 1.0
        variance_pct = abs(proj.get("variance_pct", 0))

        if len(period_data) >= 3:
            weekly = period_data["actual_amount"].tolist()
            trend_vals, method = _forecast_series(weekly, 1)
            remaining_weeks = max(1, len(weekly))
            trend_forecast = current_cost + trend_vals[0] * remaining_weeks * 0.5
            volatility = float(period_data["actual_amount"].std() / (period_data["actual_amount"].mean() + 1))
            confidence = round(max(58, min(94, 90 - volatility * 30 - variance_pct * 0.25 - max(0, 1 - cpi) * 25)), 0)
        else:
            trend_forecast = simple_forecast
            method = "ETC + Actual"
            confidence = round(max(55, min(88, 78 - variance_pct * 0.3 - max(0, 1 - cpi) * 20 - (3 - len(period_data)) * 4)), 0)

        expected_final = max(simple_forecast, trend_forecast)
        rows.append({
            "project_id": pid,
            "project_name": proj["project_name"],
            "current_cost": round(current_cost, 2),
            "expected_final_cost": round(expected_final, 2),
            "forecast_confidence_pct": confidence,
            "forecast_method": method,
        })

    return pd.DataFrame(rows)


def generate_weekly_report(kpis: dict, project_summary: pd.DataFrame, health: pd.DataFrame, recommendations: pd.DataFrame) -> str:
    top_risk = health.sort_values("health_score").head(1)
    top_action = recommendations.sort_values("project_name").head(1)

    risk_name = top_risk.iloc[0]["project_name"] if not top_risk.empty else "N/A"
    risk_score = top_risk.iloc[0]["health_score"] if not top_risk.empty else "N/A"
    action = top_action.iloc[0].get("actions_text", "Continue monitoring") if not top_action.empty else "Continue monitoring"

    return f"""## Weekly Project Summary

**Total Cost:** ₹{kpis['total_actual']:,.0f}
**Variance:** ₹{kpis['total_cost_variance']:,.0f}
**CPI:** {kpis['overall_cpi']:.2f}

**Budget Status**
- Under Budget: {kpis.get('under_budget', 0)} items
- On Budget: {kpis.get('on_budget', 0)} items
- Over Budget: {kpis.get('over_budget', 0)} items

**Top Risk:** {risk_name} (Health Score: {risk_score}/100)

**Suggested Action:** {action}

---
*Report generated automatically by AI Cost Intelligence System*
"""


def get_executive_summary(
    project_summary: pd.DataFrame,
    health: pd.DataFrame,
    predictions: pd.DataFrame,
    alerts: list,
    duplicates: pd.DataFrame,
    vendors: pd.DataFrame,
    savings: dict,
    kpis: dict,
) -> dict:
    healthy = (health["overall_status"] == "Healthy").sum()
    needs_attention = (health["overall_status"] == "Needs Attention").sum()
    at_risk = (health["overall_status"] == "At Risk").sum()
    critical = (health["overall_status"] == "Critical").sum()
    predicted_overruns = (predictions["predicted_overrun"] == True).sum()  # noqa: E712

    total_planned = project_summary["planned_cost"].sum()
    total_actual = project_summary["actual_amount"].sum()
    budget_utilization = (total_actual / total_planned * 100) if total_planned > 0 else 0
    total_overspend = max(0, -project_summary["cost_variance"].sum())
    predicted_overrun_amount = predictions.loc[
        predictions["predicted_overrun"], "estimated_final_cost"
    ].sum() - predictions.loc[predictions["predicted_overrun"], "planned_cost"].sum()
    predicted_overrun_amount = max(0, predicted_overrun_amount)

    high_risk_vendors = 0
    if not vendors.empty and "rating" in vendors.columns:
        high_risk_vendors = (vendors["rating"] <= 2).sum()

    return {
        "total_projects": len(project_summary),
        "healthy": int(healthy),
        "needs_attention": int(needs_attention),
        "at_risk": int(at_risk),
        "critical": int(critical),
        "todays_alerts": len(alerts),
        "predicted_overruns": int(predicted_overruns),
        "expected_savings": round(max(0, project_summary.loc[
            project_summary["budget_status"] == "Under Budget", "cost_variance"
        ].sum()), 2),
        "total_variance": round(project_summary["cost_variance"].sum(), 2),
        "budget_utilization_pct": round(budget_utilization, 1),
        "total_overspend": round(total_overspend, 2),
        "high_risk_vendors": int(high_risk_vendors),
        "duplicate_payments": len(duplicates),
        "predicted_cost_overrun": round(predicted_overrun_amount, 2),
        "suggested_savings": round(savings.get("total_potential_savings", 0), 2),
        "overall_cpi": kpis.get("overall_cpi", 0),
    }
