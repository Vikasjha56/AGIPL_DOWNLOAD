import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Border,
    Side,
    Alignment
)

from openpyxl.drawing.image import Image
from datetime import datetime

# ===============================
# AGIPL THEME
# ===============================

HEADER_COLOR = "0B3B6F"
TITLE_COLOR = "163A5F"
WHITE = "FFFFFF"

LOW_COLOR = "D9EAD3"
MEDIUM_COLOR = "FCE5CD"
HIGH_COLOR = "F4CCCC"

BORDER_COLOR = "C9C9C9"

# ===============================
# AGIPL BORDER
# ===============================

thin = Side(
    border_style="thin",
    color=BORDER_COLOR
)

border = Border(
    left=thin,
    right=thin,
    top=thin,
    bottom=thin
)


# ===============================
# AGIPL FONT
# ===============================


title_font = Font(
    size=18,
    bold=True,
    color=WHITE
)

header_font = Font(
    size=11,
    bold=True,
    color=WHITE
)

normal_font = Font(
    size=10
)


# ===============================
# AGIPL CREATE WORKBOOK
# ===============================



wb = Workbook()

ws = wb.active

ws.title = "Breakdown Report"


# ===============================
# AGIPL REPORT HEADER
# ===============================


ws.merge_cells("A1:J1")

cell = ws["A1"]

cell.value = "AGIPL BREAKDOWN PENDING REPORT"

cell.font = title_font

cell.alignment = Alignment(
    horizontal="center",
    vertical="center"
)

cell.fill = PatternFill(
    fill_type="solid",
    fgColor=HEADER_COLOR
)


# ===============================
# AGIPL REPORT DATE
# ===============================



ws["A2"] = "Report Generated"

ws["B2"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")

ws["A2"].font = Font(bold=True)



# ===============================
# AGIPL FREEZE PANES
# ===============================

ws.freeze_panes = "A6"


# ===============================
# AGIPL DEFAULT ROW HEIGHT
# ===============================


for i in range(1,500):

    ws.row_dimensions[i].height = 22



# ===============================
# AGIPL DEFAULT ALIGNMENT
# ===============================

center = Alignment(
    horizontal="center",
    vertical="center"
)

left = Alignment(
    horizontal="left",
    vertical="center"
)

# ===============================
# AGIPL THIS IS MAIN CODE
# ===============================




def create_excel(master_df):

    # ==========================================
    # ONLY PENDING (Resolved = No)
    # ==========================================

    master_df.columns = master_df.columns.str.strip()

    master_df = master_df[
        master_df["Resolved"]
        .astype(str)
        .str.strip()
        .str.upper() == "NO"
    ].copy()


    # ==========================================
    # Fresh Index Number
    # ==========================================

    master_df.reset_index(drop=True, inplace=True)

    master_df["Index Number"] = range(
        1,
        len(master_df) + 1
    )


    # ==========================================
    # Pending Days
    # ==========================================

    master_df["Pending for (no of days)"] = pd.to_numeric(
        master_df["Pending for (no of days)"],
        errors="coerce"
    ).fillna(0)


    # ==========================================
    # Alert Level
    # ==========================================

    def alert(days):

        if days >= 31:
            return "HIGH"

        elif days >= 16:
            return "MEDIUM"

        elif days >= 1:
            return "LOW"

        return "NO BREAKDOWN"


    master_df["Alert Level"] = master_df[
        "Pending for (no of days)"
    ].apply(alert)


    # ==========================================
    # Same Columns as PDF
    # ==========================================

    final_df = master_df[
        [
            "Index Number",
            "Site",
            "Date of breakdown",
            "Category",
            "Vehcile No",
            "Breakdown Details",
            "Reason for pendency",
            "Pending for (no of days)",
            "Alert Level"
        ]
    ].copy()



fOR hEADER

# ==========================================
# FOR HEADER
# ==========================================


    start_row = 5

    headers = list(final_df.columns)

    for col, value in enumerate(headers, 1):

        cell = ws.cell(
            row=start_row,
            column=col
        )

        cell.value = value

        cell.font = header_font

        cell.alignment = center

        cell.border = border

        cell.fill = PatternFill(
            "solid",
            fgColor=TITLE_COLOR
        )






# ==========================================
# DATA FILL
# ==========================================



    row_no = start_row + 1

    for r in final_df.itertuples(index=False):

        for col_no, value in enumerate(r, 1):

            c = ws.cell(
                row=row_no,
                column=col_no
            )

            c.value = value

            c.font = normal_font

            c.border = border

            if col_no in [1, 8]:
                c.alignment = center
            else:
                c.alignment = left







# ==========================================
# ZEBRA FORMATTING
# ==========================================


        if row_no % 2 == 0:

            for x in range(1, 10):

                ws.cell(
                    row=row_no,
                    column=x
                ).fill = PatternFill(
                    "solid",
                    fgColor="F8FBFF"
                )

        row_no += 1
