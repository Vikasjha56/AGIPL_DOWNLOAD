# =====================================================
# fuel_reader.py
# AGIPL Fuel Sheet Reader
# =====================================================

import pandas as pd


FUEL_GOOGLE_SHEET = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKygsnSF9wt3eBxzrJAvwG-gKbUrTEEuxDFT6BsRckeF8SW6k1pJdAsmfld_k1FnWXUBVMeMhZ0jgW/pub?output=csv"
)



def get_fuel_sheet_data():

    try:

        print("Loading Fuel Google Sheet...")


        df = pd.read_csv(
            FUEL_GOOGLE_SHEET
        )


        # Clean column names
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
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
            repr(e)
        )


        return pd.DataFrame()
