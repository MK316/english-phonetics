import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="📘 16-Week Course Schedule", layout="wide")
st.title("📘 Course Schedule")

schedule_content = {
    "2025-09-16": ["Functions", "Parameters, Return", "Practice Quiz", "HW1 Due"],
    "2025-09-18": ["Review", "All Topics", "Peer Review", ""],
    "2025-10-07": ["Midterm Review", "Core Concepts", "Kahoot + Quiz", ""],
    "2025-10-09": ["Midterm", "", "In-Class Test", ""]
}

# Column headers
table_header = "| Date | Chapter | Keywords | Assignments & Activities | Remark |\n"
table_divider = "|------|---------|----------|---------------------------|--------|\n"

# Start on Tuesday, September 2, 2025
start_date = datetime(2025, 9, 2)

# Step 1: Define only the content you want to appear
schedule_content = {
    "2025-09-16": ["Functions", "Parameters, Return", "Practice Quiz", "HW1 Due"],
    "2025-09-18": ["Review", "All Topics", "Peer Review", ""],
    "2025-10-07": ["Midterm Review", "Core Concepts", "Kahoot + Quiz", ""],
    "2025-10-09": ["Midterm", "", "In-Class Test", ""]
}

table_md = ""

for week in range(16):
    week_label = f"**🗓️ Week {week + 1:02d}**"
    table_md += f"\n{week_label}\n\n"
    table_md += table_header + table_divider

    # Tuesday and Thursday of the current week
    tuesday = start_date + timedelta(weeks=week)
    thursday = tuesday + timedelta(days=2)

    # Format dates
    tuesday_key = tuesday.strftime('%Y-%m-%d')
    thursday_key = thursday.strftime('%Y-%m-%d')

    # Red highlight only for Oct 7 and 9 (Week 6)
    def style_date(date_obj):
        if date_obj.strftime('%Y-%m-%d') in ["2025-10-07", "2025-10-09"]:
            return f"<span style='color:red'>{date_obj.strftime('%b. %d')}</span>"
        return date_obj.strftime('%b. %d')

    # Look up content or default to blank
    tue_data = schedule_content.get(tuesday_key, ["", "", "", ""])
    thu_data = schedule_content.get(thursday_key, ["", "", "", ""])

    # Add the two rows
    table_md += f"| {style_date(tuesday)} | {tue_data[0]} | {tue_data[1]} | {tue_data[2]} | {tue_data[3]} |\n"
    table_md += f"| {style_date(thursday)} | {thu_data[0]} | {thu_data[1]} | {thu_data[2]} | {thu_data[3]} |\n"

# Display the table
st.markdown(table_md, unsafe_allow_html=True)
