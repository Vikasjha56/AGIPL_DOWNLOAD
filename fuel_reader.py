"""
fuel_reader.py
==============
Fetches the LIVE Fuel / Machine Working Report from the published Google
Sheet CSV link and returns a clean pandas DataFrame.

The published report is a "banded" export -> it contains noise rows like:
    AGRAWAL GLOBAL INFRATECH PVT. LTD.
    HEAD OFFICE
    (Service Log : 01-05-26 To : 17-07-26 )
    SrNo. | Working Date | Log Book No. | ...   <- real header row
    Company -> AGRAWAL GLOBAL INFRATECH PVT. LTD.
    Site -> AMO
    Category -> BACKHOE LOADER - 9213
    1 | 01-05-2026 | AMO-723 | ...              <- real data row
    2 | 02-05-2026 | AMO-724 | ...
    ...
    Category -> DIESEL GENERATOR - 9219
    ...
    Total

We locate the real header row (first cell == 'SrNo.') and then keep only
the rows below it whose first cell is a clean integer (the SrNo column).
That single rule automatically drops every banner / sub-header / Total row,
regardless of how many Site/Category groups the sheet contains, and works
even as new rows get appended daily.
"""

import re
from io import StringIO

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# LIVE GOOGLE SHEET LINK (published as CSV)
# Replace this if the sheet is ever re-published with a new link.
# ---------------------------------------------------------------------------
GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKygsnSF9wt3eBxzrJAvwG-gKbUrTEEuxDFT6BsRckeF8SW6k1pJdAsmfld_k1FnWXUBVMeMhZ0jgW/pub?output=csv"
)


def get_owner_data():
    resp = requests.get(OWNER_SHEET_URL, timeout=20)
    resp.raise_for_status()

    owner_df = pd.read_csv(
        StringIO(resp.text),
        dtype=str,
        keep_default_na=False
    )

    owner_df.columns = owner_df.columns.str.strip()

    owner_df["Machine"] = owner_df["Machine"].astype(str).str.strip().str.upper()
    owner_df["Owner"] = owner_df["Owner"].astype(str).str.strip()

    return owner_df[["Machine","Owner"]]

# The real header row always starts with this text
HEADER_ANCHOR = "SrNo."


def _find_header_row(raw: pd.DataFrame) -> int:
    """Scan the first N rows to find the row that starts with 'SrNo.'"""
    scan_limit = min(25, len(raw))
    for i in range(scan_limit):
        first_cell = str(raw.iloc[i, 0]).strip()
        if first_cell == HEADER_ANCHOR:
            return i
    raise ValueError(
        f"Could not find the header row (expected first cell = '{HEADER_ANCHOR}'). "
        "The published sheet layout may have changed."
    )


def _is_valid_srno(value) -> bool:
    """A genuine data row has an integer SrNo. Banner / Total rows don't."""
    try:
        int(str(value).strip())
        return True
    except (ValueError, TypeError):
        return False


def get_fuel_sheet_data() -> pd.DataFrame:
    """
    Downloads + cleans the live Fuel / Machine Working Report.
    Returns a DataFrame with the ORIGINAL column names from the sheet
    (Working Date, Log Book No., Machine Category, Machine, From Reading,
    To Reading, Time Op. Reading, Time Cls. Reading, Fuel Issue, Work Done,
    Machine Status, etc.) - ready to be passed into prepare_fuel_analysis().
    """
    resp = requests.get(GOOGLE_SHEET_CSV_URL, timeout=25)
    resp.raise_for_status()
    resp.encoding = "utf-8"

    raw = pd.read_csv(
        StringIO(resp.text),
        header=None,
        dtype=str,
        keep_default_na=False,
        on_bad_lines="skip",
    )
    if raw.empty:
        return pd.DataFrame()

    header_idx = _find_header_row(raw)
    headers = [str(h).strip() for h in raw.iloc[header_idx].tolist()]

    df = raw.iloc[header_idx + 1:].copy()
    df.columns = headers[: len(df.columns)]

    # de-duplicate any accidental blank/duplicate column names
    seen = {}
    new_cols = []
    for c in df.columns:
        c = c if c else "Unnamed"
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}.{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols

    first_col = df.columns[0]
    df = df[df[first_col].apply(_is_valid_srno)].copy()
    df = df.reset_index(drop=True)

    return df
