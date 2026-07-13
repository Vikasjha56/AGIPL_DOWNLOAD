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

    try:

        master = get_master_table()

        print(master.columns.tolist())


        return str(master.columns.tolist())


    except Exception as e:

        return "ERROR : " + str(e)

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
