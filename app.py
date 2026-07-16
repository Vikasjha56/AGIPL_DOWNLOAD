import csv
import io
import os
import time

import requests
from flask import Flask, send_file, render_template, request
import pandas as pd

from google_reader import get_master_table
from excel_export import create_excel
from pdf_export import create_pdf
from reminder_scheduler import start_scheduler


app = Flask(__name__)


# ==========================
# CACHE SYSTEM
# ==========================

MASTER_CACHE = None
CACHE_TIME = 0
CACHE_DURATION = 300


def get_cached_master():
    """Loads Master Table from Google Sheets with a 5-minute cache."""
    global MASTER_CACHE, CACHE_TIME
    current_time = time.time()
    if MASTER_CACHE is None or current_time - CACHE_TIME > CACHE_DURATION:
        print("Loading Google Sheets Data...")
        try:
            df = get_master_table()
        except Exception as err:
            print("GOOGLE SHEET LOAD FAILED:", repr(err))
            raise
        print("Rows fetched:", len(df))
        print("Columns fetched:", df.columns.tolist())
        MASTER_CACHE = df
        CACHE_TIME = current_time
    else:
        print("Using Cached Data...")
    return MASTER_CACHE.copy()


# ==========================
# ALERT LEVEL LOGIC
# (Low: 0-15 days, Medium: 16-30 days, High: 31+ days)
# ==========================

def alert_level(days):
    if days > 30:
        return "High Alert"
    if days >= 16:
        return "Medium Alert"
    return "Low Alert"


# ==========================
# BUILD PENDING DATAFRAME
# (shared by /breakdown view AND the Excel/PDF export routes
#  so both always show the exact same numbers)
# ==========================

def build_pending_df(master):
    master.columns = master.columns.astype(str).str.strip()

    required = ["Resolved", "Site", "Category", "Reason for pendency", "Pending for (no of days)"]
    missing = [c for c in required if c not in master.columns]
    if missing:
        raise ValueError(
            f"Master Table is missing required column(s): {missing}. "
            f"Actual columns found: {master.columns.tolist()}"
        )

    resolved_col = master["Resolved"].astype(str).str.strip().str.upper()
    pending = master.loc[resolved_col == "NO"].copy()

    pending.loc[:, "Pending Days"] = pd.to_numeric(
        pending["Pending for (no of days)"], errors="coerce"
    )
    pending = pending.dropna(subset=["Pending Days"]).copy()
    pending.loc[:, "Pending Days"] = pending["Pending Days"].astype(int)

    # Optional columns — filled defensively in case sheet doesn't have them yet
    if "Owned/Hired" not in pending.columns:
        pending["Owned/Hired"] = "Not Defined"
    if "Date of breakdown" not in pending.columns:
        pending["Date of breakdown"] = ""
    if "Breakdown Details" not in pending.columns:
        pending["Breakdown Details"] = ""
    if "Vehcile No" not in pending.columns:
        pending["Vehcile No"] = ""

    # normalize date -> ISO string (yyyy-mm-dd) for slicer / sorting / export
    pending["Date Parsed"] = pd.to_datetime(
        pending["Date of breakdown"], errors="coerce", dayfirst=True
    )
    pending["Date ISO"] = pending["Date Parsed"].dt.strftime("%Y-%m-%d").fillna("")

    pending["Alert"] = pending["Pending Days"].apply(alert_level)

    pending = pending.reset_index(drop=True)
    pending["No"] = pending.index + 1

    return pending


# ==========================
# APPLY QUERY-STRING FILTERS
# (used by the Excel / PDF export routes so downloads match
#  whatever the user currently has selected/sorted on screen)
# ==========================

SORT_COLUMN_MAP = {
    "no": "No",
    "site": "Site",
    "date": "Date ISO",
    "category": "Category",
    "vehicle": "Vehcile No",
    "details": "Breakdown Details",
    "reason": "Reason for pendency",
    "days": "Pending Days",
    "owned": "Owned/Hired",
    "alert": "Alert",
}


def apply_filters_and_sort(pending, args):
    site = args.get("site", "All")
    owned = args.get("owned", "All")
    sort_key = args.get("sort", "no")
    sort_dir = args.get("dir", "asc")

    df = pending.copy()

    if site and site != "All":
        df = df[df["Site"] == site]
    if owned and owned != "All":
        df = df[df["Owned/Hired"] == owned]

    col = SORT_COLUMN_MAP.get(sort_key, "No")
    ascending = sort_dir != "desc"
    df = df.sort_values(by=col, ascending=ascending)

    return df


def build_export_df(df):
    """Final column set / order that goes into Excel & PDF —
    matches the BD Details table exactly, Stock Alert Level excluded."""
    export = pd.DataFrame({
        "No": df["No"],
        "Site": df["Site"],
        "Date of breakdown": df["Date of breakdown"],
        "Category": df["Category"],
        "Vehcile No": df["Vehcile No"],
        "Breakdown Details": df["Breakdown Details"],
        "Reason for pendency": df["Reason for pendency"],
        "Pending for (no of days)": df["Pending Days"],
        "Owned/Hired": df["Owned/Hired"],
        "Breakdown Alert Icon": df["Alert"],
    })
    return export


# ==========================
# CRITICAL PENDING TASK
# (separate published Google Sheet — Work Allotted To / Allotted By tracker)
# ==========================

CRITICAL_SHEET_CSV = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhICKU0riazqlJ1LaBoIr-3PC19f3QPG0"
    "UCMPQL5VX0xkVsP80usEtcyF2xyroKILDxgBoYp9j4WdX/pub?output=csv"
)

