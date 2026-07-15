from reportlab.lib import colors
import pandas as pd
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


# -----------------------------
# Alert Icon Drawing
# -----------------------------

class AlertIcon(Flowable):

    def __init__(self, level):

        Flowable.__init__(self)

        self.level = level

        self.width = 15
        self.height = 15



    def draw(self):

        if "High" in self.level:

            color = colors.red


        elif "Medium" in self.level:

            color = colors.orange


        elif "Low" in self.level:

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



# -----------------------------
# PDF Generator
# -----------------------------

def create_pdf(master_df):


    file_path = "AGIPL_Breakdown_Report.pdf"



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




    # Fresh Sequence

    master_df["Index Number"] = range(
        1,
        len(master_df)+1
    )



    # Stock Alert Logic

    def alert_level(days):

        try:

            qty = float(days)


            if qty >=1 and qty <=15:

                return "C [Low Alert]"


            elif qty >=16 and qty <=30:

                return "B [Medium Alert]"


            elif qty >=31 and qty <=10000:

                return "A [High Alert]"


            else:

                return "[No Breakdown]"


        except:

            return "[No Breakdown]"



    master_df["Stock Alert Level"] = (
        master_df["Pending for (no of days)"]
        .apply(alert_level)
    )


	# Required Columns

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
			"Stock Alert Level"
		]
	].copy()


	# Convert Pending Days to Integer

	final_df["Pending for (no of days)"] = (
		pd.to_numeric(
			final_df["Pending for (no of days)"],
			errors="coerce"
		)
		.fillna(0)
		.astype(int)
	)


	# Alert Icon Column

	final_df["Alert Icon"] = (
		final_df["Stock Alert Level"]
		.apply(AlertIcon)
	)


	# Rename Columns

	final_df.columns = [
		"Index Number",
		"Site",
		"Date of Breakdown",
		"Category",
		"Vehicle No",
		"Breakdown Details",
		"Reason for Pendency",
		"Pending (No of Days)",
		"Stock Alert Level",
		"Alert Icon"
	]







    # PDF

    doc = SimpleDocTemplate(

        file_path,

        pagesize=landscape(A3),

        rightMargin=20,

        leftMargin=20,

        topMargin=30,

        bottomMargin=30

    )



    styles = getSampleStyleSheet()


    elements = []


    elements.append(

        Paragraph(

            "AGIPL Breakdown Pending Report",

            styles["Heading2"]

        )

    )


    elements.append(
        Spacer(1,20)
    )



    # Wrap text

    data = [

        [

            Paragraph(
                str(col),
                styles["Normal"]
            )

            for col in final_df.columns

        ]

    ]



    for _, row in final_df.iterrows():

        data.append(

            [

                Paragraph(
                    str(value),
                    styles["Normal"]
                )

                if column != "Alert Icon"

                else value

                for column,value in zip(
                    final_df.columns,
                    row
                )

            ]

        )



    table = Table(

        data,

        repeatRows=1

    )



    table.setStyle(

        TableStyle(

            [

                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.black
                ),


                (
                    "BACKGROUND",
                    (0,0),
                    (-1,0),
                    colors.lightgrey
                ),


                (
                    "FONTSIZE",
                    (0,0),
                    (-1,-1),
                    7
                ),


                (
                    "VALIGN",
                    (0,0),
                    (-1,-1),
                    "TOP"
                )

            ]

        )

    )



    elements.append(table)


    doc.build(elements)



    return file_path
