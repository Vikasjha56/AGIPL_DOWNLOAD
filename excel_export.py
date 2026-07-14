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

# ===============================
# CREATE EXCEL
# ===============================

def create_excel(master_df):

    wb = Workbook()
    ws = wb.active
    ws.title = "Breakdown Report"

    # Header
    ws.merge_cells("A1:I1")

    cell = ws["A1"]
    cell.value = "AGIPL BREAKDOWN PENDING REPORT"
    cell.font = title_font
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.fill = PatternFill(fill_type="solid", fgColor=HEADER_COLOR)

    # Report Date
    ws["A2"] = "Report Generated"
    ws["B2"] = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    ws["A2"].font = Font(bold=True)

    # Freeze Pane
    ws.freeze_panes = "A6"

    # Row Height
    for i in range(1, 500):
        ws.row_dimensions[i].height = 22

    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center")

       # Filter Pending Data

    master_df.columns = master_df.columns.str.strip()

    master_df = master_df[
        master_df["Resolved"]
        .astype(str)
        .str.strip()
        .str.upper() == "NO"
    ].copy()
    
    
    # Remove Blank Site Rows (if required)
    
    if "Site" in master_df.columns:
        master_df = master_df[
            master_df["Site"]
            .astype(str)
            .str.strip()
            .ne("")
        ].copy()
    
    
    # Reset Index Sequence
    
    master_df.reset_index(drop=True, inplace=True)
    
    # Create Serial Number Column
    
    master_df.insert(
        0,
        "No",
        range(1, len(master_df) + 1)
    )
    
    
    # Create Excel File
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    
    output_file = "Pending_Breakdown_Report.xlsx"
    
    
    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:
    
        master_df.to_excel(
            writer,
            index=False,
            sheet_name="Pending Data"
        )
    
    
        workbook = writer.book
        worksheet = writer.sheets["Pending Data"]
    
    
        # Header Formatting
    
        header_fill = PatternFill(
            start_color="1F4E78",
            end_color="1F4E78",
            fill_type="solid"
        )
    
        header_font = Font(
            bold=True,
            color="FFFFFF"
        )
    
    
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(
                horizontal="center"
            )
    
    
        # Border
    
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )
    
    
        for row in worksheet.iter_rows():
    
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(
                    vertical="center"
                )
    
    
        # Auto Column Width
    
        for column_cells in worksheet.columns:
    
            max_length = 0
    
            column_letter = get_column_letter(
                column_cells[0].column
            )
    
            for cell in column_cells:
    
                if cell.value:
                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )
    
            worksheet.column_dimensions[
                column_letter
            ].width = max_length + 3
    
    
    print("Pending Excel Report Created Successfully")
