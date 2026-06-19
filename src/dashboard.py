"""Streamlit dashboard for AI Project Cost Intelligence System."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_header() -> None:
    st.title("AI-Powered Predictive Project Cost Intelligence System")
    st.markdown(
        "Upload **multiple ETC & Actual files** — columns like `Task_ID`, `Task_Nam`, `ETC_Cost` "
        "are read automatically. Use **Manual Column Mapping** in the sidebar if your headers differ."
    )


def render_executive_summary_card(exec_summary: dict) -> None:
    st.subheader("Executive Summary")
    st.markdown(
        f"""
        | Metric | Value |
        |--------|-------|
        | Projects Analysed | **{exec_summary['total_projects']}** |
        | Budget Utilization | **{exec_summary['budget_utilization_pct']:.0f}%** |
        | Total Overspend | **₹{exec_summary['total_overspend']:,.0f}** |
        | Healthy Projects | **{exec_summary['healthy']}** |
        | Needs Attention | **{exec_summary.get('needs_attention', 0)}** |
        | At Risk | **{exec_summary['at_risk']}** |
        | Critical Projects | **{exec_summary['critical']}** |
        | High-Risk Vendors | **{exec_summary['high_risk_vendors']}** |
        | Duplicate Payments | **{exec_summary['duplicate_payments']}** |
        | Predicted Cost Overrun | **₹{exec_summary['predicted_cost_overrun']:,.0f}** |
        | Suggested Savings | **₹{exec_summary['suggested_savings']:,.0f}** |
        | Overall CPI | **{exec_summary['overall_cpi']:.2f}** |
        """
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Healthy", exec_summary["healthy"], delta="🟢")
    c2.metric("At Risk", exec_summary["at_risk"] + exec_summary.get("needs_attention", 0), delta="🟡")
    c3.metric("Critical", exec_summary["critical"], delta="🔴")
    c4.metric("Alerts Today", exec_summary["todays_alerts"])


def render_budget_status_badges(kpis: dict) -> None:
    c1, c2, c3 = st.columns(3)
    c1.success(f"🟢 Under Budget: **{kpis.get('under_budget', 0)}**")
    c2.info(f"🔵 On Budget: **{kpis.get('on_budget', 0)}**")
    c3.error(f"🔴 Over Budget: **{kpis.get('over_budget', 0)}**")


def render_kpi_cards(kpis: dict) -> None:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total ETC", f"₹{kpis['total_etc']:,.0f}")
    col2.metric("Total Actual", f"₹{kpis['total_actual']:,.0f}")
    col3.metric("Cost Variance", f"₹{kpis['total_cost_variance']:,.0f}")
    risk, badge = _cpi_risk(kpis["overall_cpi"])
    col4.metric("Overall CPI", f"{kpis['overall_cpi']:.2f}", delta=f"{badge} {risk}")
    col5.metric("Projects", kpis["project_count"])


def _cpi_risk(cpi: float) -> tuple[str, str]:
    if cpi > 1.0:
        return "Low", "🟢"
    if cpi >= 0.9:
        return "Medium", "🟡"
    return "High", "🔴"


def render_project_risk_cards(project_risk) -> None:
    st.subheader("Project Risk Overview")
    st.caption("Expected Loss = Predicted Final Cost − Budget  (Predicted Final Cost = Actual + ETC)")
    cols = st.columns(3)
    for i, (_, row) in enumerate(project_risk.head(9).iterrows()):
        with cols[i % 3]:
            st.markdown(
                f"**{row['project_name']}**\n\n"
                f"Risk: {row['risk_badge']} **{row['risk_level']}**\n\n"
                f"CPI: **{row['cpi']:.2f}**\n\n"
                f"Budget Health: **{row['budget_health_pct']:.0f}%**\n\n"
                f"Expected Loss: **₹{row['expected_loss']:,.0f}**"
            )


def render_health_gauge(health) -> None:
    st.subheader("Project Health Score")
    avg = health["health_score"].mean()
    if avg > 80:
        status = "🟢 Healthy"
    elif avg >= 60:
        status = "🟡 Needs Attention"
    elif avg >= 40:
        status = "🟠 At Risk"
    else:
        status = "🔴 Critical"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg,
        title={"text": f"Portfolio Health – {status}"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#2ecc71" if avg > 80 else ("#f39c12" if avg >= 60 else ("#e67e22" if avg >= 40 else "#e74c3c"))},
            "steps": [
                {"range": [0, 40], "color": "#fadbd8"},
                {"range": [40, 60], "color": "#fdebd0"},
                {"range": [60, 80], "color": "#fef9e7"},
                {"range": [80, 100], "color": "#d5f5e3"},
            ],
        },
    ))
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)


def render_potential_savings(savings: dict) -> None:
    st.subheader("Potential Savings")
    st.metric("Total Potential Savings", f"₹{savings['total_potential_savings']:,.0f}")
    st.markdown(
        f"""
        - ✔ By reducing overtime: **₹{savings['overtime_saving']:,.0f}**
        - ✔ By changing supplier: **₹{savings['supplier_saving']:,.0f}**
        - ✔ By avoiding duplicate invoices: **₹{savings['duplicate_saving']:,.0f}**
        """
    )


def render_project_ranking(rankings) -> None:
    st.subheader("Project Ranking (Best → Worst)")
    st.dataframe(
        rankings.rename(columns={
            "rank": "Rank", "project_name": "Project", "cpi": "CPI",
            "budget_status": "Status", "risk_badge": "Risk", "budget_health_pct": "Health %",
            "expected_loss": "Expected Loss",
        }),
        hide_index=True,
        use_container_width=True,
    )


def render_alerts(alerts: list[dict]) -> None:
    st.subheader("Real-Time Alerts")
    if not alerts:
        st.success("🟢 No alerts – all projects within normal parameters.")
        return
    for alert in alerts[:10]:
        msg = f"{alert.get('badge', '⚪')} {alert['message']}"
        if alert["level"] == "critical":
            st.error(msg)
        elif alert["level"] == "warning":
            st.warning(msg)
        else:
            st.info(msg)


def render_charts(project_summary, metrics_df, anomaly_df, forecast_fig, trend_fig, burn_rate, cost_dist, dept_costs):
    tabs = st.tabs([
        "Trend Analysis", "Planned vs Actual", "Cost Distribution",
        "Department Costs", "CPI & Risk", "Forecast", "Anomalies", "Burn Rate",
    ])

    with tabs[0]:
        st.plotly_chart(trend_fig, use_container_width=True)
        st.caption("Rising actual line vs flat budget = spending is accelerating.")

    with tabs[1]:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Planned", x=project_summary["project_name"], y=project_summary["planned_cost"]))
        fig.add_trace(go.Bar(name="Actual", x=project_summary["project_name"], y=project_summary["actual_amount"]))
        fig.add_trace(go.Bar(name="ETC", x=project_summary["project_name"], y=project_summary["etc_amount"]))
        fig.update_layout(barmode="group", title="Planned vs Actual vs ETC", height=420)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        if not cost_dist.empty:
            fig = px.pie(cost_dist, names="department", values="actual_amount", title="Cost Distribution by Department/Phase", hole=0.35)
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(cost_dist[["department", "actual_amount", "percentage"]], hide_index=True)

    with tabs[3]:
        if not dept_costs.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Budget", x=dept_costs["department"], y=dept_costs["planned_cost"], marker_color="#3498db"))
            fig.add_trace(go.Bar(name="Actual", x=dept_costs["department"], y=dept_costs["actual_amount"], marker_color="#e74c3c"))
            fig.add_trace(go.Bar(name="Variance", x=dept_costs["department"], y=dept_costs["variance"], marker_color="#2ecc71"))
            fig.update_layout(barmode="group", title="Department-wise Cost: Budget vs Actual vs Variance", height=420)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(dept_costs[["department", "planned_cost", "actual_amount", "variance"]], hide_index=True)

    with tabs[4]:
        fig = px.bar(project_summary, x="project_name", y="cpi", color="budget_status",
                     title="CPI by Project with Budget Status",
                     color_discrete_map={"Under Budget": "#2ecc71", "On Budget": "#3498db", "Over Budget": "#e74c3c"})
        fig.add_hline(y=1.0, line_dash="dash")
        fig.add_hline(y=0.9, line_dash="dot", annotation_text="High Risk <0.9")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[5]:
        st.plotly_chart(forecast_fig, use_container_width=True)

    with tabs[6]:
        anomalies = anomaly_df[anomaly_df["is_anomaly"]]
        st.dataframe(anomalies[["project_name", "cpi", "cost_variance", "anomaly_reasons"]], hide_index=True) if not anomalies.empty else st.success("No anomalies.")

    with tabs[7]:
        if burn_rate is not None and not burn_rate.empty:
            st.plotly_chart(px.bar(burn_rate, x="period", y="actual_amount", color="alert", title="Budget Burn Rate"), use_container_width=True)
        else:
            st.info("Add Week/Period column for burn rate analysis.")


def render_timeline(timeline_df, gantt_fig) -> None:
    st.subheader("Project Timeline")
    st.dataframe(
        timeline_df.rename(columns={
            "project_name": "Task", "cost_element": "Phase",
            "task_status": "Status", "actual_amount": "Actual", "planned_cost": "Planned",
        }),
        hide_index=True,
        use_container_width=True,
    )
    st.plotly_chart(gantt_fig, use_container_width=True)


def render_intelligence_sections(predictions, health, root_causes, recommendations, forecasts, duplicates, fraud, vendors, worst_vendor, weekly_report):
    st.subheader("AI Intelligence")
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "Overrun Prediction", "Health Score", "Root Cause", "Recommendations",
        "Fraud & Duplicates", "Vendor Dashboard", "Weekly Report",
    ])

    with t1:
        for _, row in predictions.head(8).iterrows():
            conf = row.get("model_confidence_pct", 0)
            st.markdown(
                f"**{row['project_name']}**\n\n"
                f"Overrun Probability: **{row['overrun_probability_pct']:.0f}%** | "
                f"Model Confidence: **{conf:.0f}%**\n\n"
                f"Estimated final cost: **₹{row['estimated_final_cost']:,.0f}**\n\n"
                f"**AI Explanation:** {row.get('ai_explanation', 'N/A')}"
            )
            st.divider()

    with t2:
        st.dataframe(health, hide_index=True, use_container_width=True)

    with t3:
        st.dataframe(root_causes, hide_index=True, use_container_width=True)

    with t4:
        for _, row in recommendations.head(8).iterrows():
            st.markdown(f"**{row['project_name']}** — Recommended Actions:")
            actions = row["recommended_actions"] if isinstance(row["recommended_actions"], list) else [row.get("actions_text", "")]
            for action in actions:
                st.markdown(f"- ✔ {action}")

    with t5:
        st.markdown("**Duplicate Invoices**")
        st.dataframe(duplicates, hide_index=True) if not duplicates.empty else st.success("None found")
        st.markdown("**Fraud / Suspicious Spending**")
        st.dataframe(fraud, hide_index=True) if not fraud.empty else st.success("None found")

    with t6:
        if vendors.empty:
            st.info("Add Vendor column in actual files.")
        else:
            st.dataframe(vendors[["vendor", "delivery_pct", "cost_increase", "rating_stars", "assessment"]], hide_index=True)
            if worst_vendor:
                st.error(
                    f"**Worst Vendor: {worst_vendor['vendor']}** {worst_vendor.get('rating_stars', '')}\n\n"
                    f"Delivery: **{worst_vendor.get('delivery_pct', 0):.0f}%** | "
                    f"Assessment: **{worst_vendor.get('assessment', 'N/A')}**\n\n"
                    f"**Reason:** {worst_vendor['reasons']}"
                )

    with t7:
        st.markdown(weekly_report)

    st.subheader("Completion Cost Forecast")
    st.dataframe(forecasts, hide_index=True, use_container_width=True)


def render_chat_assistant(answer_fn) -> None:
    st.subheader("AI Chat Assistant")
    question = st.text_input("Ask anything about your projects", placeholder="Which project has the highest risk?")
    if question:
        st.markdown(answer_fn(question))
