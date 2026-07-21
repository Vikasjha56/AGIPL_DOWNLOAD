"""Prepare the live fuel report for every dashboard tab.

The selected reading pair always follows this order:
1. Time Op. Reading / Time Cls. Reading (hour-meter) when both values exist.
2. From Reading / To Reading (distance) only when the time pair is absent.

Hour-meter consumption is Ltr/Hr. Distance consumption is Ltr/Km. This
prevents valid fallback records from becoming zero merely because Hours Run
is blank.
"""

import re

import numpy as np
import pandas as pd


_NUMERIC_CLEAN_RE = re.compile(r"[^0-9.\-]")


def _to_float(value) -> float:
    """Convert sheet values such as ``1,250.50 km`` to a float."""
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    text = _NUMERIC_CLEAN_RE.sub("", text)
    if text in ("", "-", "."):
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _hours_text_to_decimal(value) -> float:
    """Convert ``H:MM`` (or a plain numeric value) to decimal hours."""
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    if ":" not in text:
        return _to_float(text)
    parts = text.split(":", 1)
    try:
        hours = float(parts[0]) if parts[0] else 0.0
        minutes = float(parts[1]) if parts[1] else 0.0
        return round(hours + minutes / 60, 3)
    except ValueError:
        return 0.0


def _derive_site(log_book_no) -> str:
    text = str(log_book_no).strip()
    if not text:
        return "Not Defined"
    return text.split("-", 1)[0].strip().upper() or "Not Defined"


def _get(df: pd.DataFrame, name: str, default="") -> pd.Series:
    """Get a column safely, including sheets that omit an optional column."""
    if name in df.columns:
        return df[name]
    return pd.Series([default] * len(df), index=df.index)


def _has_number(value) -> bool:
    """True for a supplied numeric cell, including a genuine zero reading."""
    if value is None:
        return False
    text = _NUMERIC_CLEAN_RE.sub("", str(value).strip())
    if text in ("", "-", "."):
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False


def prepare_fuel_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Return cleaned records, with a correct per-row consumption basis."""
    df = df.copy()

    date_raw = _get(df, "Working Date")
    parsed_date = pd.to_datetime(date_raw, format="%d-%m-%Y", errors="coerce")
    parsed_date = parsed_date.fillna(pd.to_datetime(date_raw, dayfirst=True, errors="coerce"))
    df["_ParsedDate"] = parsed_date
    df = df.loc[df["_ParsedDate"].notna()].copy()

    df["Working Date"] = df["_ParsedDate"].dt.strftime("%d-%m-%Y")
    df["Date ISO"] = df["_ParsedDate"].dt.strftime("%Y-%m-%d")
    df["Month Key"] = df["_ParsedDate"].dt.strftime("%Y-%m")
    df["Month Label"] = df["_ParsedDate"].dt.strftime("%b %Y")

    df["Log Book No."] = _get(df, "Log Book No.").astype(str).str.strip()
    df["Site Name"] = df["Log Book No."].map(_derive_site)
    df["Machine Category"] = _get(df, "Machine Category").astype(str).str.strip()
    df["Machine"] = _get(df, "Machine").astype(str).str.strip()
    df["Work Done"] = _get(df, "Work Done").astype(str).str.strip()
    # The published working report has no Owner column. Keep a safe value so
    # the Hire/Self chart code never fails; replace with a real lookup later.
    df["Owner"] = _get(df, "Owner", "Not Defined").astype(str).str.strip().replace("", "Not Defined")

    status_name = "Machine Status " if "Machine Status " in df.columns else "Machine Status"
    df["Machine Status"] = _get(df, status_name).astype(str).str.strip().replace("", "Not Defined")

    # Keep both original pairs visible to the Fuel Details dashboard.
    from_raw = _get(df, "From Reading", "")
    to_raw = _get(df, "To Reading", "")
    time_op_raw = _get(df, "Time Op. Reading", "")
    time_cls_raw = _get(df, "Time Cls. Reading", "")
    df["From Reading"] = from_raw.map(_to_float)
    df["To Reading"] = to_raw.map(_to_float)
    df["Time Op. Reading"] = time_op_raw.map(_to_float)
    df["Time Cls. Reading"] = time_cls_raw.map(_to_float)

    # Source priority is intentional. A machine can have old From/To values
    # as well as current hour-meter values: always use Time Op./Cls. first.
    # Both cells must exist; a one-sided value must never create an average.
    from_to_distance = (df["To Reading"] - df["From Reading"]).clip(lower=0)
    time_reading_run = (df["Time Cls. Reading"] - df["Time Op. Reading"]).clip(lower=0)
    has_time_pair = time_op_raw.map(_has_number) & time_cls_raw.map(_has_number)
    has_from_to_pair = from_raw.map(_has_number) & to_raw.map(_has_number)
    uses_distance = ~has_time_pair & has_from_to_pair

    df["Opening Reading"] = np.where(has_time_pair, df["Time Op. Reading"], df["From Reading"])
    df["Closing Reading"] = np.where(has_time_pair, df["Time Cls. Reading"], df["To Reading"])
    df["Run Reading"] = np.where(has_time_pair, time_reading_run, from_to_distance)
    df["Reading Type"] = np.select(
        [has_time_pair, uses_distance],
        ["Hour-Meter (Time Op./Cls. Reading)", "Distance (From/To Reading)"],
        default="No complete reading pair",
    )

    df["Fuel Used"] = _get(df, "Fuel Issue", 0).map(_to_float)
    df["Run Hours"] = _get(df, "Hours Run (0.1=6 min)", "").map(_hours_text_to_decimal)

    # Critical fix: From/To records use their travelled distance.  Other
    # records use logged hours; if those are absent, an advancing hour meter
    # is a safe fallback.  A zero denominator always remains zero.
    df["Average Denominator"] = np.select(
        [has_time_pair, uses_distance],
        [np.where(df["Run Hours"].gt(0), df["Run Hours"], time_reading_run), from_to_distance],
        default=0.0,
    )
    df["Average Unit"] = np.select(
        [has_time_pair, uses_distance], ["Ltr/Hr", "Ltr/Km"], default="N/A"
    )
    df["Fuel Average"] = np.where(
        df["Average Denominator"].gt(0),
        df["Fuel Used"] / df["Average Denominator"],
        0.0,
    ).round(2)

    df = df.sort_values(["Machine", "_ParsedDate"]).drop(columns="_ParsedDate").reset_index(drop=True)
    return df
