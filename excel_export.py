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
    # CLEAN COLUMN NAME
    # ===============================

    master_df.columns = (
        master_df.columns
        .str.strip()
    )



    # ===============================
    # REMOVE UNWANTED COLUMNS
    # ===============================

    remove_columns = [
        "No",
        "Index",
        "Index Number",
        "Source Sheet"
    ]


    for col in remove_columns:

        if col in master_df.columns:

            master_df.drop(
                columns=[col],
                inplace=True
            )



    # ===============================
    # FILTER PENDING + OWNED DATA
    # ===============================

    if "Owned/Hired" in master_df.columns:

        master_df = master_df[
            (master_df["Resolved"]
             .astype(str)
             .str.strip()
             .str.upper() == "NO")
            &
            (master_df["Owned/Hired"]
             .astype(str)
             .str.strip()
             .str.upper() == "OWNED")
        ].copy()

    else:

        master_df = master_df[
            master_df["Resolved"]
            .astype(str)
            .str.strip()
            .str.upper() == "NO"
        ].copy()



    # ===============================
    # REMOVE BLANK SITE
    # ===============================

    if "Site" in master_df.columns:

        master_df = master_df[
            master_df["Site"]
            .astype(str)
            .str.strip()
            .ne("")
        ].copy()



    # ===============================
    # CREATE INDEX NUMBER
    # ===============================

    master_df.reset_index(
        drop=True,
        inplace=True
    )


    master_df.insert(
        0,
        "Index Number",
        range(
            1,
            len(master_df) + 1
        )
    )

# ===============================
# ADD ALERT COLUMN
# ===============================

    master_df["Alert"] = ""



    # ===============================
    # CREATE WORKBOOK
    # ===============================

    wb = Workbook()

    ws = wb.active

    ws.title = "Breakdown Report"



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



    # ===============================
    # REPORT DATE TIME
    # ===============================

    india_time = datetime.now(
        pytz.timezone("Asia/Kolkata")
    )


    ws["A2"] = "Report Generated"

    ws["B2"] = india_time.strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )


    ws["A2"].font = Font(
        bold=True
    )



    # ===============================
    # HEADER
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
            vertical="center",
            wrap_text=True
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
                vertical="top",
                wrap_text=True
            )

    # ===============================
# ADD ALERT IMAGE BASED ON DAYS
# ===============================

    alert_column = len(master_df.columns)
    
    
    low_img = "low_alert.png"
    medium_img = "medium_alert.png"
    high_img = "high_alert.png"
    
    
    
    if "Pending for (no of days)" in master_df.columns:
    
    
        days_column = (
            master_df.columns
            .get_loc("Pending for (no of days)") + 1
        )
    
    
        for excel_row, value in enumerate(
            master_df["Pending for (no of days)"],
            start_row + 1
        ):
    
    
            try:
                days = int(value)
    
            except:
                days = 0
    
    
    
            if days <= 7:
    
                image_path = low_img
    
    
            elif days <= 15:
    
                image_path = medium_img
    
    
            else:
    
                image_path = high_img
    
    
    
            if os.path.exists(image_path):
    
                img = Image(image_path)
    
                img.width = 70
                img.height = 18
    
    
                ws.add_image(
                    img,
                    f"{get_column_letter(alert_column)}{excel_row}"
                )
    
    
                ws.row_dimensions[
                    excel_row
                ].height = 25
        
    


  

# ===============================
# COLUMN WIDTH
# ===============================

for column_cells in ws.columns:

    column_number = column_cells[0].column

    column_letter = get_column_letter(
        column_number
    )

    header = ws.cell(
        row=start_row,
        column=column_number
    ).value


    if header == "Index Number":

        ws.column_dimensions[
            column_letter
        ].width = 12


    elif header == "Corrective Action":

        ws.column_dimensions[
            column_letter
        ].width = 35


    elif header == "Alert":

        ws.column_dimensions[
            column_letter
        ].width = 12


    else:

        max_length = 0

        for cell in column_cells:

            if cell.value:

                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws.column_dimensions[
            column_letter
        ].width = min(
            max_length + 3,
            25
        )



    # ===============================
    # ROW SETTINGS
    # ===============================

    ws.freeze_panes = "A6"


    for row in range(
        start_row + 1,
        ws.max_row + 1
    ):

        ws.row_dimensions[row].height = 45



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
