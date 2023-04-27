from db import find_with_pipeline
from dataframes import (
    pipeline_to_dataframe,
    process_dataframe,
    group_by,
    excel_to_dataframe,
)
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
)


def build_date_choices():
    now = datetime.now()
    year = now.year
    prev_2_years = [year - 2, year - 1]

    years = prev_2_years + [year]
    months = [
        "JANUARY",
        "FEBRUARY",
        "MARCH",
        "APRIL",
        "MAY",
        "JUNE",
        "JULY",
        "AUGUST",
        "SEPTEMBER",
        "OCTOBER",
        "NOVEMBER",
        "DECEMBER",
    ]

    return [f"{month}{year}" for year in years for month in months]


@app.get("/")
def read_root():
    valid_months = build_date_choices()
    gpos = ["PREMIER", "MEDASSETS", "MAGNET", "HEALTHTRUST"]

    html = """
    <html>
        <head>
            <title>Rebate Tracing</title>
        </head>
        <body>
            <h1>Rebate Tracing</h1>
            <p>
                Enter a GPO, start date, and end date to generate a rebate tracing
                 report.
            </p>
            
            <datalist id="months">"""

    for month in valid_months:
        html += f"<option value='{month}'>"

    html += """
            </datalist>
            <datalist id="gpos">"""

    for gpo in gpos:
        html += f"<option value='{gpo}'>"

    html += """</datalist>
            <form action="/report">
                <label for="gpo">GPO</label>
                <input type="text" id="gpo" name="gpo" list="gpos"><br><br>
                <label for="start">Start Date</label>
                <input type="text" id="start" name="start" list="months"><br><br>
                <label for="end">End Date</label>
                <input type="text" id="end" name="end" list="months"><br><br>
                <label for="rerun">Rerun</label>
                <input type="checkbox" id="rerun" name="rerun"><br><br>
                <input type="submit" value="Submit">
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)


@app.get("/report")
def generate_report(gpo: str, start: str, end: str, rerun: bool = False):
    valid_months = build_date_choices()

    gpo = gpo.strip().upper()
    start = start.strip().upper()
    end = end.strip().upper()

    start_index = valid_months.index(start)
    end_index = valid_months.index(end)

    try:
        valid_months = valid_months[start_index : end_index + 1]
    except IndexError:
        return HTMLResponse(
            content="<p>Invalid date range. Please try again.</p>",
            status_code=400,
        )

    OUTPUT_FILENAME = f"{gpo}_{start}_{end}.xlsx"
    GROUPED_OUTPUT_FILENAME = f"grouped_{OUTPUT_FILENAME}"

    if (
        os.path.exists(os.path.join("reports", OUTPUT_FILENAME))
        and os.path.exists(os.path.join("reports", GROUPED_OUTPUT_FILENAME))
        and not rerun
    ):
        df = excel_to_dataframe(os.path.join("reports", OUTPUT_FILENAME))
        grouped_df = excel_to_dataframe(
            os.path.join("reports", GROUPED_OUTPUT_FILENAME)
        )
    else:
        pipeline = [
            {
                "$match": {
                    "gpo": gpo,
                    "period": {"$regex": "|".join(valid_months)},
                },
            }
        ]

        df = pipeline_to_dataframe(find_with_pipeline, pipeline)
        df = process_dataframe(df)

        df.to_excel(os.path.join("reports", OUTPUT_FILENAME), index=False)

        grouped_df = group_by(df)

        grouped_df.to_excel(
            os.path.join("reports", GROUPED_OUTPUT_FILENAME), index=True
        )

    date_of_file = os.path.getmtime(os.path.join("reports", OUTPUT_FILENAME))
    date_of_file = datetime.fromtimestamp(date_of_file).strftime("%m/%d/%Y %H:%M:%S")

    if len(df) > 100:
        sample_df = df.head(100)
        df_html = sample_df.to_html(index=False)
    else:
        df_html = df.to_html(index=False)

    grouped_df_html = grouped_df.to_html(index=True)

    html = f"""
    <html>
        <head>
            <title>Rebate Tracing</title>
        </head>
        <body>
            <h1>Rebate Tracing</h1>
            <p>Report(s) generated successfully.</p>
            <p>Report generated on {date_of_file}</p>
            <br>
            <hr />
            <br>

            <a id="grouped_report" href="/download/{GROUPED_OUTPUT_FILENAME}">
                Download Grouped Report
            </a>
            <details>
            <summary>Click to see grouped report</summary>            
    """
    html += grouped_df_html
    html += f"""
            </details>
            <br><br>
            <a id="detailed_report" href="/download/{OUTPUT_FILENAME}">
                Download Detailed Report
            </a>
            <details>
            <summary>
                Click to see detailed report 
                (*sample first 100 rows* -> download to see full report)
            </summary>
    """
    html += df_html
    html += """
            </details>

            <br><br>
            <a style="margin:auto;" href="/">Return to home page</a>
        </body>
    </html>
    """

    return HTMLResponse(content=html, status_code=200)


@app.get("/download/{OUTPUT_FILENAME}")
def download_report(OUTPUT_FILENAME: str):
    file = os.path.join("reports", OUTPUT_FILENAME)
    return FileResponse(file, media_type="application/vnd.ms-excel")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
