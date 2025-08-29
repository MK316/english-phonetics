import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="📘 16-Week Course Schedule", layout="wide")
st.title("📘 Course Schedule")

# Column headers
table_header = "| Date | Chapter | Keywords | Assignments & Activities | Remark |\n"
table_divider = "|------|---------|----------|---------------------------|--------|\n"

# Start on Tuesday, September 2, 2025
start_date = datetime(2025, 9, 2)

table_md = ""

for week in range(16):
    week_label = f"**🗓️ Week {week + 1:02d}**"
    table_md += f"\n{week_label}\n\n"
    table_md += table_header + table_divider

    # Week's Tuesday and Thursday
    tuesday = start_date + timedelta(weeks=week, days=0)
    thursday = tuesday + timedelta(days=2)

    # Highlight Week 6 dates (Oct. 7 and Oct. 9)
    if week == 5:
        tuesday_str = f"<span style='color:red'>{tuesday.strftime('%b. %d')}</span>"
        thursday_str = f"<span style='color:red'>{thursday.strftime('%b. %d')}</span>"
    else:
        tuesday_str = tuesday.strftime('%b. %d')
        thursday_str = thursday.strftime('%b. %d')

    # Add empty content rows with just the date
    table_md += f"| {tuesday_str} |  |  |  |  |\n"
    table_md += f"| {thursday_str} |  |  |  |  |\n"

# Render with HTML styling enabled
st.markdown(table_md, unsafe_allow_html=True)
