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
import pytz


# ======================================================
# AGIPL THEME
# ======================================================

HEADER_COLOR = "0B3B6F"
WHITE = "FFFFFF"
BORDER_COLOR = "C9C9C9"


# ======================================================
# BORDER
# ======================================================

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


# ======================================================
# FONT
# ======================================================

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


# ======================================================
# CREATE EXCEL
# ======================================================

def create_excel(master_df):

    # ==================================================
    # CLEAN COLUMN NAMES
    # ==================================================

    master_df = master_df.copy()

    master_df.columns = (
        master_df.columns
        .astype(str)
        .str.strip()
    )


    # ==================================================
    # REMOVE EMPTY ROWS
    # ==================================================

    master_df = master_df.dropna(how="all")


    # ==================================================
    # RENAME SERIAL COLUMN
    # app.py already sends filtered dataframe
    # ==================================================

    if "No" in master_df.columns:

        master_df.rename(
            columns={
                "No": "Index Number"
            },
            inplace=True
        )


    # ==================================================
    # REMOVE OLD INDEX IF DUPLICATE
    # ==================================================

    duplicated = master_df.columns.duplicated()

    if duplicated.any():

        master_df = master_df.loc[:, ~duplicated]


    # ==================================================
    # RECREATE INDEX IF MISSING
    # ==================================================

    if "Index Number" not in master_df.columns:

        master_df.insert(
            0,
            "Index Number",
            range(
                1,
                len(master_df) + 1
            )
        )


    # ==================================================
    # CREATE WORKBOOK
    # ==================================================

    wb = Workbook()

    ws = wb.active

    ws.title = "Breakdown Report"


    last_column = get_column_letter(
        len(master_df.columns)
    )

    ws.merge_cells(
        f"A1:{last_column}1"
    )


    title = ws["A1"]

    title.value = "AGIPL BREAKDOWN PENDING REPORT"

    title.font = title_font

    title.fill = PatternFill(
        fill_type="solid",
        fgColor=HEADER_COLOR
    )

    title.alignment = Alignment(
        horizontal="center",
        vertical="center"
    )

    ws.row_dimensions[1].height = 30


    # ==================================================
    # REPORT DATE
    # ==================================================

    india = datetime.now(
        pytz.timezone("Asia/Kolkata")
    )

    ws["A2"] = "Report Generated"

    ws["B2"] = india.strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )

    ws["A2"].font = Font(
        bold=True
    )


    # ==================================================
    # HEADER
    # ==================================================

    start_row = 5

    for col_num, column in enumerate(
        master_df.columns,
        start=1
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
            vertical="center",
            wrap_text=True
        )

        cell.border = border


    # ==================================================
    # DATA
    # ==================================================

    for row_num, row in enumerate(
        master_df.itertuples(index=False),
        start=start_row + 1
    ):

        for col_num, value in enumerate(
            row,
            start=1
        ):

            cell = ws.cell(
                row=row_num,
                column=col_num
            )

            cell.value = value

            cell.border = border

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )


    # ==================================================
    # COLUMN WIDTH
    # ==================================================

    width_map = {

        "Index Number": 12,

        "Site": 20,

        "Date of breakdown": 18,

        "Category": 22,

        "Vehcile No": 18,

        "Breakdown Details": 45,

        "Reason for pendency": 40,

        "Pending for (no of days)": 18,

        "Owned/Hired": 15,

        "Breakdown Alert Icon": 20

    }


    for column_cells in ws.columns:

        column_index = column_cells[0].column

        letter = get_column_letter(
            column_index
        )

        header = ws.cell(
            row=start_row,
            column=column_index
        ).value


        if header in width_map:

            ws.column_dimensions[
                letter
            ].width = width_map[header]

        else:

            max_len = len(str(header))

            for cell in column_cells:

                if cell.value is not None:

                    max_len = max(
                        max_len,
                        len(str(cell.value))
                    )

            ws.column_dimensions[
                letter
            ].width = min(
                max_len + 3,
                30
            )


    # ==================================================
    # FREEZE HEADER
    # ==================================================

    ws.freeze_panes = "A6"


    # ==================================================
    # ROW HEIGHT
    # ==================================================

    for r in range(
        6,
        ws.max_row + 1
    ):

        ws.row_dimensions[r].height = 42


    # ==================================================
    # SAVE
    # ==================================================

    file_name = "Pending_Breakdown_Report.xlsx"

    wb.save(file_name)

    print("Excel Report Generated Successfully")

    return file_name
