import re
import unicodedata
import streamlit as st
import pandas as pd
from gtts import gTTS
from io import BytesIO
import random
from datetime import datetime
from zoneinfo import ZoneInfo
import textwrap

# ---------------- Page setup ----------------
st.set_page_config(page_title="Term Practice", page_icon="📘", layout="wide")
st.markdown("#### 📘 Term Practice: Text, Audio, and Quiz")

# ---------------- Load glossary data ----------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/MK316/classmaterial/main/Phonetics/ch01_glossary_0915.csv"
    df = pd.read_csv(url)
    df = df.dropna(subset=["Term", "Description"])
    if "Word count" in df.columns:
        df["Word count"] = pd.to_numeric(df["Word count"], errors="coerce").fillna(0).astype(int)
    else:
        df["Word count"] = 0
    if "Syllable" in df.columns:
        df["Syllable"] = pd.to_numeric(df["Syllable"], errors="coerce").astype("Int64")
    else:
        df["Syllable"] = pd.Series([pd.NA] * len(df), dtype="Int64")
    return df

df = load_data()

# ---------------- TTS Cache ----------------
@st.cache_data(show_spinner=False)
def tts_bytes(text: str) -> bytes:
    fp = BytesIO()
    gTTS(text).write_to_fp(fp)
    fp.seek(0)
    return fp.read()

# ---------------- Helpers ----------------
def word_count_from_row(row) -> int:
    try:
        wc = int(row["Word count"])
        return wc if wc > 0 else 1
    except Exception:
        return len(str(row.get("Term", "")).split()) or 1

def syllable_count_from_row(row):
    try:
        s = int(row["Syllable"])
        return s if s > 0 else None
    except Exception:
        return None

def answer_prompt(row) -> str:
    wc = word_count_from_row(row)
    syl = syllable_count_from_row(row)
    bits = [f"{wc} word{'s' if wc != 1 else ''}"]
    if syl is not None:
        bits.append(f"{syl} syllable{'s' if syl != 1 else ''}")
    return "Type your answer: (" + ", ".join(bits) + ")"

def hint_from_term(term: str, underscores: int = 4) -> str:
    words = re.split(r"\s+", str(term).strip())
    hinted = [w[0].lower() + "_" * underscores for w in words if w]
    return " ".join(hinted)

# ---------------- Tabs ----------------
tab1, tab2, tab3 = st.tabs(["📝 Text Practice", "🔊 Audio Practice", "🧪 Audio Quiz"])

# ---------------- Tab 1 ----------------
with tab1:
    st.subheader("✍️ Practice Terms with Text Descriptions")
    HINT_UNDERSCORES = 4
    num_items = st.number_input("How many terms to practice?", min_value=1, max_value=len(df), value=3)

    if "text_items" not in st.session_state or st.button("🔄 New Text Practice"):
        st.session_state.text_items = df.sample(num_items).reset_index(drop=True)
        st.session_state.text_answers = [""] * num_items

    for i, row in st.session_state.text_items.iterrows():
        desc = str(row["Description"]).strip()
        term = str(row["Term"]).strip()
        st.markdown(f"**{i+1}. {desc}**")
        st.markdown(f"<div style='opacity:0.7'>Hint: <code>{hint_from_term(term)}</code></div>", unsafe_allow_html=True)
        st.write(answer_prompt(row))
        st.session_state.text_answers[i] = st.text_input(f"Your answer {i+1}", value=st.session_state.text_answers[i])

    if st.button("✅ Check Answers (Text)"):
        score = 0
        for i, row in st.session_state.text_items.iterrows():
            gold = " ".join(str(row["Term"]).strip().lower().split())
            guess = " ".join(str(st.session_state.text_answers[i]).strip().lower().split())
            if guess == gold:
                score += 1
                st.success(f"{i+1}. Correct!")
            else:
                st.error(f"{i+1}. Incorrect. ✅ Correct: **{row['Term']}**")
        st.success(f"Your score: {score} / {len(st.session_state.text_items)}")
        if score == len(st.session_state.text_items):
            st.balloons()

# ---------------- Tab 2 ----------------
with tab2:
    st.subheader("🔊 Audio Practice (Guess the Term from Description)")

    num_items = st.slider("How many items would you like to practice?", 1, 10, 3)

    if st.button("🎧 Generate Practice Set"):
        st.session_state.practice_set = df.sample(num_items).reset_index(drop=True)
        st.session_state.audio_answers = [""] * num_items

    if "practice_set" in st.session_state and st.session_state.practice_set is not None:
        for i, row in st.session_state.practice_set.iterrows():
            # Generate audio from description
            text = row["Description"]
            tts = gTTS(text)
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)

            # Play audio
            st.audio(mp3_fp.getvalue(), format="audio/mp3")

            # Word count hint
            word_count = row["Word count"]
            label = f"Your answer {i+1} ({word_count} word{'s' if word_count > 1 else ''})"

            # Input with unique key
            st.session_state.audio_answers[i] = st.text_input(
                label,
                value=st.session_state.audio_answers[i],
                key=f"answer_input_{i}"
            )

        # Check answers
        if st.button("✅ Check Answers"):
            score = 0
            for i, row in st.session_state.practice_set.iterrows():
                correct = row["Term"].strip().lower()
                user_answer = st.session_state.audio_answers[i].strip().lower()

                if user_answer == correct:
                    st.success(f"Item {i+1}: Correct!")
                    score += 1
                else:
                    st.error(f"Item {i+1}: Incorrect. Correct answer: {correct}")

            st.info(f"🎯 Your Score: {score} / {len(st.session_state.practice_set)}")


