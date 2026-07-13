from flask import Flask, send_file
from google_reader import get_master_table
from excel_export import create_excel
from pdf_export import create_pdf
from flask import Flask, render_template

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




if __name__ == "__main__":

    app.run(debug=True)
