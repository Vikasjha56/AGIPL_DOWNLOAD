import time

MASTER_CACHE = None
CACHE_TIME = 0
CACHE_DURATION = 300




from flask import Flask, send_file, render_template
import pandas as pd

from google_reader import get_master_table
from excel_export import create_excel
from pdf_export import create_pdf

app = Flask(__name__)


@app.route("/")
def home():

    return render_template("index.html")



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


# ===============================
# AGIPL MODULE PAGES
# ===============================

@app.route("/modules")
def modules():
    return render_template("modules.html")


@app.route("/reports")
def reports():
    return render_template("reports.html")


@app.route("/breakdown")
def breakdown():

    global MASTER_CACHE, CACHE_TIME

    try:

        current_time = time.time()


        # CACHE SYSTEM

        if (
            MASTER_CACHE is None
            or current_time - CACHE_TIME > CACHE_DURATION
        ):

            print("Loading Google Sheets Data...")

            MASTER_CACHE = get_master_table()

            CACHE_TIME = current_time


        else:

            print("Using Cached Data...")


        master = MASTER_CACHE


        master.columns = master.columns.str.strip()



        # Pending Cases

        pending = master[
            master["Resolved"]
            .astype(str)
            .str.strip()
            .str.upper()
            == "NO"
        ].copy()



        pending["Pending Days"] = pd.to_numeric(
            pending["Pending for (no of days)"],
            errors="coerce"
        )



        pending_count = len(pending)



        pending_15 = len(
            pending[
                pending["Pending Days"] > 15
            ]
        )



        return render_template(
            "breakdown.html",
            pending_count=pending_count,
            pending_15=pending_15
        )


    except Exception as e:

        print("BREAKDOWN ERROR :", e)

        return "Breakdown Error : " + str(e)
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




if __name__ == "__main__":

    app.run(debug=True)
