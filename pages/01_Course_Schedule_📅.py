import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="📘 16-Week Course Schedule", layout="wide")
st.title("📘 Course Schedule")

# Table header
table_header = "| Date | Chapter | Keywords | Assignments & Activities | Remark |\n"
table_divider = "|------|---------|----------|---------------------------|--------|\n"

# Start on Tuesday, September 2, 2025
start_date = datetime(2025, 9, 2)

# ✅ STEP 1: Fill only the weeks you want — here, Week 3 has data (Sept. 16 & 18)
schedule_content = {
    "2025-09-16": [
        "Functions",
        "Parameters, Return",
        "Practice Quiz",
        "HW1 Due"
    ],
    "2025-09-18": [
        "Review",
        "All Topics",
        '<a href="https://forms.gle/your-form-link" target="_blank">🔗 Peer Review Form</a>',
        ""
    ]
}

# ✅ STEP 2: Build the markdown table
table_md = ""

for week in range(16):
    week_label = f"**🗓️ Week {week + 1:02d}**"
    table_md += f"\n{week_label}\n\n"
    table_md += table_header + table_divider

    # Tuesday and Thursday of the current week
    tuesday = start_date + timedelta(weeks=week)
    thursday = tuesday + timedelta(days=2)

    # Date strings for lookup and display
    tuesday_key = tuesday.strftime('%Y-%m-%d')
    thursday_key = thursday.strftime('%Y-%m-%d')

    def format_date(date_obj):
        date_str = date_obj.strftime('%Y-%m-%d')
        if date_str in ["2025-10-07", "2025-10-09"]:  # Week 6
            return f"<span style='color:red'>{date_obj.strftime('%b. %d')}</span>"
        return date_obj.strftime('%b. %d')

    # Get content or use blanks
    tue_data = schedule_content.get(tuesday_key, ["", "", "", ""])
    thu_data = schedule_content.get(thursday_key, ["", "", "", ""])

    # Add the two rows
    table_md += f"| {format_date(tuesday)} | {tue_data[0]} | {tue_data[1]} | {tue_data[2]} | {tue_data[3]} |\n"
    table_md += f"| {format_date(thursday)} | {thu_data[0]} | {thu_data[1]} | {thu_data[2]} | {thu_data[3]} |\n"

# ✅ STEP 3: Display it
st.markdown(table_md, unsafe_allow_html=True)
