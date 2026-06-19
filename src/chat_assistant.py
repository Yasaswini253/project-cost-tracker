"""Enhanced AI chat assistant for project cost queries."""

from __future__ import annotations

import pandas as pd


def answer_question(
    question: str,
    project_summary: pd.DataFrame,
    project_risk: pd.DataFrame,
    health: pd.DataFrame,
    root_causes: pd.DataFrame,
    predictions: pd.DataFrame,
    vendors: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    rankings: pd.DataFrame,
    kpis: dict,
    worst_vendor: dict,
) -> str:
    """Answer natural-language questions about project costs."""
    q = question.lower().strip()

    if not q:
        return "Ask about risk, vendors, anomalies, budget, or which project to review first."

    if "highest risk" in q or "most risk" in q:
        top = project_risk.sort_values("budget_health_pct").head(1)
        if top.empty:
            return "No project data available."
        row = top.iloc[0]
        return (
            f"**{row['project_name']}** has the highest risk {row['risk_badge']}\n\n"
            f"- Risk Level: **{row['risk_level']}**\n"
            f"- Budget Health: **{row['budget_health_pct']:.0f}%**\n"
            f"- CPI: **{row['cpi']:.2f}**\n"
            f"- Expected Loss: **₹{row['expected_loss']:,.0f}**"
        )

    if "vendor" in q and ("loss" in q or "maximum" in q or "worst" in q):
        if not worst_vendor:
            return "No vendor data found. Add a Vendor column in your actual cost files."
        return (
            f"**Worst Vendor: {worst_vendor['vendor']}** ({worst_vendor.get('rating_stars', '')})\n\n"
            f"**Reasons:** {worst_vendor['reasons']}"
        )

    if "exceeded budget" in q or "most over" in q or "worst project" in q:
        worst = project_risk.sort_values("cpi").head(1)
        if worst.empty:
            return "No data available."
        row = worst.iloc[0]
        return (
            f"**{row['project_name']}** exceeded budget the most.\n\n"
            f"- CPI: **{row['cpi']:.2f}**\n"
            f"- Expected Loss: **₹{row['expected_loss']:,.0f}**\n"
            f"- Status: **{row['budget_status']}** {row['risk_badge']}"
        )

    if "anomal" in q or "unusual" in q:
        anomalies = anomaly_df[anomaly_df["is_anomaly"]]
        if anomalies.empty:
            return "No anomalies detected in the uploaded data."
        lines = [f"- **{r['project_name']}**: {r['anomaly_reasons']}" for _, r in anomalies.head(10).iterrows()]
        return "**Anomalies detected:**\n" + "\n".join(lines)

    if "review first" in q or "management" in q:
        review = rankings.sort_values("rank", ascending=False).head(1)
        if review.empty:
            return "No projects to review."
        row = review.iloc[0]
        pred = predictions[predictions["project_name"] == row["project_name"]]
        explanation = pred.iloc[0]["ai_explanation"] if not pred.empty else "Review cost trends"
        return (
            f"**Management should review {row['project_name']} first.**\n\n"
            f"- Rank: **#{int(row['rank'])}** (worst)\n"
            f"- CPI: **{row['cpi']:.2f}** {row['risk_badge']}\n"
            f"- AI Explanation: {explanation}"
        )

    if "over budget" in q or ("why" in q and any(n.lower() in q for n in project_summary["project_name"])):
        for name in project_summary["project_name"]:
            if name.lower() in q:
                proj = project_risk[project_risk["project_name"] == name].iloc[0]
                causes = root_causes[root_causes["project_name"] == name]
                cause_text = causes.iloc[0]["possible_reasons"] if not causes.empty else "Review cost data"
                pred = predictions[predictions["project_name"] == name]
                ai_exp = pred.iloc[0]["ai_explanation"] if not pred.empty else cause_text
                return (
                    f"**{name}** — Risk {proj['risk_badge']} **{proj['risk_level']}**\n\n"
                    f"- Budget Health: **{proj['budget_health_pct']:.0f}%**\n"
                    f"- Expected Loss: **₹{proj['expected_loss']:,.0f}**\n\n"
                    f"**AI Explanation:** {ai_exp}\n\n"
                    f"**Root Causes:** {cause_text}"
                )

    if "cpi" in q:
        return f"Overall **CPI is {kpis['overall_cpi']:.2f}**. 🟢 Low risk if >1, 🟡 Medium if 0.9–1, 🔴 High if <0.9."

    if "rank" in q:
        top5 = rankings.head(5)[["rank", "project_name", "cpi", "budget_status"]]
        lines = [f"{int(r['rank'])}. {r['project_name']} – CPI {r['cpi']:.2f} ({r['budget_status']})" for _, r in top5.iterrows()]
        return "**Top 5 Best Projects:**\n" + "\n".join(lines)

    if "saving" in q:
        return "Check the **Potential Savings** section for overtime reduction, supplier change, and duplicate invoice recovery estimates."

    return (
        "**Try asking:**\n"
        "- Which project has the highest risk?\n"
        "- Which vendor causes maximum loss?\n"
        "- Which task exceeded budget most?\n"
        "- Show all anomalies\n"
        "- Which project should management review first?\n"
        "- Why is Task_11 over budget?"
    )
