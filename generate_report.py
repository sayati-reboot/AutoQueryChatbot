import pandas as pd


def generate_report(results, query, output_file="report.xlsx"):
    df = results

    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")

        workbook = writer.book
        worksheet = writer.sheets["Report"]
        rows = len(df)

        if rows > 0 and len(df.columns) > 1:
            chart = workbook.add_chart({"type": "column"})

            chart.add_series({
                "categories": f"='Report'!$A$2:$A${rows + 1}",
                "values": f"='Report'!$B$2:$B${rows + 1}",
                "name": "Report Data",
            })

            chart.set_x_axis({
                "interval_unit": 1,
                "num_font": {"rotation": -45},
            })

            chart.set_size({"width": 720, "height": 420})
            worksheet.insert_chart("E2", chart)

    return {
        "query": query,
        "report": output_file,
    }