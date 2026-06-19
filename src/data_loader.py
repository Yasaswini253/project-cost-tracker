"""Load and consolidate ETC and actual cost files."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO

import pandas as pd

PROJECT_ID_ALIASES = [
    "project_id", "project id", "projectid", "id", "wbs", "wbs_id",
    "task_id", "task id", "taskid",
]
PROJECT_NAME_ALIASES = [
    "project_name", "project name", "project", "name", "description",
    "task_name", "task name", "task_nam", "tasknam", "task",
]
COST_ELEMENT_ALIASES = [
    "cost_element", "cost element", "element", "category", "phase", "activity", "module",
]
PERIOD_ALIASES = ["period", "week", "month", "date", "reporting_period", "reporting period"]
ETC_ALIASES = [
    "etc", "etc_amount", "etc_cost", "estimate_to_complete", "estimate to complete",
    "planned_remaining", "planned remaining", "remaining_cost", "remaining cost",
]
ACTUAL_ALIASES = [
    "acwp", "actual", "actual_cost", "actual cost", "actual_amount", "actual amount",
    "actuals", "spent", "cost",
]
PLANNED_ALIASES = ["planned_cost", "planned cost", "budget", "bac", "planned", "plan"]
EV_ALIASES = ["ev", "earned_value", "earned value", "bcwp"]
VENDOR_ALIASES = ["vendor", "supplier", "vendor_name", "supplier_name"]
INVOICE_ALIASES = ["invoice", "invoice_id", "invoice no", "invoice_number", "inv_no"]
DEPARTMENT_ALIASES = ["department", "dept", "discipline", "team", "division"]
STATUS_ALIASES = ["status", "task_status", "state", "progress"]

SUPPORTED_FILE_TYPES = ["csv", "tsv", "xlsx", "xls"]

SUPPORTED_COLUMN_NAMES = {
    "project": "Project_ID, Task_ID, Project_Name, Task_Nam, Task_Name, WBS",
    "cost_element": "Cost_Element, Category, Phase, Activity, Module",
    "period": "Period, Week, Month, Date",
    "etc_amount": "ETC, ETC_Cost, Estimate_to_Complete, Planned_Remaining",
    "actual_amount": "ACWP, Actual, Actual_Cost, Actuals, Cost, Spent",
    "optional": "Planned_Cost, Budget, BAC, Earned_Value, Vendor, Invoice_ID",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [
        re.sub(r"_+", "_", str(col).strip().lower().replace("-", "_").replace(" ", "_"))
        for col in normalized.columns
    ]
    return normalized


def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    alias_set = {alias.replace(" ", "_") for alias in aliases}
    for col in columns:
        if col in alias_set:
            return col
    return None


def _find_column_fuzzy(columns: list[str], file_type: str) -> dict[str, str]:
    """Fallback matching for headers like Task_Nam, ETC_Cost, etc."""
    mapping: dict[str, str] = {}

    for col in columns:
        if col in mapping.values() or col in mapping:
            continue

        if "invoice" in col and "invoice_id" not in mapping.values():
            mapping[col] = "invoice_id"
        elif any(v in col for v in ["vendor", "supplier"]) and "vendor" not in mapping.values():
            mapping[col] = "vendor"
        elif "task" in col and "id" in col and "project_id" not in mapping.values():
            mapping[col] = "project_id"
        elif "task" in col and ("nam" in col or "name" in col) and "project_name" not in mapping.values():
            mapping[col] = "project_name"
        elif col.startswith("etc") or col.endswith("_etc") or col == "etc_cost":
            if file_type == "etc" and "etc_amount" not in mapping.values():
                mapping[col] = "etc_amount"
        elif "actual" in col and file_type == "actual" and "actual_amount" not in mapping.values():
            mapping[col] = "actual_amount"
        elif file_type == "actual" and col in {"cost", "spent", "amount"} and "actual_amount" not in mapping.values():
            mapping[col] = "actual_amount"
        elif "week" in col or "period" in col or "month" in col:
            if "period" not in mapping.values():
                mapping[col] = "period"
        elif "module" in col or "phase" in col or "activity" in col:
            if "cost_element" not in mapping.values():
                mapping[col] = "cost_element"

    return mapping


def _rename_to_standard(df: pd.DataFrame, file_type: str) -> pd.DataFrame:
    cols = list(df.columns)
    mapping: dict[str, str] = {}

    for alias_list, target in [
        (PROJECT_ID_ALIASES, "project_id"),
        (PROJECT_NAME_ALIASES, "project_name"),
        (COST_ELEMENT_ALIASES, "cost_element"),
        (PERIOD_ALIASES, "period"),
        (PLANNED_ALIASES, "planned_cost"),
        (EV_ALIASES, "earned_value"),
        (VENDOR_ALIASES, "vendor"),
        (INVOICE_ALIASES, "invoice_id"),
        (DEPARTMENT_ALIASES, "department"),
        (STATUS_ALIASES, "status"),
    ]:
        found = _find_column(cols, alias_list)
        if found:
            mapping[found] = target

    if file_type == "etc":
        amount_col = _find_column(cols, ETC_ALIASES)
        if amount_col:
            mapping[amount_col] = "etc_amount"
    else:
        amount_col = _find_column(cols, ACTUAL_ALIASES)
        if amount_col:
            mapping[amount_col] = "actual_amount"

    fuzzy = _find_column_fuzzy(cols, file_type)
    for col, target in fuzzy.items():
        if col not in mapping and target not in mapping.values():
            mapping[col] = target

    renamed = df.rename(columns=mapping)

    if file_type == "etc" and "etc_amount" not in renamed.columns:
        numeric_cols = renamed.select_dtypes(include="number").columns.tolist()
        non_id = [c for c in numeric_cols if c not in {"project_id"}]
        if len(non_id) == 1:
            renamed = renamed.rename(columns={non_id[0]: "etc_amount"})
        else:
            raise ValueError(
                "ETC file must include an amount column (e.g. ETC_Cost, ETC, Estimate_to_Complete). "
                f"Found columns: {', '.join(df.columns.astype(str))}"
            )

    if file_type == "actual" and "actual_amount" not in renamed.columns:
        numeric_cols = renamed.select_dtypes(include="number").columns.tolist()
        non_id = [c for c in numeric_cols if c not in {"project_id"}]
        if len(non_id) == 1:
            renamed = renamed.rename(columns={non_id[0]: "actual_amount"})
        else:
            raise ValueError(
                "Actual file must include an amount column (e.g. Actual_Cost, ACWP, Actual). "
                f"Found columns: {', '.join(df.columns.astype(str))}"
            )

    if "project_id" not in renamed.columns and "project_name" not in renamed.columns:
        raise ValueError(
            "Each file must include a project/task ID or name column (e.g. Task_ID, Project_ID)."
        )

    return renamed


def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    for col in columns:
        if col in result.columns:
            result[col] = (
                result[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.strip()
            )
            result[col] = pd.to_numeric(result[col], errors="coerce")
    return result


def _read_file(path_or_buffer, filename: str) -> pd.DataFrame:
    lower = filename.lower()
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(path_or_buffer)
    if lower.endswith(".tsv"):
        return pd.read_csv(path_or_buffer, sep="\t")
    return pd.read_csv(path_or_buffer)


def load_cost_file(
    source: str | BinaryIO | io.BytesIO,
    file_type: str,
    manual_mapping: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Load CSV, TSV, or Excel cost file and normalize columns."""
    if file_type not in {"etc", "actual"}:
        raise ValueError("file_type must be 'etc' or 'actual'.")

    if isinstance(source, str):
        df = _read_file(source, source)
        source_name = Path(source).name
    else:
        name = getattr(source, "name", "upload.csv")
        df = _read_file(source, name)
        source_name = name

    if df.empty:
        raise ValueError(f"Uploaded file '{source_name}' is empty.")

    if manual_mapping:
        from src.column_mapper import apply_manual_mapping

        rename = {src: tgt for src, tgt in manual_mapping.items() if tgt and tgt != "(skip)"}
        df = apply_manual_mapping(df, rename)
        df = _normalize_columns(df)
        amount_col = "etc_amount" if file_type == "etc" else "actual_amount"
        if amount_col not in df.columns:
            raise ValueError(
                f"Manual mapping must map a column to '{amount_col}'. "
                f"Found columns: {', '.join(df.columns.astype(str))}"
            )
        if "project_id" not in df.columns and "project_name" not in df.columns:
            raise ValueError("Manual mapping must include project_id or project_name.")
    else:
        df = _normalize_columns(df)
        df = _rename_to_standard(df, file_type)

    numeric_cols = ["etc_amount", "actual_amount", "planned_cost", "earned_value"]
    df = _coerce_numeric(df, numeric_cols)

    amount_col = "etc_amount" if file_type == "etc" else "actual_amount"
    df = df.dropna(subset=[amount_col])

    if "project_id" not in df.columns:
        df["project_id"] = df["project_name"].astype(str)
    if "project_name" not in df.columns:
        df["project_name"] = df["project_id"].astype(str)
    if "cost_element" not in df.columns:
        df["cost_element"] = "General"
    if "period" not in df.columns:
        df["period"] = "Overall"

    df["project_id"] = df["project_id"].astype(str).str.strip()
    df["project_name"] = df["project_name"].astype(str).str.strip()
    df["cost_element"] = df["cost_element"].astype(str).str.strip()
    df["period"] = df["period"].astype(str).str.strip()
    df["source_file"] = source_name

    return df.reset_index(drop=True)


