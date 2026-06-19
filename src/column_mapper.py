"""Manual column mapping when auto-detection fails."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import pandas as pd

STANDARD_FIELDS = {
    "project_id": "Project / Task ID",
    "project_name": "Project / Task Name",
    "etc_amount": "ETC Amount (ETC files only)",
    "actual_amount": "Actual Cost (Actual files only)",
    "cost_element": "Department / Phase / Module",
    "period": "Week / Period / Date",
    "planned_cost": "Planned Cost / Budget",
    "earned_value": "Earned Value",
    "vendor": "Vendor / Supplier",
    "invoice_id": "Invoice ID",
    "department": "Department",
    "status": "Task Status",
}


def read_raw_file(source: str | BinaryIO) -> pd.DataFrame:
    """Read file without column normalization."""
    if isinstance(source, str):
        path = Path(source)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(source)
        if path.suffix.lower() == ".tsv":
            return pd.read_csv(source, sep="\t")
        return pd.read_csv(source)

    name = getattr(source, "name", "upload.csv").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(source)
    if name.endswith(".tsv"):
        return pd.read_csv(source, sep="\t")
    return pd.read_csv(source)


def get_raw_columns(source) -> list[str]:
    df = read_raw_file(source)
    return [str(c) for c in df.columns]


def apply_manual_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Apply user-selected column mapping."""
    rename_map = {src: tgt for src, tgt in mapping.items() if tgt and tgt != "(skip)"}
    return df.rename(columns=rename_map)


def suggest_column_mapping(columns: list[str], file_type: str) -> dict[str, str]:
    """Suggest mapping from raw columns to standard fields using keyword matching."""
    suggestions: dict[str, str] = {}
    lower_cols = {c: c.lower().replace(" ", "_").replace("-", "_") for c in columns}

    rules = [
        (["project_id", "task_id"], ["task_id", "project_id", "id", "wbs"]),
        (["project_name", "task_name"], ["task_nam", "task_name", "project_name", "name", "description"]),
        (["etc_amount"] if file_type == "etc" else ["actual_amount"],
         ["etc_cost", "etc", "actual_cost", "acwp", "actual", "spent", "cost"]),
        (["cost_element"], ["department", "phase", "module", "activity", "category", "element"]),
        (["period"], ["week", "period", "month", "date"]),
        (["vendor"], ["vendor", "supplier"]),
        (["invoice_id"], ["invoice"]),
        (["status"], ["status", "state"]),
        (["planned_cost"], ["budget", "planned", "bac"]),
    ]

    used_targets: set[str] = set()
    for targets, keywords in rules:
        for col, lc in lower_cols.items():
            if col in suggestions:
                continue
            if any(kw in lc for kw in keywords):
                target = targets[0]
                if target not in used_targets:
                    suggestions[col] = target
                    used_targets.add(target)
                    break

    return suggestions


def build_mapping_ui_columns(raw_columns: list[str], file_type: str) -> dict[str, list[str]]:
    """Return options for each standard field for Streamlit selectboxes."""
    options = ["(skip)"] + raw_columns
    relevant_fields = ["project_id", "project_name", "cost_element", "period", "vendor", "invoice_id", "department", "status", "planned_cost"]
    if file_type == "etc":
        relevant_fields.insert(2, "etc_amount")
    else:
        relevant_fields.insert(2, "actual_amount")

    return {field: options for field in relevant_fields if field in STANDARD_FIELDS}