# ---------------- Tab 3 ----------------
# ---------------- Tab 3 ----------------
with tab3:
    st.subheader("🧪 Audio Quiz: One-by-One Mode")

    # Session state initialization
    for var, default in {
        "quiz_user": "",
        "quiz_started": False,
        "quiz_idx": 0,
        "quiz_order": [],
        "quiz_answers": [],
        "quiz_start_time": None,
        "quiz_end_time": None,
    }.items():
        if var not in st.session_state:
            st.session_state[var] = default

    # Name and Start
    name_col, start_col = st.columns([2, 1])
    with name_col:
        user = st.text_input("Enter your name", value=st.session_state.quiz_user)
    with start_col:
        if st.button("▶️ Start Quiz"):
            if not user.strip():
                st.warning("Please enter your name.")
            else:
                st.session_state.quiz_user = user.strip()
                st.session_state.quiz_order = df.sample(frac=1).index.tolist()
                st.session_state.quiz_answers = [""] * len(st.session_state.quiz_order)
                st.session_state.quiz_idx = 0
                st.session_state.quiz_started = True
                st.session_state.quiz_start_time = datetime.now()
                st.rerun()

    if st.session_state.quiz_started:
        idx = st.session_state.quiz_idx
        total = len(st.session_state.quiz_order)
        row = df.loc[st.session_state.quiz_order[idx]]

        st.info(f"Question {idx+1} of {total}")
        st.audio(tts_bytes(row["Description"]), format="audio/mp3")
        st.write(answer_prompt(row))

        # Show input with reset key
        answer_key = f"quiz_answer_{idx}"

        user_answer = st.text_input("Your answer:", key=answer_key)
        st.session_state.quiz_answers[idx] = user_answer

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⏮️ Restart"):
                st.session_state.quiz_started = False
                st.rerun()

        with col2:
            if st.button("➡️ Next"):
                if idx < total - 1:
                    st.session_state.quiz_idx += 1
                    st.rerun()
                else:
                    st.session_state.quiz_end_time = datetime.now()
                    st.session_state.quiz_started = False
                    st.success("✅ Quiz completed!")

                    # Score calculation
                    score = 0
                    for i, idx in enumerate(st.session_state.quiz_order):
                        row = df.loc[idx]
                        correct_answers = [ans.strip().lower() for ans in row["Term"].split(",")]
                        guess = st.session_state.quiz_answers[i].strip().lower()
                        if guess in correct_answers:
                            score += 1
                            st.success(f"{i+1}. Correct — {correct_answers[0]}")
                        else:
                            st.error(f"{i+1}. Incorrect. ✅ Correct: {correct_answers[0]}, ❌ Your answer: {st.session_state.quiz_answers[i] or '—'}")

                    st.success(f"Total Score: {score} / {total}")
                    if score == total:
                        st.balloons()

        with col3:
            if st.button("⏹️ Force quit and generate report"):
                st.session_state.quiz_end_time = datetime.now()
                st.session_state.quiz_started = False

                # Score report data
                results = []
                score = 0
                for i, idx in enumerate(st.session_state.quiz_order):
                    row = df.loc[idx]
                    correct_answers = [ans.strip().lower() for ans in row["Term"].split(",")]
                    guess = st.session_state.quiz_answers[i].strip().lower()
                    is_correct = guess in correct_answers
                    if is_correct:
                        score += 1
                    results.append({
                        "No.": i + 1,
                        "Your Answer": st.session_state.quiz_answers[i] or "—",
                        "Correct Answer": correct_answers[0],
                        "Result": "✅ Correct" if is_correct else "❌ Incorrect"
                    })

                # Generate PDF
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from io import BytesIO

                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                elements = []

                start_str = st.session_state.quiz_start_time.strftime("%Y-%m-%d %H:%M:%S") if st.session_state.quiz_start_time else "N/A"
                end_str = st.session_state.quiz_end_time.strftime("%Y-%m-%d %H:%M:%S") if st.session_state.quiz_end_time else "N/A"

                elements.append(Paragraph(f"Audio Quiz Report for {st.session_state.quiz_user}", styles["Title"]))
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(f"Start Time: {start_str}", styles["Normal"]))
                elements.append(Paragraph(f"End Time: {end_str}", styles["Normal"]))
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(f"Total Score: {score} / {total}", styles["Heading2"]))
                elements.append(Spacer(1, 12))

                table_data = [["No.", "Your Answer", "Correct Answer", "Result"]]
                for item in results:
                    table_data.append([item["No."], item["Your Answer"], item["Correct Answer"], item["Result"]])

                table = Table(table_data, hAlign="LEFT", colWidths=[40, 150, 150, 100])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                elements.append(table)
                doc.build(elements)

                st.success(f"Total Score: {score} / {total}")
                st.download_button("📄 Download Quiz Report (PDF)", data=buffer.getvalue(), file_name="audio_quiz_report.pdf", mime="application/pdf")
