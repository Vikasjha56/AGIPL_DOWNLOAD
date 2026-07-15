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
# EXCEL DOWNLOAD (full master export - unchanged)
# ==========================

@app.route("/download_excel")
def download_excel():
    try:
        print("Creating Master Table for Excel...")
        master = get_master_table()
        print("Generating Excel...")
        file_path = create_excel(master)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Excel Error : {str(e)}"


# ==========================
# PDF DOWNLOAD (full master export - unchanged)
# ==========================

@app.route("/download_pdf")
def download_pdf():
    try:
        print("Creating Master Table for PDF...")
        master = get_master_table()
        print("Generating PDF...")
        file_path = create_pdf(master)
        return send_file(file_path, as_attachment=True)
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
# (sends ROW-LEVEL data as JSON so the client can cross-filter
#  KPIs + all 4 charts + BD Details table together on every
#  click / slicer change, including Owned/Hired + Date range +
#  Breakdown Alert Icon filters, and export filtered Excel/PDF
#  directly in the browser)
# ==========================

@app.route("/breakdown")
def breakdown():
    global MASTER_CACHE, CACHE_TIME

    try:
        current_time = time.time()

        # ======================
        # LOAD DATA WITH CACHE
        # ======================
        if MASTER_CACHE is None or current_time - CACHE_TIME > CACHE_DURATION:
            print("Loading Google Sheets Data...")
            try:
                MASTER_CACHE = get_master_table()
                CACHE_TIME = current_time
            except Exception as err:
                print("GOOGLE SHEET ERROR:", err)
                return "Google Sheet Loading Error : " + str(err)
        else:
            print("Using Cached Data...")

        master = MASTER_CACHE.copy()
        master.columns = master.columns.astype(str).str.strip()

        # ---- DEBUG INFO shown directly on the page (top banner) so no
        # terminal access is needed to diagnose an empty dashboard ----
        debug_info = {
            "total_rows": len(master),
            "columns": list(master.columns),
            "resolved_values": [],
            "resolved_no_count": 0,
            "dropped_non_numeric": 0,
        }

        if "Resolved" not in master.columns:
            debug_info["error"] = "'Resolved' column NOT FOUND in sheet."
            return render_template(
                "breakdown.html",
                pending_records=[],
                resolved_records=[],
                debug_info=debug_info,
            )

        debug_info["resolved_values"] = (
            master["Resolved"].astype(str).str.strip().unique().tolist()
        )

        # ======================
        # RESOLVED = NO FILTER (pending set)
        # ======================
        resolved_col = master["Resolved"].astype(str).str.strip().str.upper()
        pending = master[resolved_col == "NO"].copy()
        resolved = master[resolved_col == "YES"].copy()
        debug_info["resolved_no_count"] = len(pending)

        if "Pending for (no of days)" not in master.columns:
            debug_info["error"] = "'Pending for (no of days)' column NOT FOUND in sheet."
            return render_template(
                "breakdown.html",
                pending_records=[],
                resolved_records=[],
                debug_info=debug_info,
            )

        pending["Pending Days"] = pd.to_numeric(
            pending["Pending for (no of days)"], errors="coerce"
        )
        before_drop = len(pending)
        pending = pending.dropna(subset=["Pending Days"])
        debug_info["dropped_non_numeric"] = before_drop - len(pending)
        pending["Pending Days"] = pending["Pending Days"].astype(int)

        # ======================
        # ROW-LEVEL RECORDS FOR CLIENT-SIDE FILTERING
        # NOTE: added date / vehicleNo / details / ownedHired fields
        # so the client can build the "Owned/Hired" slicer, the
        # date-range slicer, and the BD Details table exactly like
        # the reference screenshot (minus "Stock Alert Level").
        # If your Google Sheet uses different header names than the
        # ones below, just update the .get(...) keys accordingly.
        # ======================
        pending_records = [
            {
                "category": str(row.get("Category", "Not Defined") or "Not Defined"),
                "site": str(row.get("Site", "Not Defined") or "Not Defined"),
                "days": int(row["Pending Days"]),
                "reason": str(row.get("Reason for pendency", "Not Defined") or "Not Defined"),
                "date": str(row.get("Date of breakdown", "") or ""),
                "vehicleNo": str(
                    row.get("Vehcile No", row.get("Vehicle No", "Not Defined")) or "Not Defined"
                ),
                "details": str(row.get("Breakdown Details", "Not Defined") or "Not Defined"),
                "ownedHired": str(row.get("Owned/Hired", "Not Defined") or "Not Defined"),
            }
            for _, row in pending.iterrows()
        ]

        resolved_records = [
            {"site": str(row.get("Site", "Not Defined") or "Not Defined")}
            for _, row in resolved.iterrows()
        ]

        debug_info["final_pending_records"] = len(pending_records)
        return render_template(
            "breakdown.html",
            pending_records=pending_records,
            resolved_records=resolved_records,
            debug_info=debug_info,
        )

    except Exception as e:
        print("BREAKDOWN ERROR:", e)
        return "Breakdown Error : " + str(e)


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
