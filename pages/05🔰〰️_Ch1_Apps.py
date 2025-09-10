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
st.set_page_config(page_title="Basic applications", page_icon="🗣️", layout="wide")
st.markdown("#### 🗣️ Understanding Speech Production")

# ---------------- Image + Answer Key (Tab 1) ----------------
IMAGE_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/main/pages/images/vocal_organ.png"
TOTAL_ITEMS = 14

ANSWER_KEY = {
    1:  ["upper lip"],
    2:  ["upper teeth"],
    3:  ["alveolar ridge"],
    4:  ["hard palate"],
    5:  ["soft palate", "velum"],
    6:  ["uvula"],
    7:  ["epiglottis"],
    8:  ["lower lip"],
    9:  ["tongue tip", "tip of the tongue"],
    10: ["tongue blade", "blade of the tongue"],
    11: ["front of the tongue", "tongue front"],
    12: ["center of the tongue", "tongue center"],
    13: ["back of the tongue", "tongue back"],
    14: ["tongue root", "root of the tongue"],
}

# ---------------- Common helpers ----------------
def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"[\-_/]", " ", s)
    s = re.sub(r"[^a-z\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def is_correct(num: int, user_text: str) -> bool:
    if not user_text:
        return False
    gold = [normalize(x) for x in ANSWER_KEY.get(num, [])]
    guess = normalize(user_text)
    return guess in gold or (guess.endswith("s") and guess[:-1] in gold) or ((guess + "s") in gold)

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/MK316/classmaterial/main/Phonetics/ch01_glossary.csv"
    df = pd.read_csv(url)
    # keep required fields
    df = df.dropna(subset=["Term", "Description"])
    # coerce Word count
    if "Word count" in df.columns:
        df["Word count"] = pd.to_numeric(df["Word count"], errors="coerce").fillna(0).astype(int)
    else:
        df["Word count"] = 0
    # coerce Syllable (digits)
    if "Syllable" in df.columns:
        df["Syllable"] = pd.to_numeric(df["Syllable"], errors="coerce").astype("Int64")
    else:
        df["Syllable"] = pd.Series([pd.NA] * len(df), dtype="Int64")
    return df

df = load_data()

# cache TTS bytes for repeated plays of same definition
@st.cache_data(show_spinner=False)
def tts_bytes(text: str) -> bytes:
    fp = BytesIO()
    gTTS(text).write_to_fp(fp)
    fp.seek(0)
    return fp.read()

# --------------- Count + prompt helpers ---------------
def word_count_from_row(row) -> int:
    """
    Prefer dataset 'Word count'. Fallback: strip parentheticals/variants before counting.
    """
    try:
        wc = int(row["Word count"])
        return wc if wc > 0 else 1
    except Exception:
        pass
    term = str(row.get("Term", "")).strip()
    term = re.sub(r"\(.*?\)", "", term)
    term = re.split(r"\s*(?:/|,| or )\s*", term, maxsplit=1)[0]
    term = " ".join(term.split())
    wc = len(term.split())
    return wc if wc > 0 else 1

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

# --------------- Report generation (PDF with fallbacks) ---------------
def build_report_bytes(user_name: str, score: int, total: int, wrong_items: list):
    """
    wrong_items: list of dicts with keys: term, description, your_answer
    Returns (filename, mime, bytes)
    """
    title = "Chapter 1: Phonetics Term Practice"
    now_kr = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
    base_name = f"{title.replace(' ', '_')}_{user_name.replace(' ', '_')}_{now_kr.replace(':','-')}"

    # Try reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        x_margin, y_margin = 2*cm, 2*cm
        y = height - y_margin

        def write_line(text, font="Helvetica", size=11, dy=14):
            nonlocal y
            c.setFont(font, size)
            c.drawString(x_margin, y, text)
            y -= dy

        def write_wrapped(label, text, width_chars=90, dy=14):
            nonlocal y
            wrap = textwrap.wrap(text, width=width_chars)
            if label:
                write_line(label, font="Helvetica-Bold", size=11)
            for ln in wrap:
                write_line(ln, font="Helvetica", size=11, dy=dy)

        # Header
        write_line(title, font="Helvetica-Bold", size=16, dy=22)
        write_line(f"Name: {user_name}", size=11)
        write_line(f"Date (KST): {now_kr}", size=11)
        write_line(f"Score: {score} / {total}", size=11)
        y -= 8

        # Incorrect
        write_line("Incorrect Answers", font="Helvetica-Bold", size=13, dy=18)
        if not wrong_items:
            write_line("None — All correct! 🎉", size=11)
        else:
            for i, item in enumerate(wrong_items, 1):
                if y < 6*cm:
                    c.showPage()
                    y = height - y_margin
                write_line(f"{i}. {item['term']}", font="Helvetica-Bold", size=12)
                write_wrapped("Description:", item["description"], width_chars=95)
                if item.get("your_answer"):
                    write_wrapped("Your answer:", item["your_answer"], width_chars=95)
                y -= 6

        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return f"{base_name}.pdf", "application/pdf", pdf_bytes

    except Exception:
        # Try fpdf2
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, title, ln=True)
            pdf.set_font("Helvetica", size=12)
            pdf.cell(0, 8, f"Name: {user_name}", ln=True)
            pdf.cell(0, 8, f"Date (KST): {now_kr}", ln=True)
            pdf.cell(0, 8, f"Score: {score} / {total}", ln=True)
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "Incorrect Answers", ln=True)
            pdf.set_font("Helvetica", size=12)
            if not wrong_items:
                pdf.cell(0, 8, "None — All correct! 🎉", ln=True)
            else:
                for i, item in enumerate(wrong_items, 1):
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.multi_cell(0, 8, f"{i}. {item['term']}")
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.multi_cell(0, 8, "Description:")
                    pdf.set_font("Helvetica", size=12)
                    pdf.multi_cell(0, 8, item["description"])
                    if item.get("your_answer"):
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.multi_cell(0, 8, "Your answer:")
                        pdf.set_font("Helvetica", size=12)
                        pdf.multi_cell(0, 8, item["your_answer"])
                    pdf.ln(2)
            out = pdf.output(dest="S").encode("latin1")
            return f"{base_name}.pdf", "application/pdf", out
        except Exception:
            # Fallback TXT
            lines = [
                title,
                f"Name: {user_name}",
                f"Date (KST): {now_kr}",
                f"Score: {score} / {total}",
                "",
                "Incorrect Answers:",
            ]
            if not wrong_items:
                lines.append("None — All correct! 🎉")
            else:
                for i, item in enumerate(wrong_items, 1):
                    lines.append(f"{i}. {item['term']}")
                    lines.append(f"Description: {item['description']}")
                    if item.get("your_answer"):
                        lines.append(f"Your answer: {item['your_answer']}")
                    lines.append("")
            txt = "\n".join(lines).encode("utf-8")
            return f"{base_name}.txt", "text/plain", txt

