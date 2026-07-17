# ==========================================================
# fuel_analysis.py
# AGIPL Fuel Dashboard Analytics
# ==========================================================

import pandas as pd
import numpy as np


# ==========================================================
# Safe Float
# ==========================================================

def safe(v):

    try:
        return float(v)
    except:
        return 0.0


# ==========================================================
# Prepare Fuel Analysis
# ==========================================================

def prepare_fuel_analysis(df):

    df = df.copy()

    # ---------------------------------------------
    # Numeric Safety
    # ---------------------------------------------

    numeric = [

        "Fuel Used",
        "Run Hours",
        "Fuel Average"

    ]

    for c in numeric:

        if c in df.columns:

            df[c] = (

                df[c]
                .fillna(0)
                .apply(safe)

            )


    # ---------------------------------------------
    # Month
    # ---------------------------------------------

    if "Month" not in df.columns:

        df["Month"] = (

            pd.to_datetime(

                df["Working Date"],

                errors="coerce"

            )

            .dt.strftime("%b-%Y")

        )


    # ---------------------------------------------
    # Efficiency Status
    # ---------------------------------------------

    def efficiency(row):

        avg = row["Fuel Average"]

        unit = row["Average Unit"]


        # Hour Meter

        if unit == "L/Hr":

            if avg <= 4:
                return "Excellent"

            elif avg <= 7:
                return "Good"

            elif avg <= 10:
                return "Average"

            else:
                return "Poor"


        # KM Based

        if unit == "KM/L":

            if avg >= 5:
                return "Excellent"

            elif avg >= 3.5:
                return "Good"

            elif avg >= 2:
                return "Average"

            else:
                return "Poor"


        return "Unknown"


    df["Efficiency"] = (

        df.apply(

            efficiency,

            axis=1

        )

    )


    # ---------------------------------------------
    # High Consumption Flag
    # ---------------------------------------------

    df["High Consumption"] = (

        df["Efficiency"] ==

        "Poor"

    )


    # ---------------------------------------------
    # Utilization %
    # ---------------------------------------------

    util = (

        df.groupby(

            "Machine"

        )["Working Date"]

        .nunique()

    )


    total_days = (

        df["Working Date"]

        .nunique()

    )


    util_pct = (

        util /

        max(total_days, 1)

    ) * 100


    util_pct = util_pct.round(1)


    df["Utilization %"] = (

        df["Machine"]

        .map(util_pct)

    )


    # ---------------------------------------------
    # Utilization Status
    # ---------------------------------------------

    def util_status(v):

        if v >= 80:

            return "Excellent"

        elif v >= 60:

            return "Good"

        elif v >= 30:

            return "Average"

        else:

            return "Poor"


    df["Utilization Status"] = (

        df["Utilization %"]

        .apply(util_status)

    )


    # ---------------------------------------------
    # Alerts
    # ---------------------------------------------

    alerts = []


    poor = (

        df["Efficiency"]

        == "Poor"

    ).sum()


    if poor > 0:

        alerts.append(

            {

                "title":

                f"{poor} High Fuel Consumption Machines",

                "type":

                "danger"

            }

        )


    low_util = (

        df["Utilization %"]

        < 25

    ).sum()


    if low_util > 0:

        alerts.append(

            {

                "title":

                f"{low_util} Low Utilization Machines",

                "type":

                "warning"

            }

        )


    unknown = (

        df["Working Type"]

        == "Unknown"

    ).sum()


    if unknown > 0:

        alerts.append(

            {

                "title":

                f"{unknown} Machines Missing Meter Reading",

                "type":

                "warning"

            }

        )


    # ---------------------------------------------
    # Daily Fuel Trend
    # ---------------------------------------------

    daily = (

        df.groupby(

            "Working Date"

        )["Fuel Used"]

        .sum()

        .reset_index()

    )


    # ---------------------------------------------
    # Monthly Trend
    # ---------------------------------------------

    monthly = (

        df.groupby(

            "Month"

        )["Fuel Used"]

        .sum()

        .reset_index()

    )


    # ---------------------------------------------
    # Site Summary
    # ---------------------------------------------

    site = (

        df.groupby(

            "Log Book No."

        )

        .agg(

            Fuel=("Fuel Used", "sum"),

            Hours=("Run Hours", "sum"),

            Machines=("Machine", "nunique")

        )

        .reset_index()

    )


    # ---------------------------------------------
    # Category Summary
    # ---------------------------------------------

    category = (

        df.groupby(

            "Machine Category"

        )

        .agg(

            Fuel=("Fuel Used", "sum"),

            Hours=("Run Hours", "sum"),

            Machines=("Machine", "nunique")

        )

        .reset_index()

    )


    # ---------------------------------------------
    # Machine Summary
    # ---------------------------------------------

    machine = (

        df.groupby(

            "Machine"

        )

        .agg(

            Fuel=("Fuel Used", "sum"),

            Hours=("Run Hours", "sum"),

            Average=("Fuel Average", "mean"),

            Status=("Machine Status", "first"),

            Utilization=("Utilization %", "max")

        )

        .reset_index()

    )


    machine = (

        machine

        .sort_values(

            "Fuel",

            ascending=False

        )

    )


    # ---------------------------------------------
    # Top Consumers
    # ---------------------------------------------

    top10 = (

        machine

        .head(10)

    )


    # ---------------------------------------------
    # Dashboard KPIs
    # ---------------------------------------------

    total_fuel = (

        round(

            df["Fuel Used"]

            .sum(),

            2

        )

    )


    total_hours = (

        round(

            df["Run Hours"]

            .sum(),

            2

        )

    )


    total_machine = (

        df["Machine"]

        .nunique()

    )


    total_site = (

        df["Log Book No."]

        .nunique()

    )


    avg = (

        round(

            df["Fuel Average"]

            .replace(

                0,

                np.nan

            )

            .mean(),

            2

        )

    )


    kpi = {

        "total_fuel":

        total_fuel,

        "total_hours":

        total_hours,

        "total_machine":

        total_machine,

        "total_site":

        total_site,

        "average":

        avg,

        "high_consumption":

        poor,

        "low_utilization":

        low_util

    }


    # ---------------------------------------------
    # Attach Objects
    # ---------------------------------------------

    df.attrs["kpi"] = kpi

    df.attrs["daily"] = daily

    df.attrs["monthly"] = monthly

    df.attrs["site"] = site

    df.attrs["category"] = category

    df.attrs["machine"] = machine

    df.attrs["top10"] = top10

    df.attrs["alerts"] = alerts


    return df
