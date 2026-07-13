from flask import Flask, send_file
from google_reader import get_master_table
from excel_export import create_excel
from pdf_export import create_pdf
from flask import Flask, send_file, render_template

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

    import json


    master = get_master_table()


    # Pending Only

    pending = master[
        master["Resolved"].astype(str).str.lower()=="no"
    ]



    # Total Pending

    total_pending = len(pending)



    # Pending >15 Days

    pending_15 = pending[
        pending["Pending for (no of days)"] > 15
    ]



    pending_15_count = len(pending_15)




    # Range Function

    def day_range(x):

        if x <=7:
            return "0-7 Days"

        elif x <=15:
            return "8-15 Days"

        elif x <=30:
            return "16-30 Days"

        elif x <=60:
            return "31-60 Days"

        else:
            return "60+ Days"




    pending["Range"] = pending[
        "Pending for (no of days)"
    ].apply(day_range)



    # Range Count

    range_data = (
        pending
        .groupby("Range")
        .size()
    )



    range_labels = list(range_data.index)

    range_values = list(range_data.values)




    # Machine Wise >15

    machine_data = (
        pending_15
        .groupby("Machine")
        .size()
        .sort_values(ascending=False)
        .head(10)
    )



    machine_labels=list(machine_data.index)

    machine_values=list(machine_data.values)




    # Site Doughnut

    site_data = (
        pending
        .groupby("Site")
        .size()
    )



    site_labels=list(site_data.index)

    site_values=list(site_data.values)





    # Pending Distribution >15


    dist_data = (
        pending_15
        .groupby("Range")
        .size()
    )



    dist_labels=list(dist_data.index)

    dist_values=list(dist_data.values)




    return render_template(

        "breakdown.html",

        total_pending=total_pending,

        pending_15=pending_15_count,


        range_labels=json.dumps(range_labels),

        range_values=json.dumps(range_values),


        machine_labels=json.dumps(machine_labels),

        machine_values=json.dumps(machine_values),


        site_labels=json.dumps(site_labels),

        site_values=json.dumps(site_values),


        dist_labels=json.dumps(dist_labels),

        dist_values=json.dumps(dist_values)

    )


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
