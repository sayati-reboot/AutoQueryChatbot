import pandas as pd

def generate_report(results , output_file="report.xlsx"):
    df = results
    # Perform any necessary data processing or formatting
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
        workbook = writer.book
        worksheet = writer.sheets['Report']
        chart = workbook.add_chart({'type': 'column'})
        rows=len(df)
        if rows>0 and len(df.columns)>1:
            chart.add_series({
                'categories': f"'Report'!$A$2:$A${rows+1}",
                'values':     f"'Report'!$B$2:$B${rows+1}",
                'name':       'Report Data',
            })
            worksheet.insert_chart('E2', chart)
    return output_file

