from flask import Flask, render_template, request
import pandas as pd
import re
import html
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

# Function to read a specific sheet







def clean_text(text):
    """Replaces '\n' or '\\n' with actual HTML line breaks"""
    if isinstance(text, str):
        text = text.replace("\\n", "\n")  # Handle double-escaped
        text = html.escape(text)  # Escape HTML tags
        return text.replace("\n", "<br>")
    return ""



def read_sheet(sheet_name):
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
    df = df[list(expected_columns.keys())]
    df.rename(columns=expected_columns, inplace=True)

    # Clean messy fields
    for col in ["Task", "Achievements", "Blockers"]:
        df[col] = df[col].apply(clean_text)

    return df

@app.route("/", methods=["GET", "POST"])
def dashboard():
    xls = pd.ExcelFile(EXCEL_FILE)
    sheet_names = xls.sheet_names
    selected_sheet = None
    team_members = []
    selected_member = None
    filtered_data = pd.DataFrame()
    tables = None  # HTML table string

    if request.method == "POST":
        selected_sheet = request.form.get("sheet")
        selected_member = request.form.get("member")

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
        team_members=team_members
    )



if __name__ == "__main__":
    app.run(debug=True)
