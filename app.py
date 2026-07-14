import time

from flask import Flask, send_file, render_template
import pandas as pd

from google_reader import get_master_table
from excel_export import create_excel
from pdf_export import create_pdf


app = Flask(__name__)


# ==========================
# CACHE SYSTEM
# ==========================

MASTER_CACHE = None
CACHE_TIME = 0
CACHE_DURATION = 300




# ==========================
# HOME
# ==========================

@app.route("/")
def home():

    return render_template("index.html")





# ==========================
# EXCEL DOWNLOAD
# ==========================

@app.route("/download_excel")
def download_excel():

    try:

        print("Creating Master Table for Excel...")

        master = get_master_table()


        print("Generating Excel...")


        file_path = create_excel(master)


        return send_file(
            file_path,
            as_attachment=True
        )


    except Exception as e:

        return f"Excel Error : {str(e)}"







# ==========================
# PDF DOWNLOAD
# ==========================

@app.route("/download_pdf")
def download_pdf():

    try:

        print("Creating Master Table for PDF...")


        master = get_master_table()


        print("Generating PDF...")


        file_path = create_pdf(master)


        return send_file(
            file_path,
            as_attachment=True
        )


    except Exception as e:

        return f"PDF Error : {str(e)}"







# ==========================
# MODULES
# ==========================

@app.route("/modules")
def modules():

    return render_template("modules.html")




@app.route("/reports")
def reports():

    return render_template("reports.html")






# ==========================
# BREAKDOWN DASHBOARD
# ==========================

@app.route("/breakdown")
def breakdown():

    global MASTER_CACHE, CACHE_TIME


    try:


        current_time = time.time()



        # ======================
        # LOAD DATA WITH CACHE
        # ======================


        if (
            MASTER_CACHE is None
            or current_time - CACHE_TIME > CACHE_DURATION
        ):


            print("Loading Google Sheets Data...")


            try:

                MASTER_CACHE = get_master_table()


                CACHE_TIME = current_time


            except Exception as err:


                print(
                    "GOOGLE SHEET ERROR:",
                    err
                )


                return (
                    "Google Sheet Loading Error : "
                    + str(err)
                )



        else:


            print("Using Cached Data...")




        master = MASTER_CACHE.copy()



        master.columns = (
            master.columns
            .astype(str)
            .str.strip()
        )



        print(
            "Columns:",
            master.columns.tolist()
        )






        # ======================
        # RESOLVED = NO FILTER
        # ======================


        pending = master[

            master["Resolved"]
            .astype(str)
            .str.strip()
            .str.upper()
            ==
            "NO"

        ].copy()





        pending["Pending Days"] = pd.to_numeric(

            pending["Pending for (no of days)"],

            errors="coerce"

        )






        # ======================
        # KPI
        # ======================


        pending_count = len(pending)



        pending_15_data = pending[

            pending["Pending Days"] > 15

        ]



        pending_15 = len(
            pending_15_data
        )






        # ======================
        # AGE RANGE
        # ======================


        range_data = {


            "0-7 Days":

            len(
                pending[
                    (pending["Pending Days"] >=0)
                    &
                    (pending["Pending Days"] <=7)
                ]
            ),



            "8-15 Days":

            len(
                pending[
                    (pending["Pending Days"] >=8)
                    &
                    (pending["Pending Days"] <=15)
                ]
            ),



            "16-30 Days":

            len(
                pending[
                    (pending["Pending Days"] >=16)
                    &
                    (pending["Pending Days"] <=30)
                ]
            ),



            "31+ Days":

            len(
                pending[
                    pending["Pending Days"] >30
                ]
            )

        }







        # ======================
        # MACHINE WISE
        # ======================


        machine_data = (

            pending_15_data["Category"]

            .fillna("Not Defined")

            .value_counts()

            .head(10)

        )






        # ======================
        # SITE WISE
        # ======================


        site_data = (

            pending["Site"]

            .fillna("Not Defined")

            .value_counts()

        )







        # ======================
        # REASON WISE
        # ======================


        reason_data = (

            pending_15_data["Reason for pendency"]

            .fillna("Not Defined")

            .value_counts()

        )








        return render_template(


            "breakdown.html",



            pending_count=pending_count,



            pending_15=pending_15,




            range_labels=list(
                range_data.keys()
            ),


            range_values=list(
                range_data.values()
            ),




            machine_labels=
            machine_data.index.tolist(),



            machine_values=
            machine_data.values.tolist(),





            site_labels=
            site_data.index.tolist(),



            site_values=
            site_data.values.tolist(),





            reason_labels=
            reason_data.index.tolist(),



            reason_values=
            reason_data.values.tolist()

        )





    except Exception as e:


        print(
            "BREAKDOWN ERROR:",
            e
        )


        return (
            "Breakdown Error : "
            + str(e)
        )








# ==========================
# OTHER MODULES
# ==========================


@app.route("/fuel")
def fuel():

    return render_template("fuel.html")



@app.route("/hr")
def hr():

    return render_template("hr.html")



@app.route("/purchase")
def purchase():

    return render_template("purchase.html")



@app.route("/sales")
def sales():

    return render_template("sales.html")



@app.route("/machinery")
def machinery():

    return render_template("machinery.html")



@app.route("/assets")
def assets():

    return render_template("assets.html")



@app.route("/it")
def it():

    return render_template("it.html")





# ==========================
# LOCAL RUN
# ==========================

if __name__ == "__main__":

    app.run()