# --------------- Hint builder for Tab 2 ---------------
def hint_from_term(term: str, underscores: int = 4) -> str:
    """
    'Respiratory system' -> 'r____ s____'
    """
    words = re.split(r"\s+", str(term).strip())
    hinted = []
    for w in words:
        if not w:
            continue
        hinted.append(w[0].lower() + "_" * underscores)
    return " ".join(hinted)

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["🌀 Vocal organs", "🌀 Term Practice (Text)", "🌀 Term Practice (Audio)", "🍔 Audio Quiz"]
)

# ---------------- Tab 1 ----------------
with tab1:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(IMAGE_URL, use_container_width=True,
                 caption="Refer to the numbers (1–14) on this diagram.")

    if "answers" not in st.session_state:
        st.session_state.answers = {i: "" for i in range(1, TOTAL_ITEMS + 1)}
    if "checked" not in st.session_state:
        st.session_state.checked = False
    if "results" not in st.session_state:
        st.session_state.results = {}

    top = st.columns([1, 6, 1])
    with top[0]:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.answers = {i: "" for i in range(1, TOTAL_ITEMS + 1)}
            st.session_state.checked = False
            st.session_state.results = {}
            st.rerun()

    st.divider()
    st.subheader("📌 Type all answers, then click the button below to check the answers.")
    with st.form("quiz_form"):
        col_left, col_right = st.columns(2)
        for i in range(1, TOTAL_ITEMS + 1, 2):
            with col_left:
                st.session_state.answers[i] = st.text_input(
                    f"{i}. ❄️ Number {i}",
                    value=st.session_state.answers.get(i, ""),
                    key=f"ans_{i}"
                )
            j = i + 1
            if j <= TOTAL_ITEMS:
                with col_right:
                    st.session_state.answers[j] = st.text_input(
                        f"{j}. ❄️ Number {j}",
                        value=st.session_state.answers.get(j, ""),
                        key=f"ans_{j}"
                    )
        submitted = st.form_submit_button("Check answers", use_container_width=True)

    if submitted:
        st.session_state.results = {
            n: is_correct(n, st.session_state.answers.get(n, "")) for n in range(1, TOTAL_ITEMS + 1)
        }
        st.session_state.checked = True
        st.rerun()

    if st.session_state.checked:
        correct_count = sum(1 for ok in st.session_state.results.values() if ok)
        st.success(f"Score: **{correct_count} / {TOTAL_ITEMS}**")
        rows = []
        for n in range(1, TOTAL_ITEMS + 1):
            user = st.session_state.answers.get(n, "")
            ok = st.session_state.results.get(n, False)
            gold_display = ", ".join(ANSWER_KEY.get(n, [])) or "(set me in ANSWER_KEY)"
            rows.append({
                "No.": n,
                "Your answer": user if user else "—",
                "Accepted answers": gold_display,
                "Result": "✅ Correct" if ok else "❌ Incorrect",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if st.button("🧪 Try again", use_container_width=True):
            st.session_state.checked = False
            st.session_state.results = {}
            st.rerun()

# ---------------- Tab 2 — Text Practice ----------------
with tab2:
    st.subheader("✍️ Practice Terms with Text Descriptions")
    HINT_UNDERSCORES = 4

    num_items = st.number_input(
        "How many terms would you like to practice?",
        min_value=1,
        max_value=len(df),
        value=3,
        key="text_input"
    )

    if "text_items" not in st.session_state or st.button("🔄 New Practice (Text)", key="new_text"):
        st.session_state.text_items = df.sample(num_items).reset_index(drop=True)
        st.session_state.text_answers = [""] * num_items

    for i, row in st.session_state.text_items.iterrows():
        desc = str(row["Description"]).strip()
        term = str(row["Term"]).strip()
        st.markdown(f"**{i+1}. {desc}**")
        hint = hint_from_term(term, underscores=HINT_UNDERSCORES)
        st.markdown(
            f"<div style='opacity:0.8; margin-top:-0.25rem;'>Hint: <code>{hint}</code></div>",
            unsafe_allow_html=True
        )
        st.write(answer_prompt(row))
        st.session_state.text_answers[i] = st.text_input(
            f"Your answer {i+1}",
            value=st.session_state.text_answers[i],
            key=f"text_answer_{i}"
        )

    if st.button("✅ Check Answers (Text)", key="check_text"):
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

# ---------------- Tab 3 — Audio Practice (list mode) ----------------
with tab3:
    st.subheader("🔊 Practice Terms with Audio (Hear the definition, type the term)")

    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #2e7d32;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.6em 1.2em;
            font-weight: 600;
            cursor: pointer;
        }
        div.stButton > button:hover {
            background-color: #1b5e20;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    num_items_audio = st.number_input(
        "How many terms?",
        min_value=1,
        max_value=len(df),
        value=3,
        key="audio_num",
        help="Choose how many definitions you want to practice, then click New Practice."
    )

    if "audio_idx" not in st.session_state:
        st.session_state.audio_idx = []
    if "audio_answers" not in st.session_state:
        st.session_state.audio_answers = []

    if st.button("🔄 Generate Practice Questions (Audio)", key="new_audio"):
        sample = df.sample(int(num_items_audio), random_state=None)
        st.session_state.audio_idx = sample.index.tolist()
        st.session_state.audio_answers = [""] * len(st.session_state.audio_idx)
        st.rerun()

    if not st.session_state.audio_idx:
        st.info("Set the number above and click **Generate Practice Questions (Audio)** to start.")
    else:
        for i, idx in enumerate(st.session_state.audio_idx):
            row = df.loc[idx]
            term = str(row["Term"]).strip()
            desc = str(row["Description"]).strip()

            st.markdown(f"**{i+1}. Listen to the definition and type the correct term**")
            st.audio(tts_bytes(desc), format="audio/mp3")
            st.write(answer_prompt(row))
            st.session_state.audio_answers[i] = st.text_input(
                f"Your answer {i+1}",
                value=st.session_state.audio_answers[i],
                key=f"audio_answer_{idx}",
            )

        if st.button("✅ Check Answers (Audio)", key="check_audio"):
            score = 0
            for i, idx in enumerate(st.session_state.audio_idx):
                row = df.loc[idx]
                gold = " ".join(str(row["Term"]).strip().lower().split())
                guess = " ".join(str(st.session_state.audio_answers[i]).strip().lower().split())
                if guess == gold:
                    score += 1
                    st.success(f"{i+1}. Correct!")
                else:
                    st.error(f"{i+1}. Incorrect. ✅ Correct: **{row['Term']}**")
            st.success(f"Your score: {score} / {len(st.session_state.audio_idx)}")
            if score == len(st.session_state.audio_idx):
                st.balloons()

# ---------------- Tab 4 — Audio Quiz (one-by-one + PDF report) ----------------
with tab4:
    st.subheader("🧪 Audio Quiz — with a PDF report)")

    # --- Username and Start ---
    name_col, btn_col = st.columns([2, 1])
    with name_col:
        typed_name = st.text_input("Enter your name", key="tab4_user_name_input")
    with btn_col:
        start_clicked = st.button("Start quiz ▶️", use_container_width=True, key="tab4_start")

    # --- initialize state ---
    if "tab4_user_name" not in st.session_state:
        st.session_state.tab4_user_name = ""
    if "tab4_started" not in st.session_state:
        st.session_state.tab4_started = False
    if "tab4_done" not in st.session_state:
        st.session_state.tab4_done = False
    if "tab4_order" not in st.session_state:
        st.session_state.tab4_order = []
    if "tab4_idx" not in st.session_state:
        st.session_state.tab4_idx = 0
    if "tab4_answers" not in st.session_state:
        st.session_state.tab4_answers = []

    # Start logic
    if start_clicked:
        if not typed_name.strip():
            st.warning("Please enter your name to begin. Once you start, you can't change the user name.")
        else:
            st.session_state.tab4_user_name = typed_name.strip()
            order = df.sample(frac=1, random_state=None).index.tolist()  # shuffle all terms
            st.session_state.tab4_order = order
            st.session_state.tab4_idx = 0
            st.session_state.tab4_answers = [""] * len(order)
            st.session_state.tab4_started = True
            st.session_state.tab4_done = False
            st.rerun()

    # Quiz running
    if st.session_state.tab4_started and not st.session_state.tab4_done:
        idx = st.session_state.tab4_idx
        total = len(st.session_state.tab4_order)

        row = df.loc[st.session_state.tab4_order[idx]]
        term = str(row["Term"]).strip()
        desc = str(row["Description"]).strip()

        st.info(f"Question {idx+1} of {total}")
        st.audio(tts_bytes(desc), format="audio/mp3")
        st.write(answer_prompt(row))

        ans_key = f"tab4_answer_{idx}"
        current_value = st.session_state.tab4_answers[idx]
        new_value = st.text_input("Your answer", value=current_value, key=ans_key)
        st.session_state.tab4_answers[idx] = new_value

        colA, colB = st.columns([1, 1])
        with colA:
            if st.button("⏮️ Restart quiz", use_container_width=True, key="tab4_restart"):
                st.session_state.tab4_started = False
                st.session_state.tab4_done = False
                st.session_state.tab4_order = []
                st.session_state.tab4_idx = 0
                st.session_state.tab4_answers = []
                st.rerun()
        with colB:
            if st.button("Submit & Next ➡️", use_container_width=True, key="tab4_next"):
                if st.session_state.tab4_idx < total - 1:
                    st.session_state.tab4_idx += 1
                    st.rerun()
                else:
                    st.session_state.tab4_done = True
                    st.rerun()

    # Quiz completed -> summary + PDF download
    if st.session_state.tab4_done:
        total = len(st.session_state.tab4_order)
        results = []
        score = 0
        wrong_items = []
        for i, ridx in enumerate(st.session_state.tab4_order):
            row = df.loc[ridx]
            gold = " ".join(str(row["Term"]).strip().lower().split())
            guess = " ".join(str(st.session_state.tab4_answers[i]).strip().lower().split())
            ok = (guess == gold)
            results.append(ok)
            if ok:
                score += 1
            else:
                wrong_items.append({
                    "term": str(row["Term"]).strip(),
                    "description": str(row["Description"]).strip(),
                    "your_answer": st.session_state.tab4_answers[i],
                })

        st.success(f"✅ Finished! Score: **{score} / {total}**")

        user_for_report = st.session_state.tab4_user_name or "Anonymous"
        filename, mime, data = build_report_bytes(user_for_report, score, total, wrong_items)
        st.download_button(
            "📄 Download PDF Report",
            data=data,
            file_name=filename,
            mime=mime,
            use_container_width=True,
        )

        st.write("**Incorrect items:**")
        if not wrong_items:
            st.write("🎉 None — great job!")
        else:
            for item in wrong_items:
                st.markdown(
                    f"- **{item['term']}** — {item['description']}  \n"
                    f"  _Your answer:_ {item['your_answer'] or '—'}"
                )

        if st.button("🔁 Take again", use_container_width=True, key="tab4_take_again"):
            st.session_state.tab4_started = False
            st.session_state.tab4_done = False
            st.session_state.tab4_order = []
            st.session_state.tab4_idx = 0
            st.session_state.tab4_answers = []
            st.rerun()
