import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


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