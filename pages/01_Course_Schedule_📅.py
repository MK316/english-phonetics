import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="📘 16-Week Course Schedule", layout="wide")
st.title("📘 Course Schedule")

# Table column header
table_header = "| Date | Chapter | Keywords | Assignments & Activities | Remark |\n"
table_divider = "|------|---------|----------|---------------------------|--------|\n"

# Start date (Tuesday, Week 1)
start_date = datetime(2025, 9, 2)

# Placeholder data (customize as needed)
chapters = [f"Chapter {i}" for i in range(1, 33)]
keywords = ["Intro", "Digital", "Python", "Variables", "Loops", "Functions", "Design", "Project"] * 4
activities = ["Lecture", "Quiz", "HW", "Group Work", "Discussion", "Coding", "Review", "Presentation"] * 4
remarks = ["", "", "", "", "HW Due", "", "Group Time", "Midterm"] * 4

table_md = ""

# Build week-by-week table
for week in range(16):
    week_label = f"**🗓️ Week {week + 1:02d}**"
    table_md += f"\n{week_label}\n\n"
    table_md += table_header + table_divider

    # Tuesday row
    tuesday = start_date + timedelta(weeks=week, days=0)
    table_md += f"| {tuesday.strftime('%b. %d')} | {chapters[week * 2]} | {keywords[week * 2]} | {activities[week * 2]} | {remarks[week * 2]} |\n"

    # Thursday row
    thursday = tuesday + timedelta(days=2)
    table_md += f"| {thursday.strftime('%b. %d')} | {chapters[week * 2 + 1]} | {keywords[week * 2 + 1]} | {activities[week * 2 + 1]} | {remarks[week * 2 + 1]} |\n"

# Render table
st.markdown(table_md)
