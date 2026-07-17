# =====================================================
# fuel_reader.py
# AGIPL Fuel Sheet Reader
# =====================================================

import pandas as pd
import requests


FUEL_GOOGLE_SHEET = (
"https://docs.google.com/spreadsheets/d/e/2PACX-1vT3e08cKMWasrA0FhI8Z8lAhSwgswvOoyYijyqGbHqetAUk-ga0LP3NuoCcVyMp7A/pub?output=csv"
)



def get_fuel_sheet_data():

    try:

        print("Loading Fuel Google Sheet...")


        df = pd.read_csv(
            FUEL_GOOGLE_SHEET
        )


        print(
            "Fuel Rows:",
            len(df)
        )


        print(
            "Fuel Columns:",
            df.columns.tolist()
        )


        return df



    except Exception as e:

        print(
            "Fuel Sheet Error:",
            e
        )

        return pd.DataFrame()
