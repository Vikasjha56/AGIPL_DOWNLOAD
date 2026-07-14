import pandas as pd

from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Border,
    Side,
    Alignment
)

from openpyxl.utils import get_column_letter
from datetime import datetime


# ===============================
# AGIPL THEME
# ===============================

HEADER_COLOR = "0B3B6F"
WHITE = "FFFFFF"

BORDER_COLOR = "C9C9C9"


# ===============================
# BORDER
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
# FONT
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


# ===============================
# CREATE EXCEL
# ===============================

def create_excel(master_df):


    # ===============================
    # FILTER PENDING DATA
    # ===============================

    master_df.columns = (
        master_df.columns
        .str.strip()
    )


    master_df = master_df[
        master_df["Resolved"]
        .astype(str)
        .str.strip()
        .str.upper()
        == "NO"
    ].copy()



    # Remove Blank Site

    if "Site" in master_df.columns:

        master_df = master_df[
            master_df["Site"]
            .astype(str)
            .str.strip()
            .ne("")
        ].copy()



    # Reset Sequence

    master_df.reset_index(
        drop=True,
        inplace=True
    )


    # Create Serial Number

    if "No" in master_df.columns:
        master_df.drop(
            columns=["No"],
            inplace=True
        )


    master_df.insert(
        0,
        "No",
        range(
            1,
            len(master_df)+1
        )
    )



    # ===============================
    # CREATE WORKBOOK
    # ===============================


    wb = Workbook()

    ws = wb.active

    ws.title = "Breakdown Report"



    # Dynamic Merge

    last_column = get_column_letter(
        len(master_df.columns)
    )


    ws.merge_cells(
        f"A1:{last_column}1"
    )


    title_cell = ws["A1"]

    title_cell.value = (
        "AGIPL BREAKDOWN PENDING REPORT"
    )

    title_cell.font = title_font

    title_cell.alignment = Alignment(
        horizontal="center",
        vertical="center"
    )

    title_cell.fill = PatternFill(
        fill_type="solid",
        fgColor=HEADER_COLOR
    )


    ws.row_dimensions[1].height = 30



    # Report Date

    ws["A2"] = "Report Generated"

    ws["B2"] = datetime.now().strftime(
        "%d-%m-%Y %I:%M %p"
    )

    ws["A2"].font = Font(
        bold=True
    )



    # ===============================
    # TABLE HEADER
    # ===============================


    start_row = 5


    for col_num, column in enumerate(
        master_df.columns,
        1
    ):

        cell = ws.cell(
            row=start_row,
            column=col_num
        )

        cell.value = column

        cell.font = header_font

        cell.fill = PatternFill(
            fill_type="solid",
            fgColor=HEADER_COLOR
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        cell.border = border




    # ===============================
    # INSERT DATA
    # ===============================


    for row_num, row in enumerate(
        master_df.values,
        start_row + 1
    ):

        for col_num, value in enumerate(
            row,
            1
        ):

            cell = ws.cell(
                row=row_num,
                column=col_num
            )

            cell.value = value

            cell.border = border

            cell.alignment = Alignment(
                vertical="center"
            )



    # Freeze Header

    ws.freeze_panes = "A6"



    # Row Height

    for row in ws.iter_rows():

        for cell in row:

            cell.border = border



    # ===============================
    # AUTO COLUMN WIDTH
    # ===============================


    for column_cells in ws.columns:

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


        ws.column_dimensions[
            column_letter
        ].width = max_length + 3



    # ===============================
    # SAVE FILE
    # ===============================


    output_file = (
        "Pending_Breakdown_Report.xlsx"
    )


    wb.save(
        output_file
    )


    print(
        "Pending Excel Report Created Successfully"
    )


    return output_file
