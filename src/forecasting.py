"""Cost trend forecasting using ARIMA / exponential smoothing on weekly costs."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def period_sort_key(period: str) -> tuple:
    """Sort Week-1, Week-2, ... Week-12 numerically (not alphabetically)."""
    nums = re.findall(r"\d+", str(period))
    if nums:
        return (0, int(nums[0]), str(period))
    return (1, 0, str(period))


def sort_by_period(df: pd.DataFrame, col: str = "period") -> pd.DataFrame:
    out = df.copy()
    out["_sort_key"] = out[col].map(period_sort_key)
    return out.sort_values("_sort_key").drop(columns="_sort_key")


def _forecast_series(values: list[float], steps: int = 3) -> tuple[list[float], str]:
    """Forecast future **weekly** costs (same unit as historical series)."""
    series = np.array(values, dtype=float)
    if len(series) == 0:
        return [0.0] * steps, "No data"

    mean_val = float(np.mean(series))
    std_val = float(np.std(series)) if len(series) > 1 else mean_val * 0.1
    lower = max(0.0, mean_val - 2 * std_val)
    upper = mean_val + 2 * std_val

    def _bound(forecast: list[float]) -> list[float]:
        return [float(np.clip(v, lower, upper)) for v in forecast]

    if len(series) < 3:
        step = series[-1] - series[-2] if len(series) > 1 else series[-1] * 0.05
        forecast = [max(0.0, series[-1] + step * (i + 1)) for i in range(steps)]
        return _bound(forecast), "Trend average"

    try:
        from statsmodels.tsa.holtwinters import SimpleExpSmoothing

        model = SimpleExpSmoothing(series, initialization_method="estimated").fit()
        forecast = _bound(model.forecast(steps).tolist())
        return forecast, "Exponential Smoothing"
    except Exception:
        pass

    try:
        from statsmodels.tsa.arima.model import ARIMA

        model = ARIMA(series, order=(1, 0, 1))
        fitted = model.fit()
        forecast = _bound(fitted.forecast(steps=steps).tolist())
        return forecast, "ARIMA(1,0,1) weekly"
    except Exception:
        pass

    slope = np.polyfit(np.arange(len(series)), series, 1)[0]
    forecast = [max(0.0, series[-1] + slope * (i + 1)) for i in range(steps)]
    return _bound(forecast), "Linear fallback"


def build_cost_trend_forecast(metrics_df: pd.DataFrame) -> go.Figure:
    """Forecast weekly actual cost — same metric as historical series (not cumulative)."""
    period_df = metrics_df[metrics_df["period"] != "Overall"].copy()

    if period_df.empty:
        periods = ["Current"]
        budget = [metrics_df["planned_cost"].sum()]
        actual_plot = [metrics_df["actual_amount"].sum()]
        predicted = [metrics_df["actual_amount"].sum()]
        model_used = "Single period"
    else:
        grouped = sort_by_period(
            period_df.groupby("period", as_index=False).agg(
                planned_cost=("planned_cost", "sum"),
                actual_amount=("actual_amount", "sum"),
            ),
            "period",
        )

        periods = grouped["period"].tolist()
        budget = grouped["planned_cost"].tolist()
        actual = grouped["actual_amount"].tolist()

        future_steps = 3
        future_weekly, model_used = _forecast_series(actual, future_steps)
        future_periods = [f"Forecast +{i}" for i in range(1, future_steps + 1)]

        periods = periods + future_periods
        budget = budget + [budget[-1]] * future_steps
        actual_plot = actual + [None] * future_steps
        predicted = [None] * len(actual) + future_weekly

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=periods, y=budget, mode="lines+markers", name="Weekly Budget", line=dict(dash="dash", color="#3498db")))
    fig.add_trace(go.Scatter(x=periods, y=actual_plot, mode="lines+markers", name="Weekly Actual", line=dict(color="#e74c3c")))
    fig.add_trace(go.Scatter(x=periods, y=predicted, mode="lines+markers", name="Predicted Weekly", line=dict(dash="dot", color="#9b59b6")))
    fig.update_layout(
        title=f"AI Cost Trend Forecast – weekly spend ({model_used})",
        xaxis_title="Week / Period",
        yaxis_title="Weekly Cost (₹)",
        height=450,
    )
    return fig


def build_weekly_trend_chart(actual_df: pd.DataFrame, metrics_df: pd.DataFrame) -> go.Figure:
    """Plot weekly actual cost trend with numeric week ordering."""
    if "period" in actual_df.columns and (actual_df["period"] != "Overall").any():
        trend = sort_by_period(
            actual_df[actual_df["period"] != "Overall"].groupby("period", as_index=False).agg(
                actual_amount=("actual_amount", "sum")
            ),
            "period",
        )
        budget_line = metrics_df["planned_cost"].sum() / max(len(trend), 1)
        trend["budget"] = budget_line
    else:
        trend = pd.DataFrame({
            "period": ["Week 1"],
            "actual_amount": [metrics_df["actual_amount"].sum()],
            "budget": [metrics_df["planned_cost"].sum()],
        })

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["actual_amount"], mode="lines+markers", name="Weekly Actual", line=dict(width=3, color="#e74c3c")))
    fig.add_trace(go.Scatter(x=trend["period"], y=trend["budget"], mode="lines", name="Weekly Budget Baseline", line=dict(dash="dash", color="#3498db")))
    fig.update_layout(title="Weekly Spending Trend – Is spending accelerating?", xaxis_title="Week", yaxis_title="Weekly Cost (₹)", height=420)
    return fig