def load_multiple_cost_files(
    sources: list,
    file_type: str,
    manual_mapping: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Load and combine multiple ETC or actual cost files."""
    if not sources:
        raise ValueError(f"No {file_type.upper()} files uploaded.")

    frames = [load_cost_file(source, file_type, manual_mapping) for source in sources]
    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates(
        subset=["project_id", "project_name", "cost_element", "period", "source_file"],
        keep="last",
    ).reset_index(drop=True)


def consolidate_cost_data(etc_df: pd.DataFrame, actual_df: pd.DataFrame) -> pd.DataFrame:
    """Merge ETC and actual cost data on project, element, and period."""
    etc_work = etc_df.copy()
    actual_work = actual_df.copy()

    etc_periods = set(etc_work["period"].unique())
    act_periods = set(actual_work["period"].unique())

    if etc_periods == {"Overall"} and act_periods != {"Overall"}:
        actual_agg_cols: dict = {"actual_amount": ("actual_amount", "sum")}
        if "vendor" in actual_work.columns:
            actual_agg_cols["vendor"] = ("vendor", "first")
        if "invoice_id" in actual_work.columns:
            actual_agg_cols["invoice_id"] = ("invoice_id", "first")
        actual_work = actual_work.groupby(
            ["project_id", "project_name", "cost_element"], as_index=False
        ).agg(**actual_agg_cols)
        actual_work["period"] = "Overall"

    if act_periods == {"Overall"} and etc_periods != {"Overall"}:
        etc_agg_cols: dict = {"etc_amount": ("etc_amount", "sum")}
        if "planned_cost" in etc_work.columns:
            etc_agg_cols["planned_cost"] = ("planned_cost", "sum")
        if "earned_value" in etc_work.columns:
            etc_agg_cols["earned_value"] = ("earned_value", "sum")
        etc_work = etc_work.groupby(
            ["project_id", "project_name", "cost_element"], as_index=False
        ).agg(**etc_agg_cols)
        etc_work["period"] = "Overall"

    etc_agg: dict = {"etc_amount": ("etc_amount", "sum")}
    if "planned_cost" in etc_work.columns:
        etc_agg["planned_cost"] = ("planned_cost", "sum")
    if "earned_value" in etc_work.columns:
        etc_agg["earned_value"] = ("earned_value", "sum")

    etc_grouped = etc_work.groupby(
        ["project_id", "project_name", "cost_element", "period"], as_index=False
    ).agg(**etc_agg)

    actual_agg: dict = {"actual_amount": ("actual_amount", "sum")}
    if "vendor" in actual_work.columns:
        actual_agg["vendor"] = ("vendor", "first")
    if "invoice_id" in actual_work.columns:
        actual_agg["invoice_id"] = ("invoice_id", "first")

    actual_grouped = actual_work.groupby(
        ["project_id", "project_name", "cost_element", "period"], as_index=False
    ).agg(**actual_agg)

    merged = pd.merge(
        etc_grouped,
        actual_grouped,
        on=["project_id", "project_name", "cost_element", "period"],
        how="outer",
    )

    for col in ["etc_amount", "planned_cost", "earned_value", "actual_amount"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    if "planned_cost" not in merged.columns or merged["planned_cost"].sum() == 0:
        merged["planned_cost"] = merged["etc_amount"] + merged["actual_amount"]

    if "earned_value" not in merged.columns or merged["earned_value"].sum() == 0:
        merged["earned_value"] = merged["planned_cost"]

    return merged.sort_values(["project_name", "cost_element", "period"]).reset_index(drop=True)
