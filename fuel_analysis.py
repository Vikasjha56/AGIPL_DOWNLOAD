"""
fuel_analysis.py
================
Turns the raw Fuel / Machine Working Report DataFrame (from fuel_reader.py)
into an analysis-ready DataFrame with:

  - Opening Reading / Closing Reading  -> auto-picked from whichever pair
    actually has data: "From Reading"/"To Reading" OR
    "Time Op. Reading"/"Time Cls. Reading" (most machines only populate one
    of the two pairs; the other stays 0,0).
  - Run Reading   = Closing - Opening (km OR hour-meter units, per machine)
  - Run Hours     = parsed from "Hours Run (0.1=6 min)" column (format H:MM)
  - Fuel Used     = "Fuel Issue" column
  - Fuel Average  = Fuel Used / Run Hours
  - Month / Working Date / Site Name (derived from Log Book No. prefix,
    e.g. "AMO-723" -> "AMO")
  - KPI summary dict attached to df.attrs['kpi']

NOTE ON "Owner" (Self / Hire):
This report does not contain an Owner column (that lives only in the
separate "Fuel Tracker" sheet). Owner is set to "Not Defined" here so the
dashboard/slicer still works; wire in a real Owner column/lookup later if
you publish it alongside this sheet.
"""

import re

import numpy as np
import pandas as pd

_NUMERIC_CLEAN_RE = re.compile(r"[^0-9.\-]")


def _to_float(value) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    if s == "":
        return 0.0
    s = _NUMERIC_CLEAN_RE.sub("", s)
    if s in ("", "-", "."):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _hours_text_to_decimal(value) -> float:
    """'6:30' -> 6.5 hours. Falls back to plain float if no colon."""
    if value is None:
        return 0.0
    s = str(value).strip()
    if s == "":
        return 0.0
    if ":" in s:
        parts = s.split(":")
        try:
            h = float(parts[0]) if parts[0] != "" else 0.0
            m = float(parts[1]) if len(parts) > 1 and parts[1] != "" else 0.0
            return round(h + m / 60.0, 3)
        except ValueError:
            return 0.0
    return _to_float(s)


def _derive_site(log_book_no) -> str:
    s = str(log_book_no).strip()
    m = re.match(r"^[A-Za-z]+", s)
    if m:
        return m.group(0).upper()
    return s if s else "Not Defined"


def _get(df: pd.DataFrame, name: str, default=""):
    return df[name] if name in df.columns else pd.Series([default] * len(df))


def prepare_fuel_analysis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ---------- Date / Month ----------
    working_date_raw = _get(df, "Working Date", "")
    parsed_date = pd.to_datetime(working_date_raw, format="%d-%m-%Y", errors="coerce")
    # fallback to a looser parse for any rows that don't match dd-mm-yyyy
    fallback = pd.to_datetime(working_date_raw, errors="coerce", dayfirst=True)
    parsed_date = parsed_date.fillna(fallback)

    df["_ParsedDate"] = parsed_date
    df = df[df["_ParsedDate"].notna()].copy()

    df["Working Date"] = df["_ParsedDate"].dt.strftime("%d-%m-%Y")
    df["Date ISO"] = df["_ParsedDate"].dt.strftime("%Y-%m-%d")
    df["Month Key"] = df["_ParsedDate"].dt.strftime("%Y-%m")
    df["Month Label"] = df["_ParsedDate"].dt.strftime("%b %Y")

    # ---------- Identity columns ----------
    df["Log Book No."] = _get(df, "Log Book No.").astype(str).str.strip()
    df["Site Name"] = df["Log Book No."].apply(_derive_site)
    df["Machine Category"] = _get(df, "Machine Category").astype(str).str.strip()
    df["Machine"] = _get(df, "Machine").astype(str).str.strip()

    status_col = "Machine Status " if "Machine Status " in df.columns else "Machine Status"
    df["Machine Status"] = _get(df, status_col).astype(str).str.strip()
    df.loc[df["Machine Status"] == "", "Machine Status"] = "Not Defined"

    df["Work Done"] = _get(df, "Work Done").astype(str).str.strip()

    # Owner is not present in this report -> placeholder (see module docstring)
    df["Owner"] = "Not Defined"

    # ---------- Opening / Closing reading (auto pair-detect) ----------
    from_reading = _get(df, "From Reading", 0).apply(_to_float)
    to_reading = _get(df, "To Reading", 0).apply(_to_float)
    time_op = _get(df, "Time Op. Reading", 0).apply(_to_float)
    time_cls = _get(df, "Time Cls. Reading", 0).apply(_to_float)

    use_from_to = (from_reading != 0) | (to_reading != 0)

    df["Opening Reading"] = np.where(use_from_to, from_reading, time_op)
    df["Closing Reading"] = np.where(use_from_to, to_reading, time_cls)
    df["Reading Type"] = np.where(
        use_from_to, "KM (From/To Reading)", "Hour-Meter (Time Op./Cls. Reading)"
    )
    df["Run Reading"] = (df["Closing Reading"] - df["Opening Reading"]).clip(lower=0)

    # ---------- Fuel / Hours / Average ----------
    df["Fuel Used"] = _get(df, "Fuel Issue", 0).apply(_to_float)
    df["Run Hours"] = _get(df, "Hours Run (0.1=6 min)", "").apply(_hours_text_to_decimal)

    df["Fuel Average"] = np.where(
        df["Run Hours"] > 0, df["Fuel Used"] / df["Run Hours"], 0.0
    )
    df["Fuel Average"] = df["Fuel Average"].round(2)

    df = df.sort_values(["Machine", "_ParsedDate"]).reset_index(drop=True)
    df = df.drop(columns=["_ParsedDate"])

    # ---------- KPI summary ----------
    total_fuel = float(df["Fuel Used"].sum())
    total_hours = float(df["Run Hours"].sum())
    working_mask = df["Machine Status"].str.lower() == "working"
    idle_mask = df["Machine Status"].str.lower() == "idle"

    kpi = {
        "total_records": int(len(df)),
        "total_machines": int(df["Machine"].nunique()),
        "total_sites": int(df["Site Name"].nunique()),
        "total_fuel_issued": round(total_fuel, 2),
        "total_hours_used": round(total_hours, 2),
        "overall_average": round(total_fuel / total_hours, 2) if total_hours > 0 else 0.0,
        "working_entries": int(working_mask.sum()),
        "idle_entries": int(idle_mask.sum()),
        "utilization_pct": round(
            (working_mask.sum() / len(df) * 100.0), 1
        )
        if len(df) > 0
        else 0.0,
    }
    df.attrs["kpi"] = kpi

    return df
