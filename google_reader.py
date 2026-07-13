import pandas as pd
from config import GOOGLE_SHEETS


print("Total Google Sheets Found :", len(GOOGLE_SHEETS))


def get_master_table():

    all_data = []

    for index, url in enumerate(GOOGLE_SHEETS, start=1):

        print("\n==========================")
        print("Reading Sheet :", index)
        print("==========================")

        try:

            df = pd.read_csv(url)

            df = df.dropna(how="all")

            df["Source Sheet"] = f"Sheet {index}"

            all_data.append(df)

            print("Status : SUCCESS")
            print("Rows :", len(df))
            print("Columns :", len(df.columns))


        except Exception as e:

            print("Status : FAILED")
            print(e)


    print("\nTotal Sheets Loaded :", len(all_data))


    master = pd.concat(
        all_data,
        ignore_index=True
    )


    master.insert(
        0,
        "Index Number",
        range(1, len(master)+1)
    )


    return master



if __name__ == "__main__":


    master = get_master_table()


    print("\n==============================")
    print("MASTER TABLE CREATED")
    print("==============================")

    print("Total Rows :", len(master))
    print("Total Columns :", len(master.columns))

    print("\nSource Sheet Count:")
    print(master["Source Sheet"].value_counts())
