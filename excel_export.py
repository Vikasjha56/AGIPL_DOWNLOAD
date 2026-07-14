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

    file_path = "AGIPL_Master_Table.xlsx"

    with pd.ExcelWriter(
        file_path,
        engine="openpyxl"
    ) as writer:

        master_df.to_excel(
            writer,
            index=False,
            sheet_name="Master Table"
        )


        workbook = writer.book

        worksheet = writer.sheets["Master Table"]


        # Header Formatting

        for cell in worksheet[1]:

            cell.font = Font(
                bold=True
            )

            cell.alignment = Alignment(
                horizontal="center"
            )


        # Auto Column Width

        for column in worksheet.columns:

            max_length = 0

            column_letter = get_column_letter(
                column[0].column
            )

            for cell in column:

                try:

                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))

                except:
                    pass


            worksheet.column_dimensions[
                column_letter
            ].width = max_length + 3



        # Freeze Header

        worksheet.freeze_panes = "A2"



    return file_path
