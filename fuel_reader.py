# ==========================================================
# fuel_reader.py
# AGIPL Fuel Dashboard
# Read Machine Working Report from Google Spreadsheet
# ==========================================================

import pandas as pd
import numpy as np

from config import GOOGLE_SHEETS


# ==========================================================
# Fuel Sheet Link
# (Last link of config.py)
# ==========================================================

FUEL_URL = GOOGLE_SHEETS[-1]


# ==========================================================
# Safe Float Converter
# ==========================================================

def to_float(value):

    if pd.isna(value):
        return 0.0

    txt = str(value).strip()

    if txt == "":
        return 0.0

    txt = txt.replace(",", "")

    try:
        return float(txt)
    except:
        return 0.0


# ==========================================================
# Read Fuel Sheet
# ==========================================================

def get_fuel_sheet_data():

    df = pd.read_csv(FUEL_URL)

    # -----------------------------
    # Remove blank column names
    # -----------------------------

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # -----------------------------
    # Required Columns
    # -----------------------------

    required = [

        "Working Date",
        "Log Book No.",
        "Machine Category",
        "Machine",
        "Machine Status",

        "From Reading",
        "To Reading",

        "Time Op. Reading",
        "Time Cls. Reading",

        "Fuel Issue",
        "Average",

        "Driver",
        "Helper",

        "Shift",

        "Remark",
        "Work Done"

    ]

    for col in required:

        if col not in df.columns:

            df[col] = ""


    # -----------------------------
    # Numeric Conversion
    # -----------------------------

    numeric = [

        "From Reading",
        "To Reading",

        "Time Op. Reading",
        "Time Cls. Reading",

        "Fuel Issue",
        "Average"

    ]

    for c in numeric:

        df[c] = df[c].apply(to_float)


    # -----------------------------
    # Date Conversion
    # -----------------------------

    df["Working Date"] = pd.to_datetime(

        df["Working Date"],

        errors="coerce"

    )


    df = df.sort_values(

        "Working Date"

    )


    # -----------------------------
    # Month
    # -----------------------------

    df["Month"] = (

        df["Working Date"]

        .dt.strftime("%b-%Y")

    )


    # -----------------------------
    # Machine Name
    # -----------------------------

    df["Machine"] = (

        df["Machine"]

        .fillna("")

        .astype(str)

        .str.strip()

    )


    # -----------------------------
    # RTO Number
    # Example:
    # BACK HOE LOADER-JCB(6616)-AGIPL
    # -----------------------------

    def get_rto(machine):

        machine = str(machine)

        if "(" in machine and ")" in machine:

            return machine.split("(")[-1].split(")")[0]

        return ""


    df["RTO Number"] = (

        df["Machine"]

        .apply(get_rto)

    )


    # =====================================================
    # AUTO DETECT HOURS OR KM
    # =====================================================

    run_hours = []

    fuel_average = []

    average_unit = []

    fuel_used = []

    working_type = []


    for _, row in df.iterrows():

        fuel = to_float(

            row["Fuel Issue"]

        )


        op = to_float(

            row["Time Op. Reading"]

        )


        cls = to_float(

            row["Time Cls. Reading"]

        )


        frm = to_float(

            row["From Reading"]

        )


        to = to_float(

            row["To Reading"]

        )


        # ===================================
        # Hour Meter Machine
        # ===================================

        if cls > op:

            hrs = round(

                cls - op,

                2

            )

            run_hours.append(

                hrs

            )

            fuel_used.append(

                fuel

            )

            working_type.append(

                "Hour Meter"

            )


            if hrs > 0:

                fuel_average.append(

                    round(

                        fuel / hrs,

                        2

                    )

                )

            else:

                fuel_average.append(0)


            average_unit.append(

                "L/Hr"

            )


        # ===================================
        # KM Based Machine
        # ===================================

        elif to > frm:

            km = round(

                to - frm,

                2

            )

            run_hours.append(

                km

            )

            fuel_used.append(

                fuel

            )

            working_type.append(

                "Odometer"

            )


            if fuel > 0:

                fuel_average.append(

                    round(

                        km / fuel,

                        2

                    )

                )

            else:

                fuel_average.append(0)


            average_unit.append(

                "KM/L"

            )


        # ===================================
        # No Reading
        # ===================================

        else:

            run_hours.append(0)

            fuel_used.append(fuel)

            fuel_average.append(0)

            average_unit.append("-")

            working_type.append("Unknown")


    # =====================================================
    # Final Columns
    # =====================================================

    df["Run Hours"] = run_hours

    df["Fuel Used"] = fuel_used

    df["Fuel Average"] = fuel_average

    df["Average Unit"] = average_unit

    df["Working Type"] = working_type


    # =====================================================
    # Remove Blank Machine
    # =====================================================

    df = df[

        df["Machine"] != ""

    ].copy()


    # =====================================================
    # Reset Index
    # =====================================================

    df.reset_index(

        drop=True,

        inplace=True

    )


    return df
