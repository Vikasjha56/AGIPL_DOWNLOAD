# =====================================================
# AGIPL FUEL ANALYSIS ENGINE
# =====================================================


import pandas as pd
import re




def prepare_fuel_analysis(df):


    if df.empty:

        return df



    # ---------------------------------
    # CLEAN HEADER
    # ---------------------------------

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )



    # ---------------------------------
    # DATE
    # ---------------------------------

    df["Working Date"] = pd.to_datetime(
        df["Working Date"],
        errors="coerce"
    )


    df["Month"] = (
        df["Working Date"]
        .dt.strftime("%b-%Y")
    )



    # ---------------------------------
    # NUMBER CONVERSION
    # ---------------------------------


    numeric_columns = [

        "From Reading",
        "To Reading",
        "Time Op. Reading",
        "Time Cls. Reading",
        "Fuel Issue",
        "Consumption",
        "Average"

    ]


    for col in numeric_columns:


        if col in df.columns:


            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)



    # ---------------------------------
    # RUN HOURS LOGIC
    # ---------------------------------

    df["Run Hours"] = 0



    # CASE 1
    # Time Reading available


    time_condition = (

        (df["Time Op. Reading"] > 0)
        &
        (df["Time Cls. Reading"] > 0)

    )



    df.loc[
        time_condition,
        "Run Hours"
    ] = (

        df.loc[
            time_condition,
            "Time Cls. Reading"
        ]

        -

        df.loc[
            time_condition,
            "Time Op. Reading"
        ]

    )




    # CASE 2
    # From To Reading


    reading_condition = (
        ~time_condition
    )



    df.loc[
        reading_condition,
        "Run Hours"
    ] = (

        df.loc[
            reading_condition,
            "To Reading"
        ]

        -

        df.loc[
            reading_condition,
            "From Reading"
        ]

    )




    # remove negative values

    df["Run Hours"] = (
        df["Run Hours"]
        .clip(lower=0)
        .round(2)
    )




    # ---------------------------------
    # FUEL USED
    # ---------------------------------

    df["Fuel Used"] = (

        df["Fuel Issue"]
        .fillna(0)

    )





    # ---------------------------------
    # AVERAGE LTR / HR
    # ---------------------------------


    df["Fuel Average"] = 0



    df.loc[
        df["Run Hours"] > 0,
        "Fuel Average"
    ] = (

        df["Fuel Used"]

        /

        df["Run Hours"]

    ).round(2)






    # ---------------------------------
    # MACHINE RTO EXTRACTION
    # ---------------------------------


    def get_rto(machine):


        if pd.isna(machine):

            return ""


        text=str(machine)


        result = re.findall(
            r'[A-Z]{2}\d{2}[A-Z]{1,2}\d{3,4}',
            text.upper()
        )


        if result:

            return result[0]


        return ""



    df["RTO Number"] = (

        df["Machine"]
        .apply(get_rto)

    )






    # ---------------------------------
    # STATUS
    # ---------------------------------


    def consumption_status(avg):


        if avg >= 15:

            return "High"


        elif avg >= 8:

            return "Normal"


        else:

            return "Low"



    df["Consumption Status"] = (

        df["Fuel Average"]
        .apply(consumption_status)

    )




    return df
