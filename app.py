# ============================================================
# PASTE 1: add near the top of app.py, right after the other
# cache blocks (MASTER_CACHE / CRITICAL_CACHE), BEFORE any
# @app.route definitions.
# ============================================================

FUEL_CACHE = None
FUEL_CACHE_TIME = 0
FUEL_CACHE_DURATION = 300  # 5 minutes, same pattern as get_cached_master()


def get_cached_fuel_raw():
    """Loads the raw Fuel sheet with a 5-minute cache, so /fuel opens
    instantly on repeat visits instead of hitting Google Sheets every time."""
    global FUEL_CACHE, FUEL_CACHE_TIME
    current_time = time.time()
    if FUEL_CACHE is None or current_time - FUEL_CACHE_TIME > FUEL_CACHE_DURATION:
        print("Loading Fuel Sheet...")
        FUEL_CACHE = get_fuel_sheet_data()
        FUEL_CACHE_TIME = current_time
    else:
        print("Using Cached Fuel Data...")
    return FUEL_CACHE.copy()


# ============================================================
# PASTE 2: replace the ENTIRE existing /fuel route (both the
# duplicate stub AND the real one) with just this single route.
# ============================================================

@app.route("/fuel")
def fuel():
    try:
        raw = get_cached_fuel_raw()

        if raw.empty:
            return render_template("fuel.html", fuel_records=[], error="No data rows found in the published sheet.")

        df = prepare_fuel_analysis(raw)

        fuel_records = [
            {
                "srNo": i + 1,
                "date": row["Working Date"],
                "dateIso": row["Date ISO"],
                "monthKey": row["Month Key"],
                "monthLabel": row["Month Label"],
                "site": row["Site Name"],
                "category": row["Machine Category"],
                "machine": row["Machine"],
                "owner": row["Owner"],
                "opening": round(float(row["Opening Reading"]), 2),
                "closing": round(float(row["Closing Reading"]), 2),
                "readingType": row["Reading Type"],
                "runReading": round(float(row["Run Reading"]), 2),
                "fuel": round(float(row["Fuel Used"]), 2),
                "hours": round(float(row["Run Hours"]), 2),
                "avg": round(float(row["Fuel Average"]), 2),
                "status": row["Machine Status"] if row["Machine Status"] else "Not Defined",
                "work": row["Work Done"],
            }
            for i, row in df.iterrows()
        ]

        return render_template("fuel.html", fuel_records=fuel_records, error=None)

    except Exception as e:
        print("FUEL PAGE ERROR:", repr(e))
        return render_template("fuel.html", fuel_records=[], error=str(e))
