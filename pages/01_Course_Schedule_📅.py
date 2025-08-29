import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="📘 16-Week Course Schedule", layout="wide")
st.title("📘 Course Schedule")

# Column headers
table_header = "| Date | Chapter | Keywords | Assignments & Activities | Remark |\n"
table_divider = "|------|---------|----------|---------------------------|--------|\n"

# Start on Tuesday, September 2, 2025
start_date = datetime(2025, 9, 2)

# Sample content (you can customize)
chapters = [f"Chapter {i}" for i in range(1, 33)]
keywords = ["Intro", "Digital", "Python", "Variables", "Loops", "Functions", "Design", "Project"] * 4
activities = ["Lecture", "Quiz", "HW", "Group Work", "Discussion", "Coding", "Review", "Presentation"] * 4
remarks = ["", "", "", "", "HW Due", "", "Group Time", "Midterm"] * 4

# Table markdown
table_md = ""

for week in range(16):
    week_label = f"**🗓️ Week {week + 1:02d}**"
    table_md += f"\n{week_label}\n\n"
    table_md += table_header + table_divider

    # Week start dates
    tuesday = start_date + timedelta(weeks=week, days=0)
    thursday = tuesday + timedelta(days=2)

    # Format dates, highlighting Week 6 (Oct. 7 & Oct. 9)
    if week == 5:  # Week 6 (0-based index)
        tuesday_str = f"<span style='color:red'>{tuesday.strftime('%b. %d')}</span>"
        thursday_str = f"<span style='color:red'>{thursday.strftime('%b. %d')}</span>"
    else:
        tuesday_str = tuesday.strftime('%b. %d')
        thursday_str = thursday.strftime('%b. %d')

    # Add rows
    table_md += f"| {tuesday_str} | {chapters[week * 2]} | {keywords[week * 2]} | {activities[week * 2]} | {remarks[week * 2]} |\n"
    table_md += f"| {thursday_str} | {chapters[week * 2 + 1]} | {keywords[week * 2 + 1]} | {activities[week * 2 + 1]} | {remarks[week * 2 + 1]} |\n"

# Render with HTML
st.markdown(table_md, unsafe_allow_html=True)
