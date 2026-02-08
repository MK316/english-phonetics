import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# PDF (ReportLab)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Passage Blanks Practice", layout="wide")

# ✅ CHANGE THIS to your GitHub RAW CSV URL
CSV_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/refs/heads/main/pages/readings/readingquiz001a.csv"
# Expected columns: Chapter, Passage, Correct answers

@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    # normalize column names just in case
    df.columns = [c.strip() for c in df.columns]
    required = {"Chapter", "Passage", "Correct answers"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {', '.join(sorted(missing))}")
    df["Chapter"] = df["Chapter"].astype(str).str.strip()
    df["Passage"] = df["Passage"].astype(str)
    df["Correct answers"] = df["Correct answers"].astype(str)
    return df

def split_answers(ans: str) -> list[str]:
    # "Phonetics, intelligibly, described" -> ["Phonetics","intelligibly","described"]
    parts = [a.strip() for a in ans.split(",") if a.strip()]
    return parts

def build_pdf_report(
    user_name: str,
    chapter: str,
    passage_no: int,
    started_at: datetime,
    finished_at: datetime,
    score: int,
    total: int,
    incorrect_details: list[dict],
) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Passage Practice Report")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Name: {user_name}")
    y -= 18
    c.drawString(50, y, f"Chapter: {chapter}")
    y -= 18
    c.drawString(50, y, f"Passage #: {passage_no}")
    y -= 18
    c.drawString(50, y, f"Start time: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 18
    c.drawString(50, y, f"Completion time: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 24

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Final score: {score} / {total}")
    y -= 26

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Incorrect items:")
    y -= 18

    c.setFont("Helvetica", 11)
    if not incorrect_details:
        c.drawString(50, y, "None 🎉")
        y -= 18
    else:
        for item in incorrect_details:
            line = f"- Blank {item['blank_index']}: your answer = '{item['user']}' | correct = '{item['correct']}'"
            # basic line wrap
            for chunk in [line[i:i+95] for i in range(0, len(line), 95)]:
                if y < 80:
                    c.showPage()
                    y = height - 60
                    c.setFont("Helvetica", 11)
                c.drawString(50, y, chunk)
                y -= 16

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

# -------------------------
# Load data
# -------------------------
st.title("🧩 Passage Blank Practice")

try:
    df = load_data(CSV_URL)
except Exception as e:
    st.error("Failed to load CSV.")
    st.code(str(e))
    st.stop()

# -------------------------
# UI: select Chapter + Passage
# -------------------------
chapters = sorted(df["Chapter"].dropna().unique().tolist())
colA, colB, colC = st.columns([2, 2, 2])

with colA:
    user_name = st.text_input("Your name (English):", key="user_name")

with colB:
    selected_ch = st.selectbox("Select Chapter:", chapters, key="selected_chapter")

filtered = df[df["Chapter"] == selected_ch].reset_index(drop=True)

with colC:
    passage_idx = st.selectbox(
        "Select Passage number:",
        list(range(1, len(filtered) + 1)),
        key="passage_number",
    )

row = filtered.iloc[passage_idx - 1]
passage_text = row["Passage"]
correct_list = split_answers(row["Correct answers"])

st.caption("Type your name, choose a chapter and passage, then click Start. After submission, you can download a PDF report.")

# -------------------------
# Session state init
# -------------------------
if "started" not in st.session_state:
    st.session_state.started = False
if "started_at" not in st.session_state:
    st.session_state.started_at = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "score" not in st.session_state:
    st.session_state.score = 0
if "incorrect_details" not in st.session_state:
    st.session_state.incorrect_details = []

def do_start():
    st.session_state.started = True
    st.session_state.submitted = False
    st.session_state.score = 0
    st.session_state.incorrect_details = []
    st.session_state.started_at = datetime.now()

def do_reset():
    st.session_state.started = False
    st.session_state.submitted = False
    st.session_state.score = 0
    st.session_state.incorrect_details = []
    st.session_state.started_at = None
    # clear inputs for blanks
    for k in ["blank1", "blank2", "blank3"]:
        if k in st.session_state:
            st.session_state[k] = ""

btn1, btn2 = st.columns([1, 1])
with btn1:
    st.button("✅ Start", on_click=do_start, use_container_width=True)
with btn2:
    st.button("🔄 Reset", on_click=do_reset, use_container_width=True)

st.divider()

# -------------------------
# Main practice area
# -------------------------
if not st.session_state.started:
    st.info("Click **Start** to begin.")
    st.stop()

if "___" not in passage_text:
    st.warning("This passage has no blanks (___). Please check your CSV Passage text.")
    st.stop()

parts = passage_text.split("___")

# Force exactly 3 blanks as you requested
# (If your passage has fewer/more than 3 blanks, we’ll still show 3 inputs,
# but you should keep passages consistent with 3 blanks.)
blank_count = 3

# Ensure correct_list has 3 entries (pad if needed)
while len(correct_list) < blank_count:
    correct_list.append("")
if len(correct_list) > blank_count:
    correct_list = correct_list[:blank_count]

st.subheader(f"{selected_ch} · Passage {passage_idx}")

# Display passage with inputs inline (segment -> input -> segment -> input ...)
# We’ll render in order: parts[0], blank1, parts[1], blank2, parts[2], blank3, rest
for i in range(blank_count):
    # text segment
    if i < len(parts):
        st.write(parts[i])
    # blank input
    st.text_input(f"Blank {i+1}", key=f"blank{i+1}")

# trailing text
if len(parts) > blank_count:
    st.write("___".join(parts[blank_count:]))

st.divider()

def do_submit():
    st.session_state.submitted = True

    user_answers = [
        (st.session_state.get("blank1", "") or "").strip(),
        (st.session_state.get("blank2", "") or "").strip(),
        (st.session_state.get("blank3", "") or "").strip(),
    ]

    incorrect = []
    score = 0

    # Compare case-insensitively, but keep original for report
    for i in range(blank_count):
        ua = user_answers[i]
        ca = correct_list[i].strip()

        if ua.lower() == ca.lower() and ca != "":
            score += 1
        else:
            incorrect.append(
                {"blank_index": i + 1, "user": ua, "correct": ca}
            )

    st.session_state.score = score
    st.session_state.incorrect_details = incorrect

st.button("📩 Submit (check answers)", on_click=do_submit, use_container_width=True)

# -------------------------
# Feedback area
# -------------------------
if st.session_state.submitted:
    st.subheader("Feedback")

    # Per-blank feedback
    for item in range(blank_count):
        ua = (st.session_state.get(f"blank{item+1}", "") or "").strip()
        ca = correct_list[item].strip()

        if ua.lower() == ca.lower() and ca != "":
            st.success(f"Blank {item+1}: Correct ✅")
        else:
            st.error(f"Blank {item+1}: Incorrect ❌  (Correct: {ca})")

    total = blank_count
    st.info("Score is saved for the PDF report (not shown during practice unless you want it).")

    # PDF button
    st.divider()
    if not user_name.strip():
        st.warning("Enter your name above to generate the PDF report.")
    else:
        finished_at = datetime.now()
        pdf_bytes = build_pdf_report(
            user_name=user_name.strip(),
            chapter=selected_ch,
            passage_no=passage_idx,
            started_at=st.session_state.started_at or finished_at,
            finished_at=finished_at,
            score=st.session_state.score,
            total=total,
            incorrect_details=st.session_state.incorrect_details,
        )

        st.download_button(
            "📄 Generate PDF report",
            data=pdf_bytes,
            file_name=f"report_{user_name.strip()}_{selected_ch}_passage{passage_idx}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
