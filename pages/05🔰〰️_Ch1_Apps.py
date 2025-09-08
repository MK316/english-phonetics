import re
import unicodedata
import streamlit as st
import pandas as pd
from gtts import gTTS
from io import BytesIO
import base64
import random

# ---------------- Page setup ----------------
st.set_page_config(page_title="Basic applications", page_icon="🗣️", layout="wide")
st.title("🗣️ Understanding Speech Production")

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
    9:  ["tongue tip","tip of the tongue"],
    10: ["tongue blade", "blade of the tongue"],
    11: ["front of the tongue", "tongue front"],
    12: ["center of the tongue","tongue center"],
    13: ["back of the tongue", "tongue back"],
    14: ["tongue root", "root of the tongue"],
}

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
    if guess in gold or guess.endswith("s") and guess[:-1] in gold or (guess + "s") in gold:
        return True
    return False

# ---------------- Tabs ----------------
tab1, tab2, tab3 = st.tabs(["🌀 Vocal organs", "🌀 Term Practice (Text)", "🌀 Term Practice (Audio)"])

# ---------------- Load glossary data (Tab 2 & 3) ----------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/MK316/classmaterial/main/Phonetics/ch01_glossary.csv"  # ✅ Replace if needed
    df = pd.read_csv(url)
    df = df.dropna(subset=["Term", "Word count", "Description"])
    df["Word count"] = df["Word count"].astype(int)
    return df

df = load_data()

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
                st.session_state.answers[i] = st.text_input(f"{i}. ❄️ Number {i}", value=st.session_state.answers.get(i, ""), key=f"ans_{i}")
            j = i + 1
            if j <= TOTAL_ITEMS:
                with col_right:
                    st.session_state.answers[j] = st.text_input(f"{j}. ❄️ Number {j}", value=st.session_state.answers.get(j, ""), key=f"ans_{j}")
        submitted = st.form_submit_button("Check answers", use_container_width=True)

    if submitted:
        st.session_state.results = {n: is_correct(n, st.session_state.answers.get(n, "")) for n in range(1, TOTAL_ITEMS + 1)}
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
    num_items = st.number_input("How many terms would you like to practice?", min_value=1, max_value=len(df), value=3, key="text_input")
    
    if "text_items" not in st.session_state or st.button("🔄 New Practice (Text)", key="new_text"):
        st.session_state.text_items = df.sample(num_items).reset_index(drop=True)
        st.session_state.text_answers = [""] * num_items
        st.session_state.text_score = None

    for i, row in st.session_state.text_items.iterrows():
        st.markdown(f"**{i+1}. {row['Description']}**")
        st.write("Fill in: " + "____ " * row["Word count"])
        st.session_state.text_answers[i] = st.text_input(f"Your answer {i+1}", key=f"text_answer_{i}")

    if st.button("✅ Check Answers (Text)", key="check_text"):
        score = 0
        for i, row in st.session_state.text_items.iterrows():
            if st.session_state.text_answers[i].lower().strip() == row["Term"].lower().strip():
                score += 1
                st.success(f"{i+1}. Correct!")
            else:
                st.error(f"{i+1}. Incorrect. ✅ Correct: **{row['Term']}**")
        st.success(f"Your score: {score} / {num_items}")

# ---------------- Tab 3 — Audio Practice ----------------
with tab3:
    st.subheader("🔊 Practice Terms with Audio")
    num_items_audio = st.number_input("How many terms?", min_value=1, max_value=len(df), value=3, key="audio_input")

    if "audio_items" not in st.session_state or st.button("🔄 New Practice (Audio)", key="new_audio"):
        st.session_state.audio_items = df.sample(num_items_audio).reset_index(drop=True)
        st.session_state.audio_answers = [""] * num_items_audio
        st.session_state.audio_score = None

    def speak(text):
        tts = gTTS(text)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp

    def audio_player(audio_bytes):
        audio_data = audio_bytes.read()
        b64 = base64.b64encode(audio_data).decode()
        st.markdown(f"""
        <audio controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>""", unsafe_allow_html=True)

    for i, row in st.session_state.audio_items.iterrows():
        st.markdown(f"**{i+1}. Listen and Type the Term**")
        audio = speak(row["Term"])
        audio_player(audio)
        st.write("Fill in: " + "____ " * row["Word count"])
        st.session_state.audio_answers[i] = st.text_input(f"Your answer {i+1} (audio)", key=f"audio_answer_{i}")

    if st.button("✅ Check Answers (Audio)", key="check_audio"):
        score = 0
        for i, row in st.session_state.audio_items.iterrows():
            if st.session_state.audio_answers[i].lower().strip() == row["Term"].lower().strip():
                score += 1
                st.success(f"{i+1}. Correct!")
            else:
                st.error(f"{i+1}. Incorrect. ✅ Correct: **{row['Term']}**")
        st.success(f"Your score: {score} / {num_items_audio}")
