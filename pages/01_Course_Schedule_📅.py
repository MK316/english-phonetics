import streamlit as st

st.title("📘 Course Schedule")

# Define schedule data
schedule = {
    "Week 01": ["Mar 4", "Intro to Course", "Ice-breaker", "Set up GitHub"],
    "Week 02": ["Mar 11", "Digital Literacy", "Discussion", "Survey 1"],
    "Week 03": ["Mar 18", "Basic Python", "Jupyter Notebook", "HW1 due"],
    "Week 04": ["Mar 25", "Variables & Input", "Practice", "HW2 out"],
    "Week 05": ["Apr 1", "Control Structures", "Coding Quiz", ""],
    "Week 06": ["Apr 8", "Functions", "In-class demo", "Group task start"],
    "Week 07": ["Apr 15", "App Design", "Wireframes", "Read article"],
    "Week 08": ["Apr 22", "Midterm Project", "Team plan", "Presentation"],
    "Week 09": ["Apr 29", "Streamlit Basics", "Example Apps", ""],
    "Week 10": ["May 6", "Streamlit Inputs", "App Practice", "HW3 due"],
    "Week 11": ["May 13", "App Polish", "Peer Review", ""],
    "Week 12": ["May 20", "TTS & Audio", "Gradio intro", ""],
    "Week 13": ["May 27", "App Deployment", "HuggingFace", "HW4 due"],
    "Week 14": ["Jun 3", "Final App Work", "Group time", "Final push"],
    "Week 15": ["Jun 10", "Final Presentation", "Team showcase", ""],
    "Week 16": ["Jun 17", "Wrap-up", "Reflection", "Survey 2"],
}

# Markdown table header
table_md = """
| Date | Topic | Task | Note |
|------|-------|------|------|
"""

# Generate markdown string
full_md = ""
week_num = 1

for week, content in schedule.items():
    # Add Week row
    full_md += f"\n**🗓️ {week}**\n\n"
    # Add table header
    full_md += table_md
    # Add content row
    full_md += f"| {content[0]} | {content[1]} | {content[2]} | {content[3]} |\n"

# Display the full table
st.markdown(full_md)
