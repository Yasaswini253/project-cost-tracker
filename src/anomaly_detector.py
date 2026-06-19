"""Detect unusual patterns using Isolation Forest (primary) with data-driven explanations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


FEATURE_COLS = [
    "etc_amount",
    "actual_amount",
    "planned_cost",
    "earned_value",
    "cost_variance",
    "cpi",
    "variance_pct",
    "etc_to_actual_ratio",
]


def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    features = df.copy()
    for col in FEATURE_COLS:
        if col not in features.columns:
            features[col] = 0
    features[FEATURE_COLS] = features[FEATURE_COLS].fillna(0).replace([np.inf, -np.inf], 0)
    return features


def _explain_anomaly(row: pd.Series, z_scores: dict[str, float]) -> list[str]:
    """Build explanation from strongest deviations in this row."""
    reasons: list[str] = []
    ranked = sorted(z_scores.items(), key=lambda x: abs(x[1]), reverse=True)

    for feature, z in ranked[:3]:
        if abs(z) < 1.5:
            continue
        if feature == "actual_amount" and z > 0:
            reasons.append(f"Actual spend unusually high (z={z:.1f})")
        elif feature == "etc_amount" and z > 0:
            reasons.append(f"ETC forecast spike detected (z={z:.1f})")
        elif feature == "cpi" and z < 0:
            reasons.append(f"CPI below normal range ({row.get('cpi', 0):.2f})")
        elif feature == "cost_variance" and z < 0:
            reasons.append(f"Negative cost variance outlier (z={z:.1f})")
        elif feature == "variance_pct" and z > 0:
            reasons.append(f"Variance % exceeds peer pattern ({row.get('variance_pct', 0):.1f}%)")

    if not reasons:
        reasons.append("Isolation Forest flagged as multivariate outlier")
    return reasons


def detect_anomalies(metrics_df: pd.DataFrame, contamination: float | None = None) -> pd.DataFrame:
    """
    Primary detection: Isolation Forest on scaled multivariate cost features.
    Explanations are derived from standardized feature deviations.
    """
    df = _prepare_features(metrics_df).reset_index(drop=True)
    n = len(df)

    if n < 3:
        df["anomaly_score"] = 0.0
        df["is_anomaly"] = False
        df["anomaly_reasons"] = "Insufficient data for ML detection"
        df["detection_method"] = "N/A"
        return df

    x_raw = df[FEATURE_COLS].values
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x_raw)

    auto_contamination = min(0.25, max(0.05, 1 / np.sqrt(n)))
    cont = contamination if contamination is not None else auto_contamination

    model = IsolationForest(
        n_estimators=200,
        contamination=cont,
        random_state=42,
        n_jobs=-1,
    )
    preds = model.fit_predict(x_scaled)
    scores = -model.decision_function(x_scaled)

    z_matrix = (x_raw - x_raw.mean(axis=0)) / (x_raw.std(axis=0) + 1e-9)
    reasons_list: list[str] = []

    for i in range(n):
        if preds[i] == -1:
            z_scores = {FEATURE_COLS[j]: float(z_matrix[i, j]) for j in range(len(FEATURE_COLS))}
            reasons_list.append("; ".join(_explain_anomaly(df.iloc[i], z_scores)))
        else:
            reasons_list.append("Normal")

    df["anomaly_score"] = scores
    df["is_anomaly"] = preds == -1
    df["anomaly_reasons"] = reasons_list
    df["detection_method"] = "Isolation Forest (scaled)"

    return df.sort_values(["is_anomaly", "anomaly_score"], ascending=[False, False]).reset_index(drop=True)


def get_anomaly_summary(anomaly_df: pd.DataFrame) -> dict[str, int | float]:
    anomaly_count = int(anomaly_df["is_anomaly"].sum())
    total = len(anomaly_df)
    return {
        "anomaly_count": anomaly_count,
        "normal_count": total - anomaly_count,
        "anomaly_rate_pct": round(anomaly_count / total * 100, 1) if total else 0,
    }
