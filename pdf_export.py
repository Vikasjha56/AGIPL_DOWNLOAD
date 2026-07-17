from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A3
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Flowable
)
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd


# ==========================================================
# ALERT ICON
# ==========================================================

class AlertIcon(Flowable):

    def __init__(self, level):

        Flowable.__init__(self)

        self.level = str(level)

        self.width = 15
        self.height = 15

    def draw(self):

        level = self.level.lower()

        if "high" in level:

            color = colors.red

        elif "medium" in level:

            color = colors.orange

        elif "low" in level:

            color = colors.green

        else:

            color = colors.grey

        self.canv.setFillColor(color)

        self.canv.circle(
            7,
            7,
            5,
            fill=1
        )


# ==========================================================
# PDF EXPORT
# ==========================================================

def create_pdf(master_df):

    file_path = "AGIPL_Breakdown_Report.pdf"

    master_df = master_df.copy()

    # ======================================================
    # CLEAN COLUMN NAMES
    # ======================================================

    master_df.columns = (
        master_df.columns
        .astype(str)
        .str.strip()
    )

    master_df = master_df.dropna(how="all")


    # ======================================================
    # RENAME SERIAL COLUMN
    # (app.py sends No column)
    # ======================================================

    if "No" in master_df.columns:

        master_df.rename(
            columns={
                "No": "Index Number"
            },
            inplace=True
        )


    # ======================================================
    # CREATE INDEX IF NOT PRESENT
    # ======================================================

    if "Index Number" not in master_df.columns:

        master_df.insert(
            0,
            "Index Number",
            range(
                1,
                len(master_df) + 1
            )
        )


    # ======================================================
    # BREAKDOWN ALERT ICON
    # app.py already sends:
    # Low Alert
    # Medium Alert
    # High Alert
    # ======================================================

    if "Breakdown Alert Icon" in master_df.columns:

        master_df["Alert Icon"] = master_df[
            "Breakdown Alert Icon"
        ].apply(AlertIcon)

    else:

        master_df["Breakdown Alert Icon"] = ""

        master_df["Alert Icon"] = master_df[
            "Breakdown Alert Icon"
        ].apply(AlertIcon)


    # ======================================================
    # COLUMN ORDER
    # EXACT SAME AS breakdown.html
    # ======================================================

    required_columns = [

        "Index Number",

        "Site",

        "Date of breakdown",

        "Category",

        "Vehcile No",

        "Breakdown Details",

        "Reason for pendency",

        "Pending for (no of days)",

        "Owned/Hired",

        "Breakdown Alert Icon",

        "Alert Icon"

    ]


    for col in required_columns:

        if col not in master_df.columns:

            master_df[col] = ""


    final_df = master_df[
        required_columns
    ].copy()


    final_df.rename(

        columns={

            "Vehcile No":"Vehicle No",

            "Date of breakdown":"Date of Breakdown",

            "Reason for pendency":"Reason for Pendency",

            "Pending for (no of days)":"Pending Days",

            "Breakdown Alert Icon":"Alert Level"

        },

        inplace=True

    )


    # ======================================================
    # PDF
    # ======================================================

    doc = SimpleDocTemplate(

        file_path,

        pagesize=landscape(A3),

        leftMargin=18,

        rightMargin=18,

        topMargin=25,

        bottomMargin=20

    )


    styles = getSampleStyleSheet()

    elements = []

    elements.append(

        Paragraph(

            "<b>AGIPL BREAKDOWN PENDING REPORT</b>",

            styles["Title"]

        )

    )

    elements.append(

        Spacer(1,18)

    )


    # ======================================================
    # TABLE DATA
    # ======================================================

    data = []

    data.append(

        [

            Paragraph(

                "<b>"+str(col)+"</b>",

                styles["BodyText"]

            )

            for col in final_df.columns

        ]

    )


    for _, row in final_df.iterrows():

        row_data = []

        for column in final_df.columns:

            value = row[column]

            if column == "Alert Icon":

                row_data.append(value)

            else:

                row_data.append(

                    Paragraph(

                        str(value),

                        styles["BodyText"]

                    )

                )

        data.append(row_data)


    table = Table(

        data,

        repeatRows=1

    )


    table.setStyle(

        TableStyle([

            (

                "BACKGROUND",

                (0,0),

                (-1,0),

                colors.HexColor("#0B3B6F")

            ),

            (

                "TEXTCOLOR",

                (0,0),

                (-1,0),

                colors.white

            ),

            (

                "GRID",

                (0,0),

                (-1,-1),

                0.5,

                colors.grey

            ),

            (

                "FONTNAME",

                (0,0),

                (-1,0),

                "Helvetica-Bold"

            ),

            (

                "FONTSIZE",

                (0,0),

                (-1,-1),

                8

            ),

            (

                "BOTTOMPADDING",

                (0,0),

                (-1,0),

                8

            ),

            (

                "VALIGN",

                (0,0),

                (-1,-1),

                "TOP"

            ),

            (

                "ALIGN",

                (0,0),

                (-1,-1),

                "CENTER"

            ),

            (

                "ROWBACKGROUNDS",

                (0,1),

                (-1,-1),

                [

                    colors.whitesmoke,

                    colors.beige

                ]

            )

        ])

    )


    elements.append(table)

    doc.build(elements)

    print("PDF Report Generated Successfully")

    return file_path
