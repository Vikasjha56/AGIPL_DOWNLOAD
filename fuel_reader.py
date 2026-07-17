# =====================================================
# AGIPL FUEL GOOGLE SHEET READER
# =====================================================


import pandas as pd
import requests

from io import StringIO

from fuel_config import FUEL_GOOGLE_SHEET



def get_fuel_sheet_data():

    try:

        response = requests.get(
            FUEL_GOOGLE_SHEET,
            timeout=30
        )


        response.raise_for_status()


        df = pd.read_csv(
            StringIO(response.text)
        )


        # remove extra spaces from headers

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )


        # remove empty rows

        df = df.dropna(
            how="all"
        )


        return df



    except Exception as e:


        print(
            "FUEL DATA ERROR :",
            e
        )


        return pd.DataFrame()
