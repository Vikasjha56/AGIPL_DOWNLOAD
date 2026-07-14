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
# AGIPL CREATE DATA WITH TIME REQUESTS
# ===============================

def create_excel(master_df):

    wb = Workbook()
    ws = wb.active
    ws.title = "Breakdown Report"

    # Report Header
    ws.merge_cells("A1:I1")

    cell = ws["A1"]
    cell.value = "AGIPL BREAKDOWN PENDING REPORT"
    cell.font = title_font
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.fill = PatternFill(fill_type="solid", fgColor=HEADER_COLOR)

    ws["A2"] = "Report Generated"
    ws["B2"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    ws["A2"].font = Font(bold=True)

    ws.freeze_panes = "A6"

    for i in range(1, 500):
        ws.row_dimensions[i].height = 22

    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center")

master_df.columns = master_df.columns.str.strip()

master_df = master_df[
    master_df["Resolved"]
    .astype(str)
    .str.strip()
    .str.upper() == "NO"
].copy()



file_path = "AGIPL_Breakdown_Report.xlsx"

wb.save(file_path)

return file_path
