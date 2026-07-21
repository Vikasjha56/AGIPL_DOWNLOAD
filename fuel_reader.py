"""Download and clean the published Fuel / Machine Working Report."""

from io import StringIO

import pandas as pd
import requests


GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKygsnSF9wt3eBxzrJAvwG-gKbUrTEEuxDFT6BsRckeF8SW6k1pJdAsmfld_k1FnWXUBVMeMhZ0jgW"
    "/pub?output=csv"
)
HEADER_ANCHOR = "SrNo."


def _find_header_row(raw: pd.DataFrame) -> int:
    for row_index in range(min(25, len(raw))):
        if str(raw.iloc[row_index, 0]).strip() == HEADER_ANCHOR:
            return row_index
    raise ValueError(
        f"Could not find the header row (expected first cell = {HEADER_ANCHOR!r}). "
        "The published sheet layout may have changed."
    )


def _is_valid_srno(value) -> bool:
    try:
        int(str(value).strip())
        return True
    except (ValueError, TypeError):
        return False


def get_fuel_sheet_data() -> pd.DataFrame:
    response = requests.get(GOOGLE_SHEET_CSV_URL, timeout=25)
    response.raise_for_status()
    response.encoding = "utf-8"
    raw = pd.read_csv(
        StringIO(response.text), header=None, dtype=str,
        keep_default_na=False, on_bad_lines="skip",
    )
    if raw.empty:
        return pd.DataFrame()

    header_index = _find_header_row(raw)
    headers = [str(value).strip() for value in raw.iloc[header_index].tolist()]
    df = raw.iloc[header_index + 1:].copy()
    df.columns = headers[:len(df.columns)]

    # Pandas needs unique names, including if the source has blank headers.
    seen, unique_headers = {}, []
    for header in df.columns:
        header = header or "Unnamed"
        count = seen.get(header, 0)
        unique_headers.append(header if count == 0 else f"{header}.{count}")
        seen[header] = count + 1
    df.columns = unique_headers

    first_column = df.columns[0]
    return df.loc[df[first_column].map(_is_valid_srno)].reset_index(drop=True)