CRITICAL_CACHE = None
CRITICAL_CACHE_TIME = 0
CRITICAL_CACHE_DURATION = 300  # 5 minutes, same as the Master Table cache


def task_alert_level(days):
    """Alert tiers for day-to-day pending tasks — tighter than the
    machine-breakdown SLA above. Adjust the two cutoffs if needed."""
    if days >= 7:
        return "High Alert"
    if days >= 3:
        return "Medium Alert"
    return "Low Alert"


def fetch_critical_records():
    """Fetches + parses the Critical Pending Task sheet.
    Skips blank/incomplete rows (e.g. a row that only has 'Allotted By' filled in)."""
    resp = requests.get(CRITICAL_SHEET_CSV, timeout=10)
    resp.encoding = "utf-8"
    reader = csv.DictReader(io.StringIO(resp.text))

    records = []
    for row in reader:
        sno = (row.get("S.No.") or "").strip()
        assigned_to = (row.get("Work Allotted To") or "").strip()
        if not sno or not assigned_to:
            continue

        try:
            days = int(float(row.get("Pending Since (No of Days)") or 0))
        except ValueError:
            days = 0

        records.append({
            "sno": sno,
            "assigned_to": assigned_to,
            "contact_no": (row.get("Contact No") or "").strip(),
            "details": (row.get("Details of work") or "").strip(),
            "date": (row.get("Allotted on Date") or "").strip(),
            "allotted_by": (row.get("Allotted By") or "").strip(),
            "days": days,
            "alert": task_alert_level(days),
        })
    return records


def get_cached_critical_records():
    """Same 5-minute cache pattern as the Master Table, so the scheduler
    and the /critical-pending page both read consistent data."""
    global CRITICAL_CACHE, CRITICAL_CACHE_TIME
    current_time = time.time()
    if CRITICAL_CACHE is None or current_time - CRITICAL_CACHE_TIME > CRITICAL_CACHE_DURATION:
        print("Loading Critical Pending Task sheet...")
        CRITICAL_CACHE = fetch_critical_records()
        CRITICAL_CACHE_TIME = current_time
    else:
        print("Using Cached Critical Pending Data...")
    return CRITICAL_CACHE


@app.route("/critical-pending")
def critical_pending():
    try:
        records = get_cached_critical_records()
        return render_template("critical_pending.html", critical_records=records)
    except Exception as e:
        print("CRITICAL PENDING ERROR:", e)
        return "Critical Pending Task Error : " + str(e)


# ==========================
# HOME
# ==========================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# EXCEL DOWNLOAD (filter + sort aware)
# ==========================

@app.route("/download_excel")
def download_excel():
    try:
        print("Creating Master Table for Excel...")
        master = get_cached_master()
        pending = build_pending_df(master)
        filtered = apply_filters_and_sort(pending, request.args)
        export_df = build_export_df(filtered)
        print("Generating Excel...")
        file_path = create_excel(export_df)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Excel Error : {str(e)}"


# ==========================
# PDF DOWNLOAD (filter + sort aware)
# ==========================

@app.route("/download_pdf")
def download_pdf():
    try:
        print("Creating Master Table for PDF...")
        master = get_cached_master()
        pending = build_pending_df(master)
        filtered = apply_filters_and_sort(pending, request.args)
        export_df = build_export_df(filtered)
        print("Generating PDF...")
        file_path = create_pdf(export_df)
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
#  slicer change / chart click / column-header sort)
# ==========================

@app.route("/breakdown")
def breakdown():
    try:
        master = get_cached_master()

        try:
            pending = build_pending_df(master)
        except Exception as err:
            print("GOOGLE SHEET ERROR:", err)
            return "Google Sheet Loading Error : " + str(err)

        resolved_col = master["Resolved"].astype(str).str.strip().str.upper()
        resolved = master[resolved_col == "YES"].copy()

        # ======================
        # ROW-LEVEL RECORDS FOR CLIENT-SIDE FILTERING
        # ======================
        pending_records = [
            {
                "no": int(row["No"]),
                "category": str(row.get("Category", "Not Defined") or "Not Defined"),
                "site": str(row.get("Site", "Not Defined") or "Not Defined"),
                "days": int(row["Pending Days"]),
                "reason": str(row.get("Reason for pendency", "Not Defined") or "Not Defined"),
                "date": str(row.get("Date of breakdown", "") or ""),
                "dateIso": str(row.get("Date ISO", "") or ""),
                "vehicle": str(row.get("Vehcile No", "") or ""),
                "details": str(row.get("Breakdown Details", "") or ""),
                "owned": str(row.get("Owned/Hired", "Not Defined") or "Not Defined"),
                "alert": str(row.get("Alert", "Low Alert") or "Low Alert"),
            }
            for _, row in pending.iterrows()
        ]

        resolved_records = [
            {"site": str(row.get("Site", "Not Defined") or "Not Defined")}
            for _, row in resolved.iterrows()
        ]

        owned_options = sorted(
            {r["owned"] for r in pending_records if r["owned"] not in ("", "Not Defined")}
        )

        return render_template(
            "breakdown.html",
            pending_records=pending_records,
            resolved_records=resolved_records,
            owned_options=owned_options,
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
# WHATSAPP REMINDER SCHEDULER
# Sends a WhatsApp reminder to the assignee (Contact No) and their
# supervisor (manually maintained list in reminder_scheduler.py) every
# 24 hours for as long as a task stays pending. See reminder_scheduler.py
# to plug in your Twilio credentials and supervisor phone numbers.
# ==========================

if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    start_scheduler(get_cached_critical_records)


# ==========================
# LOCAL RUN
# ==========================

if __name__ == "__main__":
    app.run()
