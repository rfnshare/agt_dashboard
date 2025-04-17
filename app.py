from flask import Flask, render_template, request
import pandas as pd
import re
import html
from datetime import datetime

app = Flask(__name__)
EXCEL_FILE = "DC4C0700.xlsx"

# Define expected columns
expected_columns = {
    "Here’s the final version with all duplicates removed:": "Project Info",
    "Week End date": "Week End Date",
    "Team Name": "Team",
    "Team Member Name": "Member",
    "Task Details": "Task",
    "Status": "Status",
    "Achievements": "Achievements",
    "Blockers": "Blockers"
}
# Register a custom date filter
@app.template_filter('date')
def format_date(value, format="%Y-%m-%d"):
    if isinstance(value, datetime):
        return value.strftime(format)
    return value


# Function to clean text
def clean_text(text):
    """Replaces '\n' or '\\n' with actual HTML line breaks"""
    if isinstance(text, str):
        text = text.replace("\\n", "\n")  # Handle double-escaped
        text = html.escape(text)  # Escape HTML tags
        return text.replace("\n", "<br>")
    return ""

# Function to read a specific sheet
def read_sheet(sheet_name):
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
    df = df[list(expected_columns.keys())]
    df.rename(columns=expected_columns, inplace=True)

    # Clean messy fields
    for col in ["Task", "Achievements", "Blockers"]:
        df[col] = df[col].apply(clean_text)

    return df

# Function to filter by date
def filter_by_date(df, start_date, end_date):
    """Filter the DataFrame based on the Week End Date"""
    if start_date:
        df = df[df["Week End Date"] >= start_date]
    if end_date:
        df = df[df["Week End Date"] <= end_date]
    return df

@app.route("/", methods=["GET", "POST"])
def dashboard():
    xls = pd.ExcelFile(EXCEL_FILE)
    sheet_names = xls.sheet_names
    selected_sheet = None
    team_members = []
    selected_member = None
    start_date = None
    end_date = None
    filtered_data = pd.DataFrame()
    tables = None  # HTML table string

    if request.method == "POST":
        selected_sheet = request.form.get("sheet")
        selected_member = request.form.get("member")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        # Convert the date strings to datetime objects
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # Load data
        if selected_sheet and selected_sheet.lower() == "all":
            all_data = []
            for sheet in sheet_names:
                try:
                    df = read_sheet(sheet)
                    df["Sheet Name"] = sheet
                    all_data.append(df)
                except Exception as e:
                    print(f"Error reading sheet {sheet}: {e}")
            data = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
        else:
            try:
                data = read_sheet(selected_sheet)
            except Exception as e:
                print(f"Error reading sheet {selected_sheet}: {e}")
                data = pd.DataFrame()

        if not data.empty:
            # Filter by date range if provided
            if start_date or end_date:
                data = filter_by_date(data, start_date, end_date)

            # Populate team members dropdown
            team_members = data["Member"].dropna().unique().tolist()

            # Filter data by member
            if selected_member and selected_member.lower() != "all":
                filtered_data = data[
                    data["Member"].astype(str).str.strip().str.lower() ==
                    selected_member.strip().lower()
                ]
            else:
                filtered_data = data

            # Replace NaN with empty string
            filtered_data = filtered_data.fillna("")

            # Format messy text columns with line breaks
            for col in ["Task", "Achievements", "Blockers"]:
                if col in filtered_data.columns:
                    filtered_data[col] = (
                        filtered_data[col].astype(str).str.replace(r"\n", "<br>", regex=True)
                    )

            # Convert to Bootstrap styled HTML table
            tables = filtered_data.to_html(
                classes="table table-bordered table-striped table-hover",
                index=False,
                escape=False  # So <br> shows as line breaks
            )

    return render_template(
        "dashboard.html",
        tables=tables,
        sheet_names=sheet_names,
        selected_sheet=selected_sheet,
        selected_member=selected_member,
        team_members=team_members,
        start_date=start_date,
        end_date=end_date
    )


if __name__ == "__main__":
    app.run(debug=False)
