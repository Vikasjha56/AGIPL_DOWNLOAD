"""Prepare the live fuel report for every dashboard tab.

For hour-meter machines the consumption unit is Ltr/Hr.  For machines that
use From Reading / To Reading (for example tippers), the consumption unit is
Ltr/Km and the distance reading is used as the denominator.  This prevents
valid tipper records from becoming zero merely because Hours Run is blank.
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

    status_name = "Machine Status " if "Machine Status " in df.columns else "Machine Status"
    df["Machine Status"] = _get(df, status_name).astype(str).str.strip().replace("", "Not Defined")

    # Keep both original pairs visible to the Fuel Details dashboard.
    df["From Reading"] = _get(df, "From Reading", 0).map(_to_float)
    df["To Reading"] = _get(df, "To Reading", 0).map(_to_float)
    df["Time Op. Reading"] = _get(df, "Time Op. Reading", 0).map(_to_float)
    df["Time Cls. Reading"] = _get(df, "Time Cls. Reading", 0).map(_to_float)

    # A From/To pair is valid only when it advanced.  A non-zero one-sided
